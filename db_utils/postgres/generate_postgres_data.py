# -*- coding: utf-8 -*-
from datetime import timedelta
import random
from datetime import datetime
import psycopg2
from psycopg2.extras import Json
from tables_data import (
    ATTENDANCE,
    COURSES,
    DEPARTMENTS,
    GROUP_COURSES,
    INSTITUTES,
    SCHEDULE,
    SESSION_TYPES,
    SPECIALTIES,
    STUDENT_GROUPS,
    TEST_STUDENTS,
    TEST_SCHEDULE,
    TEST_ATTENDANCE,
    UNIVERSITIES
)
from create_postgres_tables import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

USE_TEST_DATA = True

def insert_universities(cur):
    """Добавление университетов"""
    print("Добавление университетов")
    for uni in UNIVERSITIES:
        cur.execute(
            "INSERT INTO Universities (name, address, founded_date) VALUES (%s, %s, %s)",
            uni
        )

def insert_institutes(cur):
    """Добавление институтов"""
    print("Добавление институтов")
    for inst in INSTITUTES:
        cur.execute(
            "INSERT INTO Institutes (name, university_id) VALUES (%s, %s)",
            (inst[0], inst[1])
        )

def insert_departments(cur):
    """Добавление кафедр"""
    print("Добавление кафедр")
    for dep in DEPARTMENTS:
        cur.execute(
            "INSERT INTO Departments (name, institute_id) VALUES (%s, %s)",
            (dep[0], dep[1])
        )

def insert_specialties(cur):
    """Добавление специальностей"""
    print("Добавление специальностей")
    for special in SPECIALTIES:
        cur.execute(
            "INSERT INTO Specialties (code, name) VALUES (%s, %s)",
            (special[0], special[1])
        )

def insert_student_groups(cur):
    """Добавление студенческих групп"""
    print("Добавление студенческих групп")
    for group in STUDENT_GROUPS:
        cur.execute(
            """
            INSERT INTO Student_Groups (department_id, specialty_id, name, course_year)
            VALUES (%s, %s, %s, %s)
            """, (group[0], group[1], group[2], group[3])
        )

def insert_course_of_classes(cur):
    """Добавление курсов занятий"""
    print("Добавление курсов занятий")
    for course in COURSES:
        cur.execute(
            """
            INSERT INTO Course_of_classes (name, department_id, specialty_id, description, tech_requirements)
            VALUES (%s, %s, %s, %s, %s)
            """, (course[0], course[1], course[2], course[3], course[4])
        )

def insert_and_generate_students(cur):
    """Добавление и генерация студентов"""
    print("Добавление и генерация студентов")
    if USE_TEST_DATA:
        for student in TEST_STUDENTS:
            cur.execute(
                """
                INSERT INTO Students (group_id, name, book_number, enrollment_year, date_of_birth, email)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, student
            )
    else:
        cur.execute("SELECT id, name FROM Student_Groups;")
        groups = cur.fetchall()
        for group_id, group_name in groups:
            for i in range(20):
                name = f"stud{random.randint(10000, 99999)}"
                email = f"{name}@university.example"
                current_year = datetime.now().year
                enrollment_year = random.randint(current_year - 4, current_year)
                age_at_enrollment = random.randint(17, 22)
                birth_year = enrollment_year - age_at_enrollment
                month = random.randint(1, 12)
                day = random.randint(1, 28)
                date_of_birth = datetime(birth_year, month, day).date()
                book_number = f"{str(enrollment_year)[-2:]}{group_name[0:1].upper()}{random.randint(1000, 9999):04d}"
                cur.execute(
                    """
                    INSERT INTO Students (group_id, name, book_number, enrollment_year, date_of_birth, email)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """, (group_id, name, book_number, enrollment_year, date_of_birth, email)
                )

def insert_classes(cur):
    """Добавление занятий"""
    print("Добавление занятий")
    for session_type in SESSION_TYPES:
        cur.execute(
            """
            INSERT INTO Class (course_of_class_id, name, type)
            VALUES (%s, %s, %s)
            """, session_type
        )

def insert_class_materials(cur):
    """Добавление материалов занятий"""
    print("Добавление материалов занятий")
    for material in GROUP_COURSES:
        cur.execute(
            """
            INSERT INTO Class_Materials (class_id, content)
            VALUES (%s, %s)
            """, (material[0], Json({"file_path": material[1], "uploaded_at": material[2]}))
        )

def insert_schedule(cur):
    """Добавление расписания"""
    print("Добавление расписания")
    schedule_data = TEST_SCHEDULE if USE_TEST_DATA else SCHEDULE
    for schedule in schedule_data:
        cur.execute(
            """
            INSERT INTO Schedule (group_id, course_of_class_id, room, scheduled_date, start_time, end_time)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, schedule
        )

def insert_attendance(cur):
    """Добавление посещаемости"""
    print("Добавление посещаемости")
    attendance_data = TEST_ATTENDANCE if USE_TEST_DATA else ATTENDANCE
    for attendance in attendance_data:
        cur.execute(
            """
            INSERT INTO Attendance (schedule_id, student_id, attended, absence_reason)
            VALUES (%s, %s, %s, %s)
            """, attendance
        )

def seed_database():
    """Основная функция для заполнения БД"""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()

    try:
        insert_universities(cur)
        insert_institutes(cur)
        insert_departments(cur)
        insert_specialties(cur)
        insert_student_groups(cur)
        insert_course_of_classes(cur)
        insert_and_generate_students(cur)
        insert_classes(cur)
        insert_class_materials(cur)
        insert_schedule(cur)
        insert_attendance(cur)

        conn.commit()
        print("Данные успешно добавлены в БД Postgres")

    except Exception as e:
        conn.rollback()
        print(f"Ошибка при добавлении данных: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed_database()