from rich import box
from rich.align import Align
from rich.panel import Panel
from rich.style import Style


def createPanel(
    value,
    box: box = box.SQUARE,
    box_style: Style | str = "red",
    font_style: Style | str = "yellow",
    alignment: tuple[str] = ("center", "middle"),
):
    return Panel(
        Align(value, align=alignment[0], vertical=alignment[1], style=font_style),
        box=box,
        style=box_style,
    )


class Updatable:
    def __init__(self, callback, *args):
        self.callback = callback
        self.args = args

    def __rich__(self):
        return self.callback(*self.args)
