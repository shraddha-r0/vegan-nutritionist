CREATE TABLE meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    time TEXT,
    meal_type TEXT,
    meal_name TEXT,
    meal_source TEXT,
    food_description TEXT,

    calories REAL,
    carbohydrates REAL,
    protein REAL,
    fats REAL,
    fiber REAL,

    iron REAL,
    calcium REAL,
    zinc REAL,
    magnesium REAL,

    b1 REAL,
    b2 REAL,
    b3 REAL,
    b5 REAL,
    b6 REAL,
    b9 REAL,
    b12 REAL,

    omega3 REAL,
    vitamin_a REAL,
    vitamin_c REAL,
    vitamin_e REAL,
    vitamin_k REAL,

    notes TEXT
);

CREATE TABLE nutrient_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    unit TEXT,
    aliases TEXT,
    description TEXT,
    sources TEXT,
    rda REAL
);