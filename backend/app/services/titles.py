"""Movie title helpers shared by the picker, search and results (v2)."""

import re

# MovieLens files sort titles by moving the leading article to the end: "Dark Knight, The".
_TRAILING_ARTICLE = re.compile(r"^(?P<rest>.+), (?P<article>The|A|An|La|Le|Les|Il|El|Die|Das|Der)(?P<aka> \(.+\))?$")
_NOT_ALPHANUMERIC = re.compile(r"[^0-9a-z]+")


def display_title(title: str) -> str:
    """'Dark Knight, The' -> 'The Dark Knight'; a trailing alternate title in brackets stays at the end."""
    match = _TRAILING_ARTICLE.match(title)
    if not match:
        return title
    return f"{match['article']} {match['rest']}{match['aka'] or ''}"


def search_key(text: str) -> str:
    """Lowercase, punctuation as spaces, so 'spider man' finds 'Spider-Man' and 'wall e' finds 'WALL·E'."""
    return _NOT_ALPHANUMERIC.sub(" ", text.lower()).strip()
