"""Danh sách rule mặc định mà analyzer sẽ duyệt."""

from app.rules.alignment import AlignmentRule
from app.rules.base import Rule
from app.rules.capitalization import CapitalizationRule
from app.rules.color import ColorRule
from app.rules.component_style import ComponentStyleRule
from app.rules.font import FontRule, FontSizeRule
from app.rules.heading_number import HeadingNumberRule
from app.rules.indent import IndentRule
from app.rules.margin import MarginRule
from app.rules.page import PageSizeRule
from app.rules.page_number import PageNumberRule
from app.rules.paragraph_spacing import ParagraphSpacingRule
from app.rules.spacing import LineSpacingRule


def default_rules() -> list[Rule]:
    return [
        FontRule(),
        FontSizeRule(),
        ComponentStyleRule(),
        ColorRule(),
        MarginRule(),
        LineSpacingRule(),
        ParagraphSpacingRule(),
        PageSizeRule(),
        PageNumberRule(),
        AlignmentRule(),
        IndentRule(),
        HeadingNumberRule(),
        CapitalizationRule(),
    ]
