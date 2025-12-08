from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..db import get_db

router = APIRouter(prefix="/meals", tags=["meals"])


# Create a meal record from structured input.
# Input: JSON body matching MealCreate (date YYYY-MM-DD, time HH:MM:SS, optional nutrient floats).
# Output: 201 with Meal schema JSON including generated id; raises validation errors on bad input.
@router.post(
    "",
    response_model=schemas.Meal,
    status_code=status.HTTP_201_CREATED,
    summary="Create a meal",
)
def create_meal(meal: schemas.MealCreate, db: Session = Depends(get_db)):
    """Add a new meal."""
    return crud.add_meal(db, meal)


# List meals with paging controls.
# Input: query params skip>=0, limit>0<=1000.
# Output: list of Meal schema JSON objects.
@router.get(
    "",
    response_model=List[schemas.Meal],
    summary="List meals",
)
def list_meals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0, le=1000),
    db: Session = Depends(get_db),
):
    return crud.list_meals(db, skip=skip, limit=limit)


# List meals that fall within a date range (inclusive), with paging.
# Input: query params start_date/end_date in YYYY-MM-DD, plus skip/limit.
# Output: list of Meal schema JSON objects sorted by date then time.
@router.get(
    "/range",
    response_model=List[schemas.Meal],
    summary="List meals within a date range",
)
def meals_by_date_range(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0, le=1000),
    db: Session = Depends(get_db),
):
    meals = crud.get_meals_by_date_range(
        db,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    return meals


# Retrieve one meal by its database ID.
# Input: path param meal_id (int).
# Output: Meal schema JSON; 404 when missing.
@router.get(
    "/{meal_id}",
    response_model=schemas.Meal,
    summary="Get a meal by ID",
)
def read_meal(meal_id: int, db: Session = Depends(get_db)):
    meal = crud.get_meal(db, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    return meal
