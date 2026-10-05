"""Small SQL helpers shared by repositories."""


def like_pattern(text: str) -> str:
    """Turn user search text into a safe ILIKE pattern ('%' and '_' are matched literally)."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"
