import math
from datetime import datetime
from random import choice
from time import sleep
from typing import List

from art import text2art
from pynput.keyboard import Key
from pynput.keyboard import Listener as KeyboardListener
from rich import box
from rich.color import ANSI_COLOR_NAMES
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from lib.atm import ATM
from lib.form import Form
from lib.utility import Updatable, createPanel

Available_Colors = list(ANSI_COLOR_NAMES.keys())


class ATMCLI(ATM):
    def __init__(self):
        super().__init__()
        self.generateTemplate()

        self.ticks = -1
        self.liveRate = 4
        self.bankName = "ARG-BANK"

        self.bankArt = {"art": "", "color": ""}

        self.keyboardListener = KeyboardListener(on_press=self.HandleInteraction)

        self.option = {
            "options": ["Login", "Withdraw", "Deposit", "Account"],
            "selected": 0,
            "render": "",
        }

        self.history = []

        self.clockPanel: Panel = createPanel(
            Updatable(lambda: datetime.now().ctime()), box.HORIZONTALS, "yellow", "red"
        )
        self.bankArtPanel: Panel = createPanel(
            Updatable(self.artify), box.HEAVY_EDGE, "yellow"
        )
        self.selectionPanel: Panel = createPanel(
            Updatable(lambda: self.option["render"]), box.ASCII2, "green", "grey62"
        )

        self.loginForm = Form("Login", self.formHandler, ["User", "PIN"])
        self.withdrawForm = Form("Withdraw", self.formHandler, ["Amount", "PIN"])
        self.depositForm = Form("Deposit", self.formHandler, ["Amount", "PIN"])
        self.pinForm = Form("OTP", self.formHandler, ["OTP"])

        self.loginPanel = createPanel(self.loginForm)
        self.withdrawPanel = createPanel(self.withdrawForm)
        self.depositPanel = createPanel(self.depositForm)
        self.transactionPanel = createPanel(Updatable(self.getTransactionList))
        self.goAwayPanel = createPanel("You Must Login To View This")

        self.forms: List[Form] = [self.loginForm, self.withdrawForm, self.depositForm]

        self.outputMap: List[Panel] = [
            self.loginPanel,
            self.withdrawPanel,
            self.depositPanel,
            self.transactionPanel,
        ]

        self.mainLayout["Moto"].update(
            createPanel("Your Eternal Dept Is One Transaction Away!")
        )
        self.mainLayout["TimeStamp"].update(self.clockPanel)
        self.mainLayout["BankDisplay"].update(self.bankArtPanel)
        self.mainLayout["Selection"].update(self.selectionPanel)
        self.mainLayout["Output"].update(Updatable(self.getFocusedPanel))
        self.mainLayout["JARDIS"].update(
            createPanel(
                Updatable(lambda: "\n".join(self.history)),
                alignment=("center", "bottom"),
                box=box.DOUBLE_EDGE,
                box_style="cyan",
            )
        )

        self.keyboardListener.start()

    def getFocusedPanel(self):
        if self.isAuthenticated or (self.option["selected"] == 0):
            return self.outputMap[self.option["selected"]]
        else:
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
        match (key):
            case Key.up:
                self.option["selected"] = (self.option["selected"] - 1) % 4
                self.updateRender()

            case Key.down:
                self.option["selected"] = (self.option["selected"] + 1) % 4
                self.updateRender()

            case Key.enter:
                if self.option["selected"] == 3:
                    return
                self.keyboardListener.on_press = self.forms[
                    self.option["selected"]
                ].keyHandler

    def getTransactionList(self) -> list[dict]:
        transactTable = Table("TID", "Time", "Type", "Amount", "Balance")
        for i in super().getTransactionList()[::-1]:
            transactTable.add_row(*map(str, i))
        return transactTable

    def formHandler(self, event: str, name=None, values: dict = None):
        if event == "Escape":
            self.keyboardListener.on_press = self.HandleInteraction
            return

        try:
            if event == "Submit":
                match (name):
                    case "Login":
                        result = self.login(values["User"], int(values["PIN"]))
                        self.loginForm.setStatus("[bright_green]Logged IN!!")
                        self.history.append(
                            f"[spring_green2]Logged In As : [cyan]{result['Holder']}[/]"
                        )

                    # I'm not gonna implement password checking for Withdraw, Deposit

                    # Gotta stick with the moto
                    case "Withdraw":
                        result = self.withdraw(int(values["Amount"]))
                        self.withdrawForm.setStatus("[bright_green]Amount Withdrawn")
                        self.history.append(f"> Withdrawn: [red]{values['Amount']}[/]")
                    case "Deposit":
                        result = self.deposit(int(values["Amount"]))
                        self.depositForm.setStatus("[bright_green]Amount Deposited")
                        self.history.append(f"> Deposited: [purple]{values['Amount']}[/]")

        except Exception as e:
            if name == "Login":
                self.loginForm.setStatus(str(e))
            if name == "Withdraw":
                self.withdrawForm.setStatus(str(e))
            if name == "Deposit":
                self.depositForm.setStatus(str(e))
        else:
            pass

    def artify(self):
        # Change Art for every sec (this will screw up if live is refreshed with .refresh())
        if self.ticks % self.liveRate == 0:
            self.bankArt["art"] = text2art(self.bankName, font="rand-large").strip("\n")
        # Change color atmost 8 times per sec
        if self.ticks % (math.ceil(self.liveRate / 8)) == 0:
            self.bankArt["color"] = f"[{choice(Available_Colors)}]"

        return self.bankArt["color"] + self.bankArt["art"]

    def insertLive(self, live: Live):
        self.live = live
        self.liveRate = live.refresh_per_second
        self.updateRender()

    def generateTemplate(self):
        self.mainLayout = Layout(name="main")

        self.mainLayout.split_column(
            Layout(name="BankDisplay"),
            Layout(name="body", ratio=2),
            Layout(name="footer", size=5),
        )
        self.mainLayout["body"].split_row(
            Layout(name="Interactable", ratio=2), Layout(name="Output", ratio=4)
        )
        self.mainLayout["Interactable"].split_column(
            Layout(name="Selection"), Layout(name="JARDIS")
        )
        self.mainLayout["footer"].split_row(
            Layout(name="TimeStamp", ratio=2),
            Layout(name="Moto", ratio=4),
        )

    def __rich__(self):
        self.ticks += 1

        return self.mainLayout

    def __del__(self):
        del self.mainLayout


cli = ATMCLI()
with Live(cli, screen=True, refresh_per_second=30) as live:
    cli.insertLive(live)
    while True:
        sleep(10)
