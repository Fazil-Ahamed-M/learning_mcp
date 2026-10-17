import random
from datetime import date, timedelta

from db import get_connection

# One entry per family: (student first name, father first name, mother full name, family name).
# In Gulf families the mother usually keeps her own family name; the student shares the father's.
FAMILIES = [
    ("Omar", "Ahmed", "Mariam Al Hashimi", "Al Mansoori"),
    ("Arjun", "Rajesh", "Priya Sharma", "Sharma"),
    ("Fatima", "Khalid", "Aisha Al Suwaidi", "Al Nuaimi"),
    ("Yousef", "Hamad", "Noora Al Kuwari", "Al Thani"),
    ("Diya", "Suresh", "Lakshmi Nair", "Nair"),
    ("Aisha", "Saeed", "Latifa Al Mazrouei", "Al Falasi"),
    ("Khalid", "Rashid", "Hessa Al Marri", "Al Kaabi"),
    ("Daniel", "George", "Susan Thomas", "Thomas"),
    ("Mariam", "Abdullah", "Shaikha Al Dhaheri", "Al Shamsi"),
    ("Ali", "Mohammed", "Amna Al Mulla", "Al Mazrouei"),
    ("Maria", "Jose", "Ana Santos", "Santos"),
    ("Noora", "Jassim", "Moza Al Sulaiti", "Al Kuwari"),
    ("Hamdan", "Sultan", "Reem Al Qasimi", "Al Ketbi"),
    ("Rohan", "Anil", "Divya Menon", "Menon"),
    ("Sara", "Faisal", "Huda Al Ansari", "Al Marri"),
    ("Zayed", "Majid", "Alia Al Romaithi", "Al Muhairi"),
    ("Ananya", "Ravi", "Kavya Iyer", "Iyer"),
    ("Layla", "Tariq", "Salma Haddad", "Al Hammadi"),
    ("Kabir", "Sanjay", "Neha Patel", "Patel"),
    ("Ibrahim", "Imran", "Ayesha Siddiqui", "Khan"),
]
FATHER_OCCUPATIONS = ["Engineer", "Doctor", "Government Officer", "Business Owner", "Banker", "Pilot",
                      "Lawyer", "Accountant", "Architect", "Police Officer", "Professor", "IT Manager"]
MOTHER_OCCUPATIONS = ["Teacher", "Doctor", "Engineer", "Homemaker", "Pharmacist", "Banker",
                      "Nurse", "Architect", "Government Officer", "Business Owner", "Lawyer", "Professor"]

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


def make_students() -> tuple[list, list]:
    """Build personal and academic rows from FAMILIES, with random DOBs, jobs and marks."""
    random.seed(42)  # same data on every run
    personal_rows, academic_rows = [], []
    for sl_no, (student, father, mother, family_name) in enumerate(FAMILIES, start=1):
        dob = date(2008, 1, 1) + timedelta(days=random.randint(0, 3 * 365))
        personal_rows.append((
            sl_no,
            f"{student} {family_name}",
            dob,
            mother,
            random.choice(MOTHER_OCCUPATIONS),
            f"{father} {family_name}",
            random.choice(FATHER_OCCUPATIONS),
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
