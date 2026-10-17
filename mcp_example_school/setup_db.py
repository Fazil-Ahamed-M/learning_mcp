import random
from datetime import date, timedelta

from db import get_connection

FIRST_NAMES = ["Aarav", "Diya", "Kabir", "Ananya", "Rohan", "Meera", "Arjun", "Isha", "Vihaan", "Saanvi",
               "Aditya", "Priya", "Karan", "Neha", "Rahul", "Sneha", "Dev", "Pooja", "Nikhil", "Tara"]
LAST_NAMES = ["Sharma", "Iyer", "Khan", "Reddy", "Nair", "Gupta", "Das", "Menon", "Patel", "Singh"]
MOTHER_NAMES = ["Lakshmi", "Sunita", "Fatima", "Kavya", "Anjali", "Rekha", "Divya", "Geeta", "Shalini", "Nisha"]
FATHER_NAMES = ["Rajesh", "Suresh", "Imran", "Vikram", "Manoj", "Anil", "Sanjay", "Ravi", "Prakash", "Ashok"]
OCCUPATIONS = ["Teacher", "Doctor", "Engineer", "Lawyer", "Accountant", "Farmer", "Nurse",
               "Business Owner", "Banker", "Homemaker", "Architect", "Police Officer"]

CREATE_PERSONAL_DATA = """
CREATE TABLE personal_data (
    sl_no INT PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL,
    student_dob DATE NOT NULL,
    mother_name VARCHAR(100),
    mother_occupation VARCHAR(100),
    father_name VARCHAR(100),
    father_occupation VARCHAR(100)
)
"""

CREATE_ACADEMIC_DATA = """
CREATE TABLE academic_data (
    sl_no INT PRIMARY KEY,
    marks_english INT CHECK (marks_english BETWEEN 0 AND 100),
    marks_science INT CHECK (marks_science BETWEEN 0 AND 100),
    marks_business_education INT CHECK (marks_business_education BETWEEN 0 AND 100),
    marks_finance INT CHECK (marks_finance BETWEEN 0 AND 100),
    FOREIGN KEY (sl_no) REFERENCES personal_data(sl_no)
)
"""


def make_students(count: int = 20) -> tuple[list, list]:
    """Generate synthetic personal and academic rows."""
    random.seed(42)  # same data on every run
    personal_rows, academic_rows = [], []
    for sl_no in range(1, count + 1):
        last_name = random.choice(LAST_NAMES)
        dob = date(2008, 1, 1) + timedelta(days=random.randint(0, 3 * 365))
        personal_rows.append((
            sl_no,
            f"{FIRST_NAMES[sl_no - 1]} {last_name}",
            dob,
            f"{random.choice(MOTHER_NAMES)} {last_name}",
            random.choice(OCCUPATIONS),
            f"{random.choice(FATHER_NAMES)} {last_name}",
            random.choice(OCCUPATIONS),
        ))
        academic_rows.append((sl_no, *[random.randint(35, 100) for _ in range(4)]))
    return personal_rows, academic_rows


def main():
    # Connect without a database first so we can create it
    connection = get_connection(use_database=False)
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS school")
            cursor.execute("USE school")

            # Start fresh every time the script runs
            cursor.execute("DROP TABLE IF EXISTS academic_data")
            cursor.execute("DROP TABLE IF EXISTS personal_data")
            cursor.execute(CREATE_PERSONAL_DATA)
            cursor.execute(CREATE_ACADEMIC_DATA)

            personal_rows, academic_rows = make_students()
            cursor.executemany("INSERT INTO personal_data VALUES (%s, %s, %s, %s, %s, %s, %s)", personal_rows)
            cursor.executemany("INSERT INTO academic_data VALUES (%s, %s, %s, %s, %s)", academic_rows)
        connection.commit()

    print(f"Database 'school' is ready with {len(personal_rows)} students.")


if __name__ == "__main__":
    main()
