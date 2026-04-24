"""
Shared utility functions.
"""


def strip_patterns(obj: object) -> None:
    """Recursively remove 'pattern' keys from a JSON schema dict.

    Some MCP servers emit JSON schemas with lookahead regexes that are
    rejected by certain LLM APIs (e.g. Groq). This patches schemas in-place.
    """
    if isinstance(obj, dict):
        obj.pop("pattern", None)
        for v in list(obj.values()):
            strip_patterns(v)
    elif isinstance(obj, list):
        for item in obj:
            strip_patterns(item)
