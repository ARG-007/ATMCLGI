from random import randint
from mysql.connector import connect , Error as SQLError, errorcode as SQLErrorCode
from redis import Redis

#Unsafe But Who Cares?
sqlConnection = {
    "user": "pyatm",
    "password": "pyatm",
    "host": "localhost",
    "port": 3306,
    "database" : "PythonATM"
}

redisConnection = {
    "host": "localhost",
    "port": 6379,
    "decode_responses":True
}

class ATM:
    def __init__(self) -> None:
        self.__mysqlDB = connect(**sqlConnection)
        self.__redisDB = Redis(**redisConnection)
        self._isAuthenticated  :bool = False
        self.currentUser       :dict = {}
        self.lastTransaction   :dict = {}

    @property
    def isAuthenticated(self):
        return self._isAuthenticated

    @property
    def otp(self):
        otp = randint(100000,999999)
        self.__redisDB.set(name=self.currentUser["ID"], value=otp, ex=600)
        return otp

    def login(self, user :str, password :int) -> int:
        """
        Checks Whether Credentials Provided By User is Valid
        
        Raises ValueError on Two Conditions:
            1. When the password is not exactly 6 digits 
            2. When the user and password combiantion is not found in the database
        
        Returns 6 Digit OTP which is stored to redis database for further validation
        """
        if not (100000<=password<=999999): 
            raise ValueError("Password Must Be 6 Digits") 

        with self.__mysqlDB.cursor(prepared=True, dictionary=True) as cursor:
            cursor.execute("SELECT ID, Holder, Balance FROM `Accounts` WHERE `Holder` = %s AND `PIN` = %s",(user,password))
            result = cursor.fetchone()
        if not result:
            raise ValueError("Username or Password is Incorrect")
        
        self.currentUser.update(result)

        # store OTP in redis for sole purpose of being overkill,
        # it even expires after 600 secs (10 mins), so hey not all are bad :)
        self.lastTransaction = {}

        return self.otp

    def authenticateLogin(self,otp :int) -> bool:
        """
        Authenticates the OTP which is provided by the callee Against the OTP stored in Redis

        The Result is stored to __isAuthenticated which is used by withdraw, deposit methods

        The Result is returned 
        """
        if(not (self.currentUser)): raise ValueError("No User Logged In")

        self._isAuthenticated = int(str(self.__redisDB.get(self.currentUser["ID"]))) == otp
        return self._isAuthenticated
    
    def withdraw(self, amount :float) -> dict:
        """
        Withdraws Money from user's Account

        Raises AssertionError, ValueError, ConnectionError

        Returns the Resulting Transaction
        """
        if not self._isAuthenticated :
            raise AssertionError("User Is Not Authenticated To Withdraw")

        if self.currentUser["Balance"] < amount :
            raise ValueError("User Does Not Have Sufficient Balance To Withdraw")

        Transaction = {}
        try :
            with self.__mysqlDB.cursor(dictionary=True) as cursor:
                cursor.callproc('Withdraw',(self.currentUser["ID"],amount))
                Transaction = next(cursor.stored_results()).fetchone()
        except SQLError as err:
            self.__mysqlDB.rollback()
            raise ConnectionError("Something Wrong With The Database, Guess Whatever You Are Doing Should Wait")
        else:
            self.__mysqlDB.commit()
            self.currentUser["Balance"] = Transaction["Balance"]
            self.lastTransaction = Transaction

        return Transaction
    
    def deposit(self, amount :float) -> dict:
        """
        Deposits Money to User's Account

        Raises AssertionError, ConnectionError

        Returns the Resulting Transaction
        """

        if not self._isAuthenticated :
            raise AssertionError("User Is Not Authenticated To Withdraw")
        
        Transaction = {}
        try :
            with self.__mysqlDB.cursor( dictionary=True) as cursor: 
                cursor.callproc('Deposit',(self.currentUser["ID"],amount))
                Transaction = next(cursor.stored_results()).fetchone()
        except SQLError as err:
            self.__mysqlDB.rollback()
            raise ConnectionError("Something Wrong With The Database, Guess Whatever You Are Doing Should Wait")
        else:
            self.__mysqlDB.commit()
            self.currentUser["Balance"] = Transaction["Balance"]
            self.lastTransaction = Transaction
        
        return Transaction

    def registerUser(self, user, password, intialAmount) -> dict:
        """
        Registers New User into the Database

        Raises ValueError when :
            -> Password is Not 6 digits long
            -> User already exists!
        
        Returns Resulting Transaction and The OTP
        """

        if not (100000<=password<=999999): 
            raise ValueError("Password Must Be 6 Digits")
        
        Transaction = {}
        try:
            with self.__mysqlDB.cursor(dictionary=True) as cursor:
                cursor.callproc("AddUser",(user,password,intialAmount))
                Transaction = next(cursor.stored_results()).fetchone()
                cursor.execute("SELECT ID, Holder, Balance FROM `Accounts` WHERE `Holder` = %s AND `PIN` = %s",(user,password))
                self.currentUser = cursor.fetchone() 
        except SQLError as err : 
            self.__mysqlDB.rollback()
            if err.errno == SQLErrorCode.ER_DUP_ENTRY:
                raise ValueError("User Already Exists")
            else:
                raise ConnectionError("Something Wrong With The Database, Guess Whatever You Are Doing Should Wait")
        else:
            self.__mysqlDB.commit()
            self.lastTransaction = Transaction
        
        return Transaction
    
    def getTransactionList(self) -> list[dict]:
        """
        Returns All Transactions of the user as list of dicts
        """

        with self.__mysqlDB.cursor(prepared=True, dictionary=True) as cursor:
            cursor.execute("SELECT * FROM `Transactions` WHERE AccountID = %s",[self.currentUser['ID']])
            transactions = cursor.fetchall()
        return transactions
