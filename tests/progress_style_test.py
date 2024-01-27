from rich.style import Style
from rich.text import Text

from BAET.display.progress_status import ProgressStatus, ProgressStatusType
from BAET.display.progress_style import ProgressStyle


def test_call_applies_style() -> None:
    waiting_style: dict[ProgressStatusType, str | Style] = {ProgressStatus.Running: "blue"}
    input_str = "test message"
    style = ProgressStyle(style_dict=waiting_style)
    test_style = Style.parse(waiting_style[ProgressStatus.Running])

    assert style(input_str, status="Running").markup == Text(input_str, style=test_style).markup
