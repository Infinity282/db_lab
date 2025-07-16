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

    # Методы для Лабораторной работы №1
    def get_course_lectures(self, course_id, semester, year):
        """
        Метод для Лабораторной работы №1: Получение лекций курса.
        :param course_id: ID курса.
        :param semester: Номер семестра.
        :param year: Год.
        :return: Список словарей с данными о лекциях.
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
        Метод для Лабораторной работы №1: Подсчет количества студентов на курсе.
        :param course_id: ID курса.
        :return: Количество студентов.
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
        Метод для Лабораторной работы №1: Получение студентов с минимальной посещаемостью.
        :param schedule_ids: Массив ID расписаний для анализа.
        :param students_ids: Массив ID студентов для анализа.
        :param limit: Количество возвращаемых студентов.
        :return: Список словарей в формате [{
            'student_id': int,
            'missed_count': int,
            'total_lectures': int,
            'attendance_percent': float
        }, ...]
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
                    missed_count = total_lectures - attendance_count
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
                logger.info(f"Найдено {len(results)} студентов с низкой посещаемостью")
                return results
        except Exception as e:
            logger.error(f"Ошибка при анализе посещаемости: {str(e)}")
            return []

    # Методы для Лабораторной работы №2
    def get_courses_lectures_lab2(self, start_date: date, end_date: date) -> list:
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

    def get_student_count_lab2(self, course_id: int) -> int:
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