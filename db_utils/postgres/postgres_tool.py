import psycopg2
import logging
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PostgresTool:
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

    def get_student_group_by_name(self, group_name: str):
        """
        Возвращает id группы студентов по названию группы

        :param group_name: название группы
        :return: id группы (число) или None если группа не найдена
        """
        try:
            with self.conn.cursor() as cur:
                query = """
                SELECT id, department_id, name, course_year FROM Student_Groups
                WHERE LOWER(name) LIKE LOWER(%s)
                """
                cur.execute(query, (group_name,))

                result = cur.fetchone()

                if result:
                    id, department_id, name, course_year = result
                    group_info = {
                        "id": id,
                        "department_id": department_id,
                        "name": name,
                        "course_year": course_year,
                    }
                    logger.info(
                        f"Найдена группа '{group_name}' с ID: {group_info['id']}")
                    return group_info
                else:
                    logger.warning(
                        f"Группа с названием '{group_name}' не найдена")
                    return None

        except Exception as e:
            logger.error(f"Ошибка при поиске группы по названию: {str(e)}")
            return None

    def get_students_with_lowest_attendance(self, schedule_ids: list, students_ids: list, limit: int = 10):
        """
        Возвращает список студентов с информацией о посещаемости

        :param schedule_ids: Массив ID расписаний для анализа
        :param students_ids: Массив ID студентов для анализа
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
                cur.execute(attendance_query,
                            (schedule_ids, students_ids, limit))

                results = []
                total_lectures = len(schedule_ids)
                for row in cur.fetchall():
                    student_id, attendance_count = row
                    missed_count = total_lectures - attendance_count
                    attendance_percent = round(
                        (attendance_count / total_lectures) * 100, 2
                    ) if len(schedule_ids) > 0 else 0

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

    def get_student_attendance(self, student_id: int, schedule_list: list[str]):
        """
        Возвращает посещение студента по ID расписаний и его ID

        :param student_id: ID студента
        :param schedule_list: массив ID расписаний
        :return: attendance_info: информация об оставшихся лекция и прослушанных
        """
        try:
            with self.conn.cursor() as cur:
                query = """
                    SELECT COUNT(*) AS attendance_count
                    FROM Attendance
                    WHERE student_id = %s
                    AND schedule_id = ANY(%s);
                """
                cur.execute(query, (student_id, schedule_list,))

                result = cur.fetchone()

                if result:
                    return result[0]
                else:
                    logger.warning(
                        f"Для расписаний '{schedule_list}' не найдены посещения")
                    return None

        except Exception as e:
            logger.error(f"Ошибка при поиске группы по названию: {str(e)}")
            return None

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
