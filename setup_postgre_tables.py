import psycopg2
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


def setup_tables():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()

    try:
        # Таблица Universities (университеты)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Universities (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                address VARCHAR(255) NOT NULL,
                founded_date DATE NOT NULL
            )
        """)

        # Таблица Institutes (институты)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Institutes (
                id SERIAL PRIMARY KEY,
                university_id INTEGER REFERENCES Universities(id),
                name VARCHAR(255) NOT NULL
            )
        """)

        # Таблица Departments (кафедры)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Departments (
                id SERIAL PRIMARY KEY,
                institute_id INTEGER REFERENCES Institutes(id),
                name VARCHAR(255) NOT NULL
            )
        """)

        # Таблица Student_Groups (студент, которые принадлежат кафедрам)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Student_Groups (
                id SERIAL PRIMARY KEY,
                department_id INTEGER REFERENCES Departments(id),
                name VARCHAR(50) NOT NULL,
                course_year INTEGER
            )
        """)

        # Таблица Students
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Students (
                id SERIAL PRIMARY KEY,
                group_id INTEGER REFERENCES Student_Groups(id),
                name VARCHAR(255) NOT NULL,
                enrollment_year INTEGER,
                date_of_birth DATE,
                email VARCHAR(255),
                book_number VARCHAR(20)
            )
        """)

        # Таблица Specialties
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Specialties (
                id SERIAL PRIMARY KEY,
                code VARCHAR(20) NOT NULL,
                name VARCHAR(255) NOT NULL
            )
        """)

        # Таблица Course_of_classes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Course_of_classes (
                id SERIAL PRIMARY KEY,
                department_id INTEGER REFERENCES Departments(id),
                specialty_id INTEGER REFERENCES Specialties(id),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                tech_requirements TEXT
            )
        """)

        # Таблица Class
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Class (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                course_of_class_id INTEGER REFERENCES Course_of_classes(id),
                type VARCHAR(50) NOT NULL
            )
         """)

        # Таблица Class_Materials
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Class_Materials (
                id SERIAL PRIMARY KEY,
                class_id INTEGER REFERENCES Class(id),
                content TEXT
            )
        """)

        # Таблица Schedule
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Schedule (
                id SERIAL PRIMARY KEY,
                group_id INTEGER REFERENCES Student_Groups(id),
                course_of_class_id INTEGER REFERENCES Course_of_classes(id),
                room VARCHAR(50),
                scheduled_date DATE,
                start_time TIME,
                end_time TIME
            )
        """)

        # Таблица Attendance
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Attendance (
                id SERIAL PRIMARY KEY,
                schedule_id INTEGER REFERENCES Schedule(id),
                student_id INTEGER REFERENCES Students(id),
                attended BOOLEAN NOT NULL,
                absence_reason TEXT
            )
        """)

        conn.commit()
        print("Таблицы успешно созданы!")

    except Exception as e:
        conn.rollback()
        print(f"Ошибка: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    setup_tables()
