from fastapi import FastAPI

from .api import meals as meals_router
from .db import init_db

app = FastAPI(
    title="Vegan Nutritionist API",
    version="0.1.0",
    description="API for logging meals and retrieving nutrition data.",
)


# Build DB tables at startup so the API can serve immediately.
# Input: none; Output: side effect of creating tables in SQLite file if absent.
@app.on_event("startup")
def on_startup() -> None:
    """Ensure database tables exist."""
    init_db()


# Lightweight health endpoint for uptime checks.
# Input: none; Output: JSON {"status": "ok"} with 200.
@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}


app.include_router(meals_router.router)
