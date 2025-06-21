import psycopg2
import logging
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PostgresTool:
    def __init__(self, pg_host=DB_HOST):
        self.conn = None
        self.pg_host = pg_host

        self.connect()

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=self.pg_host,
                port=DB_PORT
            )
            logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"PostgreSQL connection error: {str(e)}")
            raise

    def get_course_lectures(self, course_id, semester, year):
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

    def get_students_with_lowest_attendance(self, schedule_ids: list, limit: int = 10) -> list:
        """
        Возвращает список студентов с информацией о посещаемости

        :param schedule_ids: Массив ID расписаний для анализа
        :param limit: Количество возвращаемых студентов
        :return: Список словарей в формате [{
            'student_id': int, 
            'missed_count': int,
            'total_lectures': int,
            'attendance_percent': float
        }, ...]
        """
        try:
            with self.conn.cursor() as cur:
                # Получаем студентов с низкой посещаемостью
                attendance_query = """
                SELECT student_id, SUM((attended)::int) AS missed_count, COUNT(*) AS total_lectures
                FROM attendance
                WHERE schedule_id = ANY(%s)
                GROUP BY student_id
                ORDER BY missed_count ASC
                LIMIT %s
                """
                cur.execute(attendance_query, (schedule_ids, limit))

                results = []
                for row in cur.fetchall():
                    student_id, missed_count, total_lectures = row
                    attendance_percent = round(
                        (missed_count / total_lectures) * 100, 2
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

                logger.info(
                    f"Найдено {len(results)} студентов с низкой посещаемостью"
                )
                return results

        except Exception as e:
            logger.error(
                f"Ошибка при анализе посещаемости: {str(e)}"
            )
            return []

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("PostgreSQL connection closed")

    def __del__(self):
        self.close()


def main():
    # Инициализация инструмента
    try:
        tool = PostgresTool()
        logger.info("Успешно подключились к PostgreSQL")
    except Exception as e:
        logger.error(f"Ошибка подключения: {str(e)}")
        return

    try:
        # Тест 3: Студенты с низкой посещаемостью
        print("\n=== Тест 3: Студенты с низкой посещаемостью ===")
        print(f"\nТоп 10 студентов с пропусками:")
        students = tool.get_students_with_lowest_attendance(
            schedule_ids=[1])

        if not students:
            print("Нет данных или ошибка запроса")

        for i, student_id in enumerate(students, 1):
            print(f"{i}. ID студента: {student_id}")

    except Exception as e:
        logger.error(f"Ошибка во время тестирования: {str(e)}")
    finally:
        tool.close()
        print("\nТестирование завершено, соединение закрыто")


if __name__ == "__main__":
    main()
