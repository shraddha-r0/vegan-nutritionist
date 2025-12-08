# backend/app/models.py

from sqlalchemy import Column, Integer, String, Float, Text, Date, Time
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date)
    time = Column(Time)
    meal_type = Column(String)
    meal_name = Column(String)
    meal_source = Column(String)
    food_description = Column(Text)

    # Macronutrients
    calories = Column(Float)
    carbohydrates = Column(Float)
    protein = Column(Float)
    fats = Column(Float)
    fiber = Column(Float)

    # Minerals & vitamins
    iron = Column(Float)
    calcium = Column(Float)
    zinc = Column(Float)
    magnesium = Column(Float)

    # B vitamins
    b1 = Column(Float)
    b2 = Column(Float)
    b3 = Column(Float)
    b5 = Column(Float)
    b6 = Column(Float)
    b9 = Column(Float)
    b12 = Column(Float)

    # Other nutrients
    omega3 = Column(Float)
    vitamin_a = Column(Float)
    vitamin_c = Column(Float)
    vitamin_e = Column(Float)
    vitamin_k = Column(Float)

    notes = Column(Text)


class NutrientMetadata(Base):
    __tablename__ = "nutrient_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)
    unit = Column(String)
    aliases = Column(Text)          # comma-separated or JSON string
    description = Column(Text)
    sources = Column(Text)
    rda = Column(Float)