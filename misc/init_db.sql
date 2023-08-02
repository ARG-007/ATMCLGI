USE `PythonATM`;

DROP TABLE IF EXISTS `Transactions`;
DROP TABLE IF EXISTS `Accounts`;
DROP FUNCTION IF EXISTS `rando`;
DROP PROCEDURE IF EXISTS `PopulateTransaction`;
DROP PROCEDURE IF EXISTS `Deposit`;
DROP PROCEDURE IF EXISTS `Withdraw`;
DROP PROCEDURE IF EXISTS `AddUser`;

CREATE TABLE `Accounts` (
	ID INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    Holder VARCHAR(30) NOT NULL UNIQUE,
    PIN INT NOT NULL,
    Balance DOUBLE NOT NULL,
    CONSTRAINT `ValidatePIN` CHECK(PIN >= 100000 AND PIN <= 999999)
    #CONSTRAINT `CheckBalance` CHECK(Balance >= 0 )
);

CREATE TABLE `Transactions` (
	TID INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    AccountID INT UNSIGNED NOT NULL,
    TransactTime DATETIME DEFAULT CURRENT_TIMESTAMP,
    TransactType CHAR(8) NOT NULL,
    Amount DOUBLE NOT NULL,
    Balance DOUBLE NOT NULL,
    CONSTRAINT `TranAccountID` FOREIGN KEY (`AccountID`) REFERENCES `Accounts`(`ID`) ON DELETE CASCADE ON UPDATE CASCADE
);



/**
* The Following Triggers are important as they
* automatically update Transaction table whenever a
* user registers, deposits, withdraws money from their
* account.
*/
DELIMITER $$
CREATE TRIGGER `AFTER_Accounts_INSERT`
AFTER INSERT ON `Accounts` FOR EACH ROW
BEGIN
	INSERT INTO `Transactions` (AccountID, TransactType, Amount, Balance) VALUES (NEW.ID, "ACC_CRE", NEW.Balance, NEW.Balance);
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER `AFTER_Accounts_UPDATE`
AFTER UPDATE ON `Accounts` FOR EACH ROW
BEGIN
	DECLARE dAmount DOUBLE;
	DECLARE tType CHAR(8) ;
	SET dAmount = NEW.Balance - OLD.Balance;
	IF (dAmount <> 0) THEN
		IF (dAmount < 0) THEN 
			SET tType = "WITHDRAW";
		ELSE
			SET tType = "DEPOSIT";
		END IF;
		SET dAmount = ABS(dAmount);
    
		INSERT INTO `Transactions`(AccountID, TransactType, Amount, Balance) VALUES (OLD.ID, tType, dAmount, NEW.Balance);
	END IF;
END$$
DELIMITER ;

/**
* Convenience Methods(Yes these are known as procedures) for
* the python program as these result in somewhat clean code in it
* These methods(procedures) will return the resulting transaction
* from these operations and hence heavly rely on above mentioned triggers
* I could rewrite these to not rely on triggers but i am burntout
*/
DELIMITER $$
CREATE PROCEDURE `Deposit`( IN AccountID INT, IN DepositAmount DOUBLE) BEGIN
	UPDATE `Accounts` SET Balance = Balance + DepositAmount WHERE ID = AccountID;
	SELECT * FROM `Transactions` WHERE `AccountID` = AccountID ORDER BY TID DESC LIMIT 1;
END $$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE `Withdraw` ( IN AccountID INT, IN WithdrawAmount DOUBLE) BEGIN
	 UPDATE `Accounts` SET Balance = Balance - WithdrawAmount WHERE ID = AccountID;
     SELECT * FROM `Transactions` WHERE `AccountID` = AccountID ORDER BY TID DESC LIMIT 1;
END $$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE `AddUser` ( IN Holder VARCHAR(30), IN Pass INT, IN initialAmount DOUBLE) BEGIN
	INSERT INTO `Accounts` (Holder, PIN, Balance) VALUES (Holder, Pass, initialAmount);
    SELECT * FROM `Transactions` WHERE `AccountID` = LAST_INSERT_ID();
END $$
DELIMITER ;

/**
* The Procedure `PopulateTransaction` and Function `rando` are used to do random transactions
* fill up transaction table
*/

# Equivalent to random.randint(x,y) from python
CREATE FUNCTION `rando` (minLimit INT, maxLimit INT)
RETURNS INT NO SQL DETERMINISTIC 
RETURN FLOOR(minLimit + RAND()*(maxLimit-minLimit+1));

# Randomly does transactions
DELIMITER $$
CREATE PROCEDURE `PopulateTransaction` (IN rep INT) BEGIN
	DECLARE entries INT;
    SELECT COUNT(ID) INTO entries FROM `Accounts`;
    
    WHILE rep>0 DO
		IF rando(1,2) = 1 THEN
            UPDATE `Accounts` SET Balance = Balance + (500*rando(1,4)) WHERE ID = rep%entries+1;
		ELSE
			UPDATE `Accounts` SET Balance = Balance - (500*rando(1,4)) WHERE ID = rep%entries+1;
        END IF;
		SET rep=rep-1;
	END WHILE;


	SELECT AccountID, COUNT(TID) FROM `Transactions` GROUP BY AccountID;
    SELECT TransactType, COUNT(TransactType) FROM `Transactions` GROUP BY TransactType;
    
END $$
DELIMITER ;


/**
* Populating both tables with data
*/
INSERT INTO `Accounts` (Holder, PIN, Balance) VALUES
("ARG",694201,6254),
("BSS",567831,7234),
("CHJ",123413,8565),
("DKS",451221,8651),
("DAK",135122,7413),
("GHR",134134,7134);

CALL PopulateTransaction(60);

