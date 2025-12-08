"""
Pydantic models for request/response validation.
"""
from datetime import date, time
from typing import List, Optional
from pydantic import BaseModel

# Shared properties
class MealBase(BaseModel):
    date: date
    time: time
    meal_type: str
    meal_name: str
    meal_source: Optional[str] = None
    food_description: Optional[str] = None
    calories: Optional[float] = None
    carbohydrates: Optional[float] = None
    protein: Optional[float] = None
    fats: Optional[float] = None
    fiber: Optional[float] = None
    iron: Optional[float] = None
    calcium: Optional[float] = None
    zinc: Optional[float] = None
    magnesium: Optional[float] = None
    b1: Optional[float] = None
    b2: Optional[float] = None
    b3: Optional[float] = None
    b5: Optional[float] = None
    b6: Optional[float] = None
    b9: Optional[float] = None
    b12: Optional[float] = None
    omega3: Optional[float] = None
    vitamin_a: Optional[float] = None
    vitamin_c: Optional[float] = None
    vitamin_e: Optional[float] = None
    vitamin_k: Optional[float] = None
    notes: Optional[str] = None

# Properties to receive on meal creation
class MealCreate(MealBase):
    pass

# Properties to receive on meal update
class MealUpdate(BaseModel):
    date: Optional[date] = None
    time: Optional[time] = None
    meal_type: Optional[str] = None
    meal_name: Optional[str] = None
    meal_source: Optional[str] = None
    food_description: Optional[str] = None
    calories: Optional[float] = None
    carbohydrates: Optional[float] = None
    protein: Optional[float] = None
    fats: Optional[float] = None
    fiber: Optional[float] = None
    iron: Optional[float] = None
    calcium: Optional[float] = None
    zinc: Optional[float] = None
    magnesium: Optional[float] = None
    b1: Optional[float] = None
    b2: Optional[float] = None
    b3: Optional[float] = None
    b5: Optional[float] = None
    b6: Optional[float] = None
    b9: Optional[float] = None
    b12: Optional[float] = None
    omega3: Optional[float] = None
    vitamin_a: Optional[float] = None
    vitamin_c: Optional[float] = None
    vitamin_e: Optional[float] = None
    vitamin_k: Optional[float] = None
    notes: Optional[str] = None

# Properties shared by models stored in DB
class MealInDBBase(MealBase):
    id: int

    class Config:
        orm_mode = True

# Properties to return to client
class Meal(MealInDBBase):
    pass

# Properties stored in DB
class MealInDB(MealInDBBase):
    pass
