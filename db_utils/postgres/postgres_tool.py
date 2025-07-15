import psycopg2
import logging
from datetime import date
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PostgresTool:
    """
    Класс для работы с базой данных PostgreSQL.
    Содержит методы для подключения и выполнения запросов, необходимых для Лабораторных работ №1 и №2.
    """
    def __init__(self, host=DB_HOST, port=DB_PORT):
        """
        Инициализация объекта PostgresTool.
        :param host: Адрес хоста базы данных (по умолчанию из env.py).
        :param port: Порт базы данных (по умолчанию из env.py).
        """
        self.conn = None
        self.host = host
        self.port = port
        self.connect()

    def connect(self):
        """
        Устанавливает соединение с базой данных PostgreSQL с использованием параметров из env.py.
        """
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

    def get_courses_lectures(self, start_date: date, end_date: date) -> list:
        """
        Метод для Лабораторной работы №2: Получение списка курсов и их лекций за указанный период.
        :param start_date: Начальная дата периода (тип date).
        :param end_date: Конечная дата периода (тип date).
        :return: Список словарей с информацией о курсах и лекциях.
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
                logger.info(f"Fetched {len(results)} courses and lectures")
                return results
        except Exception as e:
            logger.error(f"Error fetching courses and lectures: {str(e)}")
            return []

    def get_student_count(self, course_id: int) -> int:
        """
        Метод для Лабораторной работы №2: Подсчет количества студентов на курсе.
        :param course_id: ID курса (целое число).
        :return: Количество студентов (целое число).
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
                logger.info(f"Student count for course {course_id}: {count}")
                return count
        except Exception as e:
            logger.error(f"Error fetching student count: {str(e)}")
            return 0

    def get_course_lectures(self, course_id: int, semester: int, year: int, term: str = None) -> list:
        """
        Метод для Лабораторной работы №1: Получение лекций курса с возможной фильтрацией по термину.
        :param course_id: ID курса (целое число).
        :param semester: Номер семестра (целое число).
        :param year: Год (целое число).
        :param term: Строка для фильтрации тем лекций (опционально).
        :return: Список словарей с данными о лекциях.
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
                logger.info(f"Fetched {len(results)} lectures for course {course_id}")
                return results
        except Exception as e:
            logger.error(f"Error fetching course lectures: {str(e)}")
            return []

    def get_students_with_lowest_attendance(self, schedule_ids: list, start_date: date, end_date: date, term: str = None, limit: int = 10) -> list:
        """
        Метод для Лабораторной работы №1: Получение студентов с минимальной посещаемостью.
        :param schedule_ids: Список ID расписаний (список целых чисел).
        :param start_date: Начальная дата периода (тип date).
        :param end_date: Конечная дата периода (тип date).
        :param term: Строка для фильтрации по теме лекций (опционально).
        :param limit: Максимальное количество студентов в результате (по умолчанию 10).
        :return: Список словарей с данными о студентах и их посещаемости.
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
                logger.info(f"Found {len(results)} students with low attendance")
                return results
        except Exception as e:
            logger.error(f"Error analyzing attendance: {str(e)}")
            return []

    def close(self):
        """
        Закрытие соединения с базой данных.
        """
        if self.conn:
            self.conn.close()
            logger.info("PostgreSQL connection closed")

    def __del__(self):
        """
        Деструктор: автоматически закрывает соединение при удалении объекта.
        """
        self.close()