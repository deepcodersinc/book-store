"""Template wiring shared by the storefront and the admin console.

Each app keeps its own templates; both fall back to the shared layout here.
"""

from pathlib import Path

from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

SHARED_TEMPLATES = Path(__file__).parent / "templates"


def money(cents: int | None) -> str:
    if cents is None:
        return "—"
    return f"${cents / 100:,.2f}"


def build(app_templates: Path) -> Jinja2Templates:
    templates = Jinja2Templates(directory=str(app_templates))
    templates.env.loader = ChoiceLoader([
        FileSystemLoader(str(app_templates)),
        FileSystemLoader(str(SHARED_TEMPLATES)),
    ])
    templates.env.filters["money"] = money
    return templates
