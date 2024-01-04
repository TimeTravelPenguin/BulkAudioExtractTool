from rich.style import Style
from rich.text import Text

from BAET.progress_status import ProgressStatusLiteral
from BAET.progress_style import ProgressStyle


def test_call_applies_style() -> None:
    waiting_style: dict[ProgressStatusLiteral, str] = {"Running": "blue"}
    input_str = "test message"
    style = ProgressStyle(waiting_style)
    test_style = Style.parse(waiting_style["Running"])

    assert style(input_str, status="Running").markup == Text(input_str, style=test_style).markup
