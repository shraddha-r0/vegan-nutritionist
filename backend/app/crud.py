"""
CRUD (Create, Read, Update, Delete) operations for the Vegan Nutritionist application.

This module provides functions to interact with the database for meal-related operations.
All database operations should go through these functions to maintain data consistency.
"""
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import and_
from sqlalchemy.orm import Session

from . import models, schemas

### Meal CRUD Operations

#### Create Meal

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

def get_meals_by_date_range(
    db: Session,
    start_date: date,
    end_date: date,
    skip: int = 0,
    limit: int = 100
) -> List[models.Meal]:
    """
    Retrieve meals within a date range.

    Args:
        db: Database session
        start_date: Start date of the range (inclusive)
        end_date: End date of the range (inclusive)
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (max 1000)

    Returns:
        List[models.Meal]: List of meal objects within the date range

    Example:
        >>> meals = get_meals_by_date_range(
        ...     db,
        ...     date(2023, 12, 1),
        ...     date(2023, 12, 31)
        ... )
    """
    return (
        db.query(models.Meal)
        .filter(
            and_(
                models.Meal.date >= start_date,
                models.Meal.date <= end_date
            )
        )
        .order_by(models.Meal.date, models.Meal.time)
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_meals_by_date(
    db: Session, 
    meal_date: date,
    skip: int = 0, 
    limit: int = 100
) -> List[models.Meal]:
    """
    Retrieve all meals for a specific date.

    Args:
        db: Database session
        meal_date: Date to filter meals by (inclusive)
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (max 1000)

    Returns:
        List[models.Meal]: List of meal objects for the specified date

    Example:
        >>> from datetime import date
        >>> meals = get_meals_by_date(db, date(2023, 12, 8))
    """
    return (
        db.query(models.Meal)
        .filter(models.Meal.date == meal_date)
        .order_by(models.Meal.time)
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_meals_by_date_and_type(
    db: Session, 
    meal_date: date,
    meal_type: str,
    skip: int = 0, 
    limit: int = 100
) -> List[models.Meal]:
    """
    Retrieve meals for a specific date and meal type.

    Args:
        db: Database session
        meal_date: Date to filter meals by
        meal_type: Type of meal (e.g., 'Breakfast', 'Lunch', 'Dinner')
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (max 1000)

    Returns:
        List[models.Meal]: List of meal objects matching the criteria

    Example:
        >>> meals = get_meals_by_date_and_type(
        ...     db, 
        ...     date(2023, 12, 8),
        ...     'Breakfast'
        ... )
    """
    return (
        db.query(models.Meal)
        .filter(
            and_(
                models.Meal.date == meal_date,
                models.Meal.meal_type == meal_type.capitalize()
            )
        )
        .order_by(models.Meal.time)
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_meals_by_date_range_and_source(
    db: Session, 
    start_date: date,
    end_date: date,
    meal_source: str,
    skip: int = 0,
    limit: int = 100
) -> List[models.Meal]:
    """
    Retrieve meals within a date range from a specific source.

    Args:
        db: Database session
        start_date: Start date of the range (inclusive)
        end_date: End date of the range (inclusive)
        meal_source: Source of the meals (e.g., 'Home', 'Restaurant')
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (max 1000)

    Returns:
        List[models.Meal]: List of meal objects matching the criteria

    Example:
        >>> meals = get_meals_by_date_range_and_source(
        ...     db,
        ...     date(2023, 12, 1),
        ...     date(2023, 12, 31),
        ...     'Restaurant'
        ... )
    """
    return (
        db.query(models.Meal)
        .filter(
            and_(
                models.Meal.date >= start_date,
                models.Meal.date <= end_date,
                models.Meal.meal_source.ilike(f"%{meal_source}%")
            )
        )
        .order_by(models.Meal.date, models.Meal.time)
        .offset(skip)
        .limit(limit)
        .all()
    )