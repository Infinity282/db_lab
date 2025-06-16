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
        # Таблица Universities
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Universities (
                university_id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                address TEXT,
                founded_date DATE
            )
        """)

        # Таблица Institutes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Institutes (
                institute_id SERIAL PRIMARY KEY,
                university_id INTEGER REFERENCES Universities(university_id),
                name VARCHAR(255) NOT NULL
            )
        """)

        # Таблица Departments
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Departments (
                department_id SERIAL PRIMARY KEY,
                institute_id INTEGER REFERENCES Institutes(institute_id),
                name VARCHAR(255) NOT NULL
            )
        """)

        # Таблица Specialties
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Specialties (
                specialty_id SERIAL PRIMARY KEY,
                code VARCHAR(20) NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT
            )
        """)

        # Таблица Course_of_lecture (из скрипта Егора)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Course_of_lecture (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                department_id INTEGER REFERENCES Departments(department_id),
                specialty_id INTEGER REFERENCES Specialties(specialty_id)
            )
        """)

        # Таблица Student_Groups
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Student_Groups (
                group_id SERIAL PRIMARY KEY,
                department_id INTEGER REFERENCES Departments(department_id),
                specialty_id INTEGER REFERENCES Specialties(specialty_id),
                name VARCHAR(50) NOT NULL,
                course_year INTEGER
            )
        """)

        # Таблица Group_Courses (обновлена для ссылки на Course_of_lecture)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Group_Courses (
                group_id INTEGER REFERENCES Student_Groups(group_id),
                course_id INTEGER REFERENCES Course_of_lecture(id),
                PRIMARY KEY (group_id, course_id)
            )
        """)

        # Таблица Session_Types
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Session_Types (
                session_type_id SERIAL PRIMARY KEY,
                name VARCHAR(50) NOT NULL
            )
        """)

        # Таблица Lecture (из скрипта Егора, без tags, с добавленным status)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Lecture (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                course_of_lecture_id INTEGER REFERENCES Course_of_lecture(id),
                status VARCHAR(50)
            )
        """)

        # Таблица Schedule (обновлена для ссылки на Lecture)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Schedule (
                schedule_id SERIAL PRIMARY KEY,
                group_id INTEGER REFERENCES Student_Groups(group_id),
                lecture_id INTEGER REFERENCES Lecture(id),
                room VARCHAR(50),
                scheduled_date DATE,
                start_time TIME
            )
        """)

        # Таблица Students
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Students (
                student_id SERIAL PRIMARY KEY,
                group_id INTEGER REFERENCES Student_Groups(group_id),
                name VARCHAR(255) NOT NULL,
                enrollment_year INTEGER,
                date_of_birth DATE,
                email VARCHAR(255),
                book_number VARCHAR(20)
            )
        """)

        # Таблица Attendance
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Attendance (
                attendance_id SERIAL PRIMARY KEY,
                schedule_id INTEGER REFERENCES Schedule(schedule_id),
                student_id INTEGER REFERENCES Students(student_id),
                attended BOOLEAN NOT NULL,
                absence_reason TEXT
            )
        """)

        # Таблица Material_of_lecture (из скрипта Егора, с добавленными полями)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Material_of_lecture (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                lecture_id INTEGER REFERENCES Lecture(id),
                type VARCHAR(50),
                uploaded_at TIMESTAMP
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