"""Custom ASGI app that mounts static file serving on top of LangGraph."""
from pathlib import Path
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

IMAGES_DIR = Path(__file__).parent / "generated_images"
IMAGES_DIR.mkdir(exist_ok=True)

app = Starlette(
    routes=[
        Mount("/images/generated_images", app=StaticFiles(directory=str(IMAGES_DIR)), name="images"),
    ]
)
