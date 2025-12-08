import csv
import sqlite3
from pathlib import Path
from datetime import datetime, date, time
import sys

# Paths
DB_PATH = Path(__file__).parent /  "nutrition.db"
CSV_PATH = Path(__file__).parent /  "sample_data_meal.csv"

def create_connection():
    """Create a database connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def parse_date(date_str):
    """Parse date string in format 'DD-Mon-YYYY' to date object."""
    try:
        return datetime.strptime(date_str, '%d-%b-%Y').date()
    except (ValueError, TypeError) as e:
        print(f"Error parsing date '{date_str}': {e}")
        return None

def parse_time(time_str):
    """Parse time string in format 'HH:MM AM/PM' to 'HH:MM:SS' string."""
    try:
        # Parse the time and format it as 'HH:MM:SS' for SQLite
        dt = datetime.strptime(time_str, '%I:%M %p')
        return dt.strftime('%H:%M:%S')
    except (ValueError, TypeError) as e:
        print(f"Error parsing time '{time_str}': {e}")
        return None

def import_meals():
    """Import meals from CSV to SQLite database."""
    conn = create_connection()
    if conn is None:
        print("Error: Cannot create database connection.")
        return

    try:
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM meals;")
        
        # Read and insert data from CSV
        with open(CSV_PATH, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file, delimiter='\t')
            for row_num, row in enumerate(csv_reader, 1):
                # Parse date and time
                meal_date = parse_date(row.get('Date', ''))
                meal_time = parse_time(row.get('Time', ''))
                
                if not meal_date or not meal_time:
                    print(f"Skipping row {row_num} due to invalid date/time")
                    continue
                    
                # Convert date to string in YYYY-MM-DD format for SQLite
                meal_date_str = meal_date.strftime('%Y-%m-%d')
                
                # Handle B vitamins - they're combined in the CSV
                b_vitamins = row.get('B_Vitamins', '')
                b1 = '1' if 'B1' in b_vitamins else '0'
                b2 = '1' if 'B2' in b_vitamins else '0'
                b3 = '1' if 'B3' in b_vitamins else '0'
                b5 = '1' if 'B5' in b_vitamins else '0'
                b6 = '1' if 'B6' in b_vitamins else '0'
                b9 = '1' if 'Folate' in b_vitamins or 'B9' in b_vitamins else '0'
                b12 = '1' if 'B12' in b_vitamins else '0'
                
                # Convert numeric values, handling non-numeric cases
                def safe_float(val, default=0.0):
                    if not val:
                        return default
                    try:
                        # Extract first part if there's a space (e.g., '400 mg' -> '400')
                        num_str = str(val).split()[0] if ' ' in str(val) else str(val)
                        return float(num_str)
                    except (ValueError, TypeError):
                        return default
                
                # Insert the data
                try:
                    cursor.execute("""
                        INSERT INTO meals (
                            date, time, meal_type, meal_name, meal_source, food_description,
                            calories, carbohydrates, protein, fats, fiber, iron, calcium,
                            zinc, magnesium, b1, b2, b3, b5, b6, b9, b12, omega3,
                            vitamin_a, vitamin_c, vitamin_e, vitamin_k, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        meal_date_str,
                        meal_time,  # This is already a string in HH:MM:SS format
                        row.get('Meal_type', ''),
                        row.get('Meal_name', ''),
                        row.get('Meal_Source', ''),
                        row.get('Food_Description', ''),
                        safe_float(row.get('Calories')),
                        safe_float(row.get('Carbohydrates')),
                        safe_float(row.get('Protein')),
                        safe_float(row.get('Fats')),
                        safe_float(row.get('Fiber')),
                        safe_float(row.get('Iron')),
                        safe_float(row.get('Calcium')),
                        safe_float(row.get('Zinc')),
                        safe_float(row.get('Magnesium')),
                        float(b1),
                        float(b2),
                        float(b3),
                        float(b5),
                        float(b6),
                        float(b9),
                        float(b12),
                        safe_float(row.get('Omega_3s')),
                        safe_float(row.get('Vitamin_A')),
                        safe_float(row.get('Vitamin_C')),
                        safe_float(row.get('Vitamin_E')),
                        safe_float(row.get('Vitamin_K')),
                        row.get('Notes', '')
                    ))
                except sqlite3.Error as e:
                    print(f"Error inserting row {row_num}: {e}")
                    print(f"Row data: {row}")
                    conn.rollback()
                    return
        
        # Commit the changes
        conn.commit()
        print(f"Successfully imported {cursor.rowcount} meals into the database.")
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting meal import...")
    import_meals()
    print("Import completed.")
