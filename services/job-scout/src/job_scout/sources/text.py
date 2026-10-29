"""Small text helpers shared by the board adapters."""

import html
import re
from datetime import UTC, datetime
from html.parser import HTMLParser

_WHITESPACE = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINES = re.compile(r"\n\s*\n+")
_BLOCK_TAGS = frozenset({"p", "br", "li", "div", "h1", "h2", "h3", "h4", "ul", "ol", "tr"})


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def html_to_text(markup: str, max_chars: int) -> str:
    """Strip tags, keep line breaks between blocks. Never rendered as HTML, so it's safe."""
    parser = _TextExtractor()
    parser.feed(html.unescape(markup))  # Greenhouse sends the HTML itself entity-escaped
    text = _WHITESPACE.sub(" ", "".join(parser.parts))
    text = _BLANK_LINES.sub("\n\n", text).strip()
    return text[:max_chars]


def parse_iso(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def looks_remote(*values: str | None) -> bool:
    return any(v and "remote" in v.lower() for v in values)
