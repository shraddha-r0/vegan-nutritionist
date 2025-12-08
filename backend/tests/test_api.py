"""
Tests for FastAPI meal endpoints using an in-memory SQLite database.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend package is on path when pytest is invoked from repo root.
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.db import get_db
from app.models import Base

# Use isolated in-memory DB for tests.
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Single shared in-memory connection
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Provide a fresh database session per test, with tables recreated each time.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    FastAPI TestClient that overrides the default get_db dependency to use the
    in-memory session.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def make_meal_payload(**overrides):
    """
    Build a minimal valid meal payload; override any field via kwargs.
    """
    base = {
        "date": "2024-12-09",
        "time": "09:00:00",
        "meal_type": "Breakfast",
        "meal_name": "Test meal",
        "calories": 250.0,
        "protein": 15.5,
    }
    base.update(overrides)
    return base


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_meal(client):
    payload = make_meal_payload(meal_name="Created meal")
    response = client.post("/meals", json=payload)
    body = response.json()
    assert response.status_code == 201
    assert body["id"] == 1
    assert body["meal_name"] == "Created meal"
    assert body["calories"] == payload["calories"]


def test_get_meal_by_id(client):
    payload = make_meal_payload(meal_name="Fetch me")
    post_resp = client.post("/meals", json=payload)
    meal_id = post_resp.json()["id"]

    get_resp = client.get(f"/meals/{meal_id}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["id"] == meal_id
    assert fetched["meal_type"] == payload["meal_type"]
    assert fetched["meal_name"] == payload["meal_name"]


def test_list_meals_with_paging(client):
    client.post("/meals", json=make_meal_payload(meal_name="Meal A"))
    client.post("/meals", json=make_meal_payload(meal_name="Meal B", time="12:00:00"))

    list_resp = client.get("/meals", params={"skip": 0, "limit": 10})
    assert list_resp.status_code == 200
    meals = list_resp.json()
    names = {m["meal_name"] for m in meals}
    assert {"Meal A", "Meal B"} <= names


def test_meals_by_date_range(client):
    client.post("/meals", json=make_meal_payload(meal_name="Day 1", date="2024-12-09"))
    client.post("/meals", json=make_meal_payload(meal_name="Day 2", date="2024-12-15"))

    range_resp = client.get(
        "/meals/range",
        params={"start_date": "2024-12-10", "end_date": "2024-12-12"},
    )
    assert range_resp.status_code == 200
    meals = range_resp.json()
    assert len(meals) == 0

    inclusive_resp = client.get(
        "/meals/range",
        params={"start_date": "2024-12-09", "end_date": "2024-12-10"},
    )
    assert inclusive_resp.status_code == 200
    names = {m["meal_name"] for m in inclusive_resp.json()}
    assert names == {"Day 1"}
