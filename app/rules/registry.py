"""Danh sách rule mặc định mà analyzer sẽ duyệt."""

from app.rules.alignment import AlignmentRule
from app.rules.base import Rule
from app.rules.capitalization import CapitalizationRule
from app.rules.font import FontRule, FontSizeRule
from app.rules.indent import IndentRule
from app.rules.margin import MarginRule
from app.rules.page import PageSizeRule
from app.rules.spacing import LineSpacingRule


def default_rules() -> list[Rule]:
    return [
        FontRule(),
        FontSizeRule(),
        MarginRule(),
        LineSpacingRule(),
        PageSizeRule(),
        AlignmentRule(),
        IndentRule(),
        CapitalizationRule(),
    ]
