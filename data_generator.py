from datetime import timedelta
import random
from datetime import datetime
import psycopg2
from consts import ATTENDANCE, COURSE_OF_LECTURE, DEPARTMENTS, GROUP_COURSES, INSTITUTES, LECTURE, MATERIAL_OF_LECTURE, SCHEDULE, SPECIALTIES, STUDENT_GROUPS, UNIVERSITIES
from setup_postgre_tables import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

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
            inst
        )

def insert_departments(cur):
    """Добавление кафедр"""
    print("Добавление кафедр")
    for dep in DEPARTMENTS:
        cur.execute(
            "INSERT INTO Departments (name, institute_id) VALUES (%s, %s)",
            dep
        )

def insert_specialties(cur):
    """Добавление специальностей"""
    print("Добавление специальностей")
    for special in SPECIALTIES:
        cur.execute(
            "INSERT INTO Specialties (code, name, description) VALUES (%s, %s, %s)",
            special
        )

def insert_student_groups(cur):
    """Добавление студенческих групп"""
    print("Добавление студенческих групп")
    for group in STUDENT_GROUPS:
        cur.execute(
            """
            INSERT INTO Student_Groups (name, department_id, specialty_id, course_year)
            VALUES (%s, %s, %s, %s)
            """, group
        )

def insert_course_of_lecture(cur):
    """Добавление курсов лекций"""
    print("Добавление курсов лекций")
    for course in COURSE_OF_LECTURE:
        cur.execute(
            """
            INSERT INTO Course_of_lecture (name, department_id, specialty_id)
            VALUES (%s, %s, %s)
            """, course
        )

def insert_group_courses(cur):
    """Добавление групп и курсов"""
    print("Добавление групп и курсов")
    for course in GROUP_COURSES:
        cur.execute(
            """
            INSERT INTO Group_Courses (group_id, course_id)
            VALUES (%s, %s)
            """, course
        )

def insert_and_generate_students(cur):
    """Добавление и генерация студентов"""
    print("Добавление и генерация студентов")
    cur.execute("SELECT group_id, name FROM Student_Groups;")
    groups = cur.fetchall()
    groups = groups[:32]

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
            group_letter = group_name[0:1].upper()
            book_number = (
                f"{str(enrollment_year)[-2:]}"
                f"{group_letter}"
                f"{random.randint(1000, 9999):04d}"
            )
            cur.execute("""
                INSERT INTO Students (group_id, name, enrollment_year, date_of_birth, email, book_number)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (group_id, name, enrollment_year, date_of_birth, email, book_number)
            )

def insert_and_generate_lectures(cur):
    """Добавление и генерация лекций"""
    print("Добавление и генерация лекций")
    lecture_topics = [
        "Введение в курс", "Основные понятия", "Теоретические основы",
        "Методология", "История развития", "Современные подходы",
        "Ключевые концепции", "Продвинутые техники"
    ]
    statuses = ["Active", "Cancelled", "Planned"]

    cur.execute("SELECT id FROM Course_of_lecture;")
    courses = cur.fetchall()

    for course in courses:
        course_id = course[0]
        for i in range(8):
            topic = f"Лекция {i+1}: {random.choice(lecture_topics)}"
            status = random.choice(statuses)
            cur.execute("""
                INSERT INTO Lecture (name, course_of_lecture_id, status)
                VALUES (%s, %s, %s)
                """, (topic, course_id, status))

def insert_material_of_lecture(cur):
    """Добавление материалов лекций"""
    print("Добавление материалов лекций")
    cur.execute("SELECT id FROM Lecture;")
    lecture_ids = cur.fetchall()
    material_types = ['PDF', 'PPTX', 'DOCX', 'MP4', 'MP3', 'ZIP', 'CODE']
    
    for lecture_id in lecture_ids:
        material_type = random.choice(material_types)
        uploaded_at = datetime.now() - timedelta(days=random.randint(0, 30))
        name = f"Материал для лекции {lecture_id[0]}"
        cur.execute("""
            INSERT INTO Material_of_lecture (name, lecture_id, type, uploaded_at)
            VALUES (%s, %s, %s, %s)
            """, (name, lecture_id[0], material_type, uploaded_at))

def insert_schedule(cur):
    """Добавление расписания"""
    print("Добавление расписания")
    for schedule in SCHEDULE:
        cur.execute(
            "INSERT INTO Schedule (group_id, lecture_id, room, scheduled_date, start_time) VALUES (%s, %s, %s, %s, %s)",
            schedule
        )

def insert_attendance(cur):
    """Добавление посещаемости"""
    print("Добавление посещаемости")
    for attendance in ATTENDANCE:
        cur.execute(
            "INSERT INTO Attendance (schedule_id, student_id, attended, absence_reason) VALUES (%s, %s, %s, %s)",
            attendance
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
        # Вызываем функции по порядку с учетом зависимостей
        insert_universities(cur)
        insert_institutes(cur)
        insert_departments(cur)
        insert_specialties(cur)
        insert_student_groups(cur)
        insert_course_of_lecture(cur)
        insert_and_generate_students(cur)
        insert_group_courses(cur)
        insert_and_generate_lectures(cur)
        insert_material_of_lecture(cur)
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