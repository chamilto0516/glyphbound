from textual.app import App, ComposeResult
from textual.widgets import Label

class GlyphboundApp(App):
    CSS = """
    Screen {
        align: center middle;
    }

    Label {
        text-style: bold;
    }
    """

    BINDINGS = [("q", "quit", "Quit"), ("escape", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Label("Glyphbound")
