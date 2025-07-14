import psycopg2
import logging
from datetime import date
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PostgresTool:
    """
    Класс для работы с базой данных PostgreSQL.
    Содержит оригинальные методы и методы для Лабораторных работ №1 и №2.
    """
    def __init__(self, host=DB_HOST, port=DB_PORT):
        self.conn = None
        self.host = host
        self.port = port
        self.connect()

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=self.host,
                port=self.port
            )
            logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"PostgreSQL connection error: {str(e)}")
            raise

    # Оригинальные функции
    def get_course_lectures(self, course_id, semester, year):
        """
        Получение лекций для конкретного курса.
        """
        try:
            with self.conn.cursor() as cur:
                query = """
                SELECT
                    c.id AS course_id,
                    c.name AS course_name,
                    l.id AS lecture_id,
                    l.topic,
                    l.date,
                    l.duration
                FROM courses c
                JOIN lectures l ON c.id = l.course_id
                WHERE
                    c.id = %s
                    AND c.semester = %s
                    AND c.year = %s
                """
                cur.execute(query, (course_id, semester, year))
                columns = [desc[0] for desc in cur.description]
                results = [dict(zip(columns, row)) for row in cur.fetchall()]
                return results
        except Exception as e:
            logger.error(f"Error fetching course lectures: {str(e)}")
            return []

    def get_student_count(self, course_id):
        """
        Подсчет количества студентов на курсе.
        """
        try:
            with self.conn.cursor() as cur:
                query = """
                SELECT COUNT(*)
                FROM enrollments
                WHERE course_id = %s
                """
                cur.execute(query, (course_id,))
                return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Error fetching student count: {str(e)}")
            return 0

    def get_students_with_lowest_attendance(self, schedule_ids: list, students_ids: list, limit: int = 10) -> list:
        """
        Возвращает список студентов с информацией о посещаемости.
        """
        try:
            with self.conn.cursor() as cur:
                attendance_query = """
                SELECT s.student_id, COALESCE((
                    SELECT COUNT(*)
                    FROM attendance a
                    WHERE a.student_id = s.student_id AND schedule_id = ANY(%s)
                ), 0) AS attendance_count
                FROM unnest(%s) AS s(student_id)
                ORDER BY attendance_count ASC, s.student_id ASC
                LIMIT %s
                """
                cur.execute(attendance_query, (schedule_ids, students_ids, limit))
                results = []
                total_lectures = len(schedule_ids)
                for row in cur.fetchall():
                    student_id, attendance_count = row
                    missed_count = total_lectures -attendance_count
                    attendance_percent = round(
                        (attendance_count / total_lectures) * 100, 2
                    ) if total_lectures > 0 else 0
                    student_data = {
                        'student_id': student_id,
                        'missed_count': missed_count,
                        'total_lectures': total_lectures,
                        'attendance_percent': attendance_percent
                    }
                    results.append(student_data)
                    logger.info(
                        f"Студент (ID: {student_id}): "
                        f"пропущено {missed_count} из {total_lectures} лекций "
                        f"({attendance_percent}% посещаемости)"
                    )
                logger.info(f"Най omissionдено {len(results)} студентов с низкой посещаемостью")
                return results
        except Exception as e:
            logger.error(f"Ошибка при анализе посещаемости: {str(e)}")
            return []

    # Новые функции для лабораторных работ
    def get_courses_lectures_lab2(self, start_date: date, end_date: date) -> list:
        """
        Метод для Лабораторной работы №2: Получение списка курсов и их лекций за указанный период.
        """
        try:
            with self.conn.cursor() as cur:
                query = """
                SELECT
                    c.id AS course_id,
                    c.name AS course_name,
                    cl.id AS lecture_id,
                    cl.name AS topic,
                    s.scheduled_date AS date,
                    s.start_time,
                    s.end_time,
                    cl.tech_requirements
                FROM course_of_classes c
                JOIN class cl ON c.id = cl.course_of_class_id
                JOIN schedule s ON cl.id = s.class_id
                WHERE
                    cl.type = 'лекция'
                    AND s.scheduled_date >= %s
                    AND s.scheduled_date <= %s
                ORDER BY c.id, s.scheduled_date, s.start_time
                """
                cur.execute(query, (start_date, end_date))
                columns = [desc[0] for desc in cur.description]
                results = [dict(zip(columns, row)) for row in cur.fetchall()]
                logger.info(f"Fetched {len(results)} courses and lectures for lab2")
                return results
        except Exception as e:
            logger.error(f"Error fetching courses and lectures for lab2: {str(e)}")
            return []

    def get_student_count_lab2(self, course_id: int) -> int:
        """
        Метод для Лабораторной работы №2: Подсчет количества студентов на курсе.
        """
        try:
            with self.conn.cursor() as cur:
                query = """
                SELECT COUNT(DISTINCT s.id)
                FROM students s
                JOIN student_groups g ON s.group_id = g.id
                JOIN schedule sch ON g.id = sch.group_id
                JOIN class cl ON sch.class_id = cl.id
                WHERE cl.course_of_class_id = %s
                """
                cur.execute(query, (course_id,))
                count = cur.fetchone()[0]
                logger.info(f"Student count for course {course_id} (lab2): {count}")
                return count
        except Exception as e:
            logger.error(f"Error fetching student count for lab2: {str(e)}")
            return 0

    def get_course_lectures_lab1(self, course_id: int, semester: int, year: int, term: str = None) -> list:
        """
        Метод для Лабораторной работы №1: Получение лекций курса с возможной фильтрацией по термину.
        """
        try:
            with self.conn.cursor() as cur:
                query = """
                SELECT
                    c.id AS course_id,
                    c.name AS course_name,
                    cl.id AS lecture_id,
                    cl.name AS topic,
                    s.scheduled_date AS date,
                    s.start_time AS duration
                FROM course_of_classes c
                JOIN class cl ON c.id = cl.course_of_class_id
                JOIN schedule s ON cl.id = s.class_id
                WHERE
                    c.id = %s
                    AND c.semester = %s
                    AND EXTRACT(YEAR FROM s.scheduled_date) = %s
                    AND cl.type = 'лекция'
                """
                params = [course_id, semester, year]
                if term:
                    query += " AND cl.name ILIKE %s"
                    params.append(f"%{term}%")
                
                cur.execute(query, tuple(params))
                columns = [desc[0] for desc in cur.description]
                results = [dict(zip(columns, row)) for row in cur.fetchall()]
                logger.info(f"Fetched {len(results)} lectures for course {course_id} (lab1)")
                return results
        except Exception as e:
            logger.error(f"Error fetching course lectures for lab1: {str(e)}")
            return []

    def get_students_with_lowest_attendance_lab1(self, schedule_ids: list, start_date: date, end_date: date, term: str = None, limit: int = 10) -> list:
        """
        Метод для Лабораторной работы №1: Получение студентов с минимальной посещаемостью.
        """
        try:
            with self.conn.cursor() as cur:
                query = """
                SELECT
                    s.id AS student_id,
                    s.name AS student_name,
                    s.email AS student_email,
                    s.enrollment_year,
                    s.date_of_birth,
                    SUM(CASE WHEN a.attended = FALSE THEN 1 ELSE 0 END) AS missed_count,
                    COUNT(a.schedule_id) AS total_lectures
                FROM students s
                JOIN attendance a ON s.id = a.student_id
                JOIN schedule sch ON a.schedule_id = sch.id
                JOIN class cl ON sch.class_id = cl.id
                WHERE
                    a.schedule_id = ANY(%s)
                    AND sch.scheduled_date >= %s
                    AND sch.scheduled_date <= %s
                """
                params = [schedule_ids, start_date, end_date]
                if term:
                    query += " AND cl.name ILIKE %s"
                    params.append(f"%{term}%")
                
                query += """
                GROUP BY s.id, s.name, s.email, s.enrollment_year, s.date_of_birth
                ORDER BY missed_count DESC
                LIMIT %s
                """
                params.append(limit)
                
                cur.execute(query, tuple(params))
                results = []
                for row in cur.fetchall():
                    student_id, student_name, student_email, enrollment_year, date_of_birth, missed_count, total_lectures = row
                    attendance_percent = round(
                        ((total_lectures - missed_count) / total_lectures) * 100, 2
                    ) if total_lectures > 0 else 0.0
                    student_data = {
                        'student_id': student_id,
                        'student_name': student_name,
                        'student_email': student_email,
                        'enrollment_year': enrollment_year,
                        'date_of_birth': str(date_of_birth),
                        'missed_count': missed_count,
                        'total_lectures': total_lectures,
                        'attendance_percent': attendance_percent
                    }
                    results.append(student_data)
                    logger.info(
                        f"Student (ID: {student_id}): "
                        f"missed {missed_count} of {total_lectures} lectures "
                        f"({attendance_percent}% attendance)"
                    )
                logger.info(f"Found {len(results)} students with low attendance for lab1")
                return results
        except Exception as e:
            logger.error(f"Error analyzing attendance for lab1: {str(e)}")
            return []

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("PostgreSQL connection closed")

    def __del__(self):
        self.close()

if __name__ == "__main__":
    from datetime import datetime
    tool = PostgresTool()
    try:
        # Пример использования оригинальной функции
        course_lectures = tool.get_course_lectures(course_id=1, semester=1, year=2023)
        print(f"Оригинальная функция: Получено {len(course_lectures)} лекций")

        # Пример использования новой функции для Лабораторной работы №2
        start_date = datetime.strptime("2023-09-01", "%Y-%m-%d").date()
        end_date = datetime.strptime("2023-12-31", "%Y-%m-%d").date()
        courses_lectures = tool.get_courses_lectures_lab2(start_date, end_date)
        print(f"Лабораторная №2: Получено {len(courses_lectures)} лекций")
    finally:
        tool.close()