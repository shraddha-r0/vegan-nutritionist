from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..db import get_db

router = APIRouter(prefix="/meals", tags=["meals"])

# Create a meal record from structured input.
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
@router.get(
    "",
    response_model=List[schemas.Meal],
    summary="List all meals with pagination",
)
def list_meals(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, gt=0, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
):
    """
    Retrieve all meals with pagination support.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (1-1000)
        db: Database session (injected by FastAPI)
        
    Returns:
        List of all meals, ordered by date and time
    """
    return crud.list_meals(db, skip=skip, limit=limit)

# List meals within a date range
@router.get(
    "/range",
    response_model=List[schemas.Meal],
    summary="List meals within a date range",
)
def meals_by_date_range(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, gt=0, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
):
    """
    Retrieve meals within a specific date range.
    
    Args:
        start_date: Start date of the range (inclusive, YYYY-MM-DD)
        end_date: End date of the range (inclusive, YYYY-MM-DD)
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (1-1000)
        db: Database session (injected by FastAPI)
        
    Returns:
        List of meals within the date range, ordered by date and time
    """
    return crud.get_meals_by_date_range(
        db,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )

# Get meals by date range and source
@router.get(
    "/by-source",
    response_model=List[schemas.Meal],
    summary="Get meals by date range and source",
)
def get_meals_by_source(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    source: str = Query(..., description="Source of the meals (e.g., Home, Restaurant)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, gt=0, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
):
    """
    Retrieve meals within a date range from a specific source.
    
    Args:
        start_date: Start date of the range (inclusive, YYYY-MM-DD)
        end_date: End date of the range (inclusive, YYYY-MM-DD)
        source: Source of the meals (e.g., Home, Restaurant)
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (1-1000)
        db: Database session (injected by FastAPI)
        
    Returns:
        List of meals matching the date range and source, ordered by date and time
    """
    return crud.get_meals_by_date_range_and_source(
        db,
        start_date=start_date,
        end_date=end_date,
        meal_source=source,
        skip=skip,
        limit=limit
    )

# Get meals by specific date
@router.get(
    "/date/{meal_date}",
    response_model=List[schemas.Meal],
    summary="Get meals by date",
)
def get_meals_for_date(
    meal_date: date,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, gt=0, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
):
    """
    Retrieve all meals for a specific date.
    
    Args:
        meal_date: The date to filter meals by (YYYY-MM-DD)
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (1-1000)
        db: Database session (injected by FastAPI)
        
    Returns:
        List of meals for the specified date, ordered by time
    """
    return crud.get_meals_by_date(
        db, 
        meal_date=meal_date,
        skip=skip, 
        limit=limit
    )

# Get meals by date and meal type
@router.get(
    "/date/{meal_date}/type/{meal_type}",
    response_model=List[schemas.Meal],
    summary="Get meals by date and type",
)
def get_meals_for_date_and_type(
    meal_date: date,
    meal_type: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, gt=0, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
):
    """
    Retrieve meals for a specific date and meal type.
    
    Args:
        meal_date: The date to filter meals by (YYYY-MM-DD)
        meal_type: Type of meal (e.g., Breakfast, Lunch, Dinner)
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (1-1000)
        db: Database session (injected by FastAPI)
        
    Returns:
        List of meals matching the date and type, ordered by time
    """
    return crud.get_meals_by_date_and_type(
        db,
        meal_date=meal_date,
        meal_type=meal_type,
        skip=skip,
        limit=limit
    )

# Get meal by ID (keep this last as it's a catch-all)
@router.get(
    "/{meal_id}",
    response_model=schemas.Meal,
    summary="Get a meal by ID",
)
def read_meal(meal_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single meal by its unique ID.
    
    Args:
        meal_id: The unique identifier of the meal to retrieve
        db: Database session (injected by FastAPI)
        
    Returns:
        The meal data if found
        
    Raises:
        HTTPException: 404 if no meal with the given ID exists
    """
    meal = crud.get_meal(db, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    return meal