"""
CRUD operations for the Vegan Nutritionist application.
"""
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from . import models, schemas

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
