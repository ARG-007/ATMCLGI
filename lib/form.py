from typing import Dict, List

from pynput.keyboard import Key
from pynput.keyboard import Listener as KeyboardListener
from rich import box
from rich.table import Table

from .utility import Updatable


class Form:
    def __init__(self, name, callback, fields: List[str]):
        self.name = name
        self.callback = callback

        self.fields: List[str] = fields
        self.fieldsMap: Dict[str, str] = {i: "" for i in fields}
        self._focused = 0

        self.form = Table(
            show_header=False,
            box=box.HEAVY_EDGE,
            expand=True,
            show_lines=True,
            caption_style="red",
        )
        self.form.add_column(max_width=10)
        self.form.add_column(max_width=30)

        for i in self.fields:
            self.form.add_row(i, Updatable(self.getFieldValue, i))

        self.focused = 0

    @property
    def focused(self):
        return self._focused

    @focused.setter
    def focused(self, newValue):
        self.form.rows[self._focused].style = ""
        self._focused = newValue
        self.form.rows[self._focused].style = "violet"

    def setStatus(self, message):
        self.form.caption = message

    def getFieldValue(self, field):
        return self.fieldsMap[field]

    @property
    def getFocused(self):
        return self.fields[self.focused]

    def keyHandler(self, key: Key):
        try:
            k = key.char
            self.fieldsMap[self.getFocused] += k
        except:
            match (key):
                case Key.up:
                    self.focused = (self.focused - 1) % (len(self.fields))
                case Key.down:
                    self.focused = (self.focused + 1) % (len(self.fields))
                case Key.enter:
                    self.setStatus(f"Trying to {self.name}")
                    self.callback(name=self.name, event="Submit", values=self.fieldsMap)
                case Key.backspace:
                    self.fieldsMap[self.getFocused] = self.fieldsMap[self.getFocused][
                        :-1
                    ]
                case Key.esc:
                    self.callback(event="Escape")

    def __rich__(self):
        return self.form
