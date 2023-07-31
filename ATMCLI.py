from art import text2art
from rich import print, inspect
from rich.console import group, Group
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from time import sleep
from rich import box
from rich.text import Text
from rich.align import Align
from rich.style import Style
from rich.table import Table
from rich.color import ANSI_COLOR_NAMES
from datetime import datetime
from random import choice
from pynput.keyboard import Listener as KeyboardListener, Key
from re import sub
import math
from ATM import ATM
from typing import List, Dict


Available_Colors = list(ANSI_COLOR_NAMES.keys())

def createPanel(
    value,
    box: box = box.SQUARE,
    box_style: Style | str = "red",
    font_style: Style | str = "yellow",
    alignment: tuple[str] = ("center", "middle")
):
    return Panel(
        Align(value, align=alignment[0], vertical=alignment[1], style=font_style),
        box=box,
        style=box_style,
    )

class Updatable:
    def __init__(self,callback,*args):
        self.callback = callback
        self.args = args
    def __rich__(self):
        return self.callback(*self.args)

class Form:
    def __init__(self, name, callback, fields: List[str]):
        self.name = name
        self.callback = callback

        self.fields: List[str] = fields
        self.fieldsMap: Dict[str, str] = {i: "" for i in fields}
        self._focused = 0

        self.form = Table(show_header=False,box=box.HEAVY_EDGE, expand=True, show_lines= True, caption_style="red")
        self.form.add_column(max_width=10)
        self.form.add_column(max_width=30)

        for i in self.fields :
            self.form.add_row(i,Updatable(self.getFieldValue,i))
        
        self.focused=0
        

    @property
    def focused(self):
        return self._focused

    @focused.setter
    def focused(self,newValue):
        self.form.rows[self._focused].style = ""
        self._focused = newValue
        self.form.rows[self._focused].style = "violet"

    def setStatus(self,message):
        self.form.caption = message

    def getFieldValue(self,field):
        return self.fieldsMap[field]
    
    @property
    def getFocused(self):
        return self.fields[self.focused]

    def keyHandler(self,key : Key):
        try: 
            k=key.char
            self.fieldsMap[self.getFocused]+=k
        except:
            match(key):
                case Key.up   : self.focused=(self.focused-1)%(len(self.fields))
                case Key.down : self.focused=(self.focused+1)%(len(self.fields))
                case Key.enter: self.callback(name = self.name, event = "Submit", values = self.fieldsMap)
                case Key.backspace : self.fieldsMap[self.getFocused] = self.fieldsMap[self.getFocused][:-1]
                case Key.esc : self.callback(event="Escape")
    
    def __rich__(self):
        return self.form
        

class ATMCLI(ATM):

    def __init__(self):
        super().__init__()
        self.generateTemplate()

        self.ticks = -1
        self.liveRate = 4
        self.bankName = "ARG-BANK"

        self.bankArt = {
            "art":"",
            "color":""
        }

        self.keyboardListener = KeyboardListener(on_press=self.HandleInteraction)
        self.option = {
            "options": ["Login", "Withdraw", "Deposit", "Account"],
            "selected": 0,
            "render": ""
        }

        self.clockPanel: Panel = createPanel(Updatable(lambda: datetime.now().ctime()), box.HORIZONTALS, "yellow", "red")
        self.bankArtPanel: Panel = createPanel(Updatable(self.artify), box.HEAVY_EDGE, "yellow")
        self.selectionPanel: Panel = createPanel(Updatable(lambda: self.option["render"]), box.ASCII2, "green", "grey62")

        self.loginForm = Form("Login",self.formHandler, ["User", "PIN"])
        self.withdrawForm = Form("Withdraw",self.formHandler, ["Amount", "PIN"])
        self.depositForm = Form("Deposit",self.formHandler,["Amount","PIN"])
        self.pinForm = Form("OTP",self.formHandler,["OTP"])

        self.loginPanel = createPanel(self.loginForm)
        self.withdrawPanel = createPanel(self.withdrawForm)
        self.depositPanel = createPanel(self.depositForm)
        self.transactionPanel = createPanel("Press Enter To View Transactions")
        self.goAwayPanel=createPanel("You Must Login To View This")


        self.forms :List[Form] = [
            self.loginForm,
            self.withdrawForm,
            self.depositForm
        ]

        self.outputMap: List[Panel] = [
            self.loginPanel,
            self.withdrawPanel,
            self.depositPanel,
            self.transactionPanel,
        ]

        self.mainLayout["Moto"].update(createPanel("Your Eternal Dept Is One Transaction Away!"))
        self.mainLayout["TimeStamp"].update(self.clockPanel)
        self.mainLayout["BankDisplay"].update(self.bankArtPanel)
        self.mainLayout["Selection"].update(self.selectionPanel)
        self.mainLayout["Output"].update(Updatable(self.getFocusedPanel))

        self.keyboardListener.start()

    def getFocusedPanel(self):
        if self.isAuthenticated or (self.option["selected"] == 0):
            return self.outputMap[self.option["selected"]]
        else :
            return self.goAwayPanel
    
    def updateRender(self):
        selected = self.option["selected"]
        selected = self.option["options"][selected]
        render = ""
        for i in self.option["options"]:
            if i == selected:
                render += f"[bright_green]> {i}[/]"
            else:
                render += f"  {i}"
            render += "\n"
        self.option["render"] = render.strip("\n")

    def HandleInteraction(self, key: Key):
        match(key):
            case Key.up:
                self.option["selected"] = (self.option["selected"]-1) % 4
                self.updateRender()

            case Key.down:
                self.option["selected"] = (self.option["selected"]+1) % 4
                self.updateRender()

            case Key.enter :
                self.keyboardListener.on_press=self.forms[self.option["selected"]].keyHandler

    def formHandler(self,event : str,name=None,values:dict = None):
        if (event == "Escape"):
            self.keyboardListener.on_press = self.HandleInteraction
            return
        
        try:
            if(event == "Submit"):
                match(name):
                    case "Login":
                        result = self.login(values["User"],int(values["PIN"]))
                        
                    # I'm not gonna implement password checking for Withdraw, Deposit
                    # Gotta stick with the moto
                    case "Withdraw":
                        result = self.withdraw(int(values["Amount"]))
                    case "Deposit":
                        result = self.deposit(int(values["Amount"]))

        except Exception as e:
            if(name == "Login"): self.loginForm.setStatus(str(e))
            if(name == "Withdraw"): self.withdrawForm.setStatus(str(e))
            if(name == "Deposit"): self.depositForm.setStatus(str(e))
        else:
            pass
    def artify(self):
        #Change Art for every sec (this will screw up if live is refreshed with .refresh())
        if self.ticks % self.liveRate == 0:
            self.bankArt["art"] = text2art(self.bankName, font="rand-large").strip("\n")
        #Change color atmost 8 times per sec 
        if self.ticks % (math.ceil(self.liveRate / 8)) == 0:
            self.bankArt["color"]=f"[{choice(Available_Colors)}]"

        return self.bankArt["color"]+self.bankArt["art"]

    def insertLive(self, live: Live):
        self.live = live
        self.liveRate = live.refresh_per_second
        self.updateRender()

    def generateTemplate(self):
        self.mainLayout = Layout(name="main")

        self.mainLayout.split_column(
            Layout(name="BankDisplay"),
            Layout(name="body", ratio=2),
            Layout(name="footer", size=5)
        )
        self.mainLayout["body"].split_row(
            Layout(name="Interactable", ratio=2),
            Layout(name="Output", ratio=4)
        )
        self.mainLayout["Interactable"].split_column(
            Layout(name="Selection"),
            Layout(name="JARDIS")
        )
        self.mainLayout["footer"].split_row(
            Layout(name="TimeStamp",ratio=2),
            Layout(name="Moto",ratio=4),
        )

    def __rich__(self):
        self.ticks += 1

        return self.mainLayout
    
    def __del__(self):
        del self.mainLayout


cli = ATMCLI()
with Live(cli,screen=True, refresh_per_second=30) as live:
    cli.insertLive(live)
    while True:
        sleep(10)
