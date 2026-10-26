"""Building PromQL/LogQL selectors from alert labels, safely."""


def quote(value: str) -> str:
    """A label value as a quoted string literal. Escaping backslashes and quotes stops a
    strange label value from breaking out of the selector and changing the query."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return f'"{escaped}"'


def selector(labels: dict[str, str]) -> str:
    """{namespace="hiretrack",app="api"} from a dict, keys in a stable order."""
    return "{" + ",".join(f"{key}={quote(value)}" for key, value in sorted(labels.items())) + "}"
