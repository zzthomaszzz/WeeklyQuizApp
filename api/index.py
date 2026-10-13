from app.main import app

# Vercel imports this module and looks for `app`. The re-export is the
# entrypoint, not an unused import.
__all__ = ["app"]
