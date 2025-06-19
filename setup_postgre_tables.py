import psycopg2
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


def create_table(cur, table_name, definition):
    """Создает таблицу с обработкой ошибок"""
    try:
        cur.execute(f"CREATE TABLE IF NOT EXISTS {table_name} {definition}")
        print(f"Таблица {table_name} успешно создана")
    except Exception as e:
        print(f"Ошибка при создании таблицы {table_name}: {e}")
        raise


def setup_tables():
    """Создает все таблицы в базе данных"""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()

    tables = {
        "Universities": """
            (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                address VARCHAR(255) NOT NULL,
                founded_date DATE NOT NULL
            )
        """,
        "Institutes": """
            (
                id SERIAL PRIMARY KEY,
                university_id INTEGER REFERENCES Universities(id),
                name VARCHAR(255) NOT NULL
            )
        """,
        "Departments": """
            (
                id SERIAL PRIMARY KEY,
                institute_id INTEGER REFERENCES Institutes(id),
                name VARCHAR(255) NOT NULL
            )
        """,
        "Specialties": """
            (
                id SERIAL PRIMARY KEY,
                code VARCHAR(20) NOT NULL,
                name VARCHAR(255) NOT NULL
            )
        """,
        "Student_Groups": """
            (
                id SERIAL PRIMARY KEY,
                department_id INTEGER REFERENCES Departments(id),
                specialty_id INTEGER REFERENCES Specialties(id),
                name VARCHAR(50) NOT NULL,
                course_year INTEGER
            )
        """,
        "Students": """
            (
                id SERIAL PRIMARY KEY,
                group_id INTEGER REFERENCES Student_Groups(id),
                name VARCHAR(255) NOT NULL,
                enrollment_year INTEGER,
                date_of_birth DATE,
                email VARCHAR(255),
                book_number VARCHAR(20)
            )
        """,
        "Course_of_classes": """
            (
                id SERIAL PRIMARY KEY,
                department_id INTEGER REFERENCES Departments(id),
                specialty_id INTEGER REFERENCES Specialties(id),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                tech_requirements TEXT
            )
        """,
        "Class": """
            (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                course_of_class_id INTEGER REFERENCES Course_of_classes(id),
                type VARCHAR(50) NOT NULL
            )
        """,
        "Class_Materials": """
            (
                id SERIAL PRIMARY KEY,
                class_id INTEGER REFERENCES Class(id),
                content TEXT
            )
        """,
        "Schedule": """
            (
                id SERIAL PRIMARY KEY,
                group_id INTEGER REFERENCES Student_Groups(id),
                course_of_class_id INTEGER REFERENCES Course_of_classes(id),
                room VARCHAR(50),
                scheduled_date DATE,
                start_time TIME,
                end_time TIME
            )
        """,
        "Attendance": """
            (
                id SERIAL PRIMARY KEY,
                schedule_id INTEGER REFERENCES Schedule(id),
                student_id INTEGER REFERENCES Students(id),
                attended BOOLEAN NOT NULL,
                absence_reason TEXT
            )
        """
    }

    try:
        for table_name, definition in tables.items():
            create_table(cur, table_name, definition)

        conn.commit()
        print("Все таблицы успешно созданы!")

    except Exception as e:
        conn.rollback()
        print(f"Ошибка при создании таблиц: {e}")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    setup_tables()
