"""
CRUD operations for the Vegan Nutritionist application.
"""
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from . import models, schemas

# Insert a new meal record using validated Pydantic payload.
# Input: Session plus schemas.MealCreate (dict-like), values already typed (date, time, floats).
# Output: models.Meal ORM object refreshed from DB (includes generated id).
def add_meal(db: Session, meal_data: schemas.MealCreate) -> models.Meal:
    """
    Add a new meal to the database.
    
    Args:
        db: Database session
        meal_data: Pydantic model containing meal data
        
    Returns:
        The created meal record
    """
    db_meal = models.Meal(**meal_data.dict())
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return db_meal

# Retrieve a specific meal by primary key.
# Input: Session and integer meal_id.
# Output: models.Meal ORM object, or None if not found.
def get_meal(db: Session, meal_id: int) -> Optional[models.Meal]:
    """
    Retrieve a single meal by its ID.
    
    Args:
        db: Database session
        meal_id: ID of the meal to retrieve
        
    Returns:
        The meal record if found, None otherwise
    """
    return db.query(models.Meal).filter(models.Meal.id == meal_id).first()

# List meals with optional pagination offsets.
# Input: Session, skip (offset >=0), limit (max rows).
# Output: list[models.Meal] ordered by insertion (SQLite default).
def list_meals(db: Session, skip: int = 0, limit: int = 100) -> List[models.Meal]:
    """
    List all meals with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of meal records
    """
    return db.query(models.Meal).offset(skip).limit(limit).all()

# Fetch meals that fall within an inclusive date range, ordered by date/time.
# Input: Session; start_date/end_date are datetime.date; skip/limit for paging.
# Output: list[models.Meal] sorted ascending by date then time.
def get_meals_by_date_range(
    db: Session, 
    start_date: date, 
    end_date: date,
    skip: int = 0,
    limit: int = 100
) -> List[models.Meal]:
    """
    Get meals within a specific date range.
    
    Args:
        db: Database session
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of meal records within the date range
    """
    return (
        db.query(models.Meal)
        .filter(models.Meal.date >= start_date, models.Meal.date <= end_date)
        .order_by(models.Meal.date, models.Meal.time)
        .offset(skip)
        .limit(limit)
        .all()
    )
