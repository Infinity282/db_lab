# -*- coding: utf-8 -*-
import psycopg2

DB_HOST = "localhost"
DB_NAME = "postgres_db"
DB_USER = "postgres_user"
DB_PASSWORD = "postgres_password"
DB_PORT = 5430

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
        # Universities
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Universities (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                address VARCHAR(255) NOT NULL,
                founded_date DATE NOT NULL
            );
        """)

        # Institutes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Institutes (
                id SERIAL PRIMARY KEY,
                university_id INT REFERENCES Universities(id),
                name VARCHAR(255) NOT NULL,
                dean VARCHAR(255)
            );
        """)

        # Departments
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Departments (
                id SERIAL PRIMARY KEY,
                institute_id INT REFERENCES Institutes(id),
                name VARCHAR(255) NOT NULL,
                head VARCHAR(255)
            );
        """)

        # Specialties (оставлено для совместимости)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Specialties (
                code VARCHAR(10) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT
            );
        """)

        # Student_Groups
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Student_Groups (
                id SERIAL PRIMARY KEY,
                department_id INT REFERENCES Departments(id),
                name VARCHAR(10) NOT NULL,
                course_year INT NOT NULL
            );
        """)

        # Course_of_lecture
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Course_of_lecture (
                id SERIAL PRIMARY KEY,
                department_id INT REFERENCES Departments(id),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                tech_requirements TEXT
            );
        """)

        # Students
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Students (
                id SERIAL PRIMARY KEY,
                student_group_id INT REFERENCES Student_Groups(id),
                name VARCHAR(255) NOT NULL,
                book_number VARCHAR(10) NOT NULL,
                enrollment_year INT NOT NULL,
                date_of_birth DATE NOT NULL,
                email VARCHAR(255) NOT NULL
            );
        """)

        # Lecture
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Lecture (
                id SERIAL PRIMARY KEY,
                course_id INT REFERENCES Course_of_lecture(id),
                topic VARCHAR(255) NOT NULL,
                lecture_date DATE NOT NULL,
                duration INT NOT NULL,
                tags VARCHAR(255)
            );
        """)

        # Schedule
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Schedule (
                id SERIAL PRIMARY KEY,
                student_group_id INT REFERENCES Student_Groups(id),
                lecture_id INT REFERENCES Lecture(id),
                room VARCHAR(10) NOT NULL,
                scheduled_date DATE NOT NULL,
                lecture_time TIME NOT NULL,
                planned_hours INT NOT NULL
            );
        """)

        # Attendance
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Attendance (
                id SERIAL PRIMARY KEY,
                schedule_id INT REFERENCES Schedule(id),
                student_id INT REFERENCES Students(id),
                attended BOOLEAN NOT NULL,
                attendance_date DATE
            );
        """)

        # Material_of_lecture
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Material_of_lecture (
                id SERIAL PRIMARY KEY,
                lecture_id INT REFERENCES Lecture(id),
                file_path VARCHAR(255) NOT NULL,
                uploaded_at TIMESTAMP NOT NULL
            );
        """)

        conn.commit()
        print("Таблицы успешно созданы в PostgreSQL")

    except Exception as e:
        conn.rollback()
        print(f"Ошибка при создании таблиц: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    setup_tables()