import logging
from neo4j import GraphDatabase
from env import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Neo4jTool:
    def __init__(self, host: str = NEO4J_URI):
        """Инициализация класса, но соединение пока не устанавливаем"""
        self.neo_driver = None
        self.connect_uri = host

    def _get_connection(self):
        """Создает и возвращает новое соединение с Neo4j"""
        try:
            driver = GraphDatabase.driver(
                self.connect_uri,
                auth=(NEO4J_USER, NEO4J_PASSWORD))

            # Проверяем соединение
            with driver.session() as session:
                session.run("RETURN 1")

            return driver
        except Exception as e:
            logger.error(f"Ошибка подключения к Neo4j: {e}")
            raise

    def find_lecture_schedules(self, class_ids: list, start_date: str, end_date: str) -> list:
        """
        Поиск расписаний лекций для указанных Class ID в заданном интервале дат

        :param class_ids: Список ID классов (лекций)
        :param start_date: Начальная дата в формате 'YYYY-MM-DD'
        :param end_date: Конечная дата в формате 'YYYY-MM-DD'
        :return: Список расписаний или пустой список при ошибке
        """
        try:
            # Валидация формата дат
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')

            self.neo_driver = self._get_connection()

            cypher = """
                MATCH (g:StudentGroup)-[:HAS_SCHEDULE]->(sch:Schedule)-[:FOR_CLASS]->(c:Class)
                WHERE
                    c.postgres_id IN $class_ids
                    AND c.type = 'лекция'
                    AND date(sch.scheduled_date) >= date($start_date)
                    AND date(sch.scheduled_date) <= date($end_date)
                RETURN
                    sch.postgres_id AS id,
                    c.postgres_id AS class_id,
                    sch.room AS room,
                    g.postgres_id AS group_id,
                    sch.scheduled_date AS scheduled_date,
                    sch.start_time AS start_time,
                    sch.end_time AS end_time
                ORDER BY sch.scheduled_date, sch.start_time
            """

            with self.neo_driver.session() as session:
                result = session.run(
                    cypher,
                    class_ids=class_ids,
                    start_date=start_date,
                    end_date=end_date
                )
                schedules = [dict(record) for record in result]

            logger.info(f"Найдено {len(schedules)} расписаний лекций")
            return schedules

        except ValueError as ve:
            logger.error(f"Некорректный формат даты: {ve}")
            return []
        except Exception as e:
            logger.error(f"Ошибка при поиске расписаний: {e}")
            return []
        finally:
            if self.neo_driver:
                self.neo_driver.close()
                self.neo_driver = None

    def find_students_and_lectures(self, start_date: str, end_date: str) -> list:
        """
        Поиск лекций, кол-ва студентов и курса лекций по заданному промежутку времени

        :param start_date: Начальная дата в формате 'YYYY-MM-DD'
        :param end_date: Конечная дата в формате 'YYYY-MM-DD'
        :return: Список колв-ва студентов, курса и лекций
        """
        try:
            self.neo_driver = self._get_connection()

            cypher = """
                MATCH (c:Class)-[:BELONGS_TO]->(course:Course)
                WHERE c.type = "лекция"

                MATCH (c)<-[:FOR_CLASS]-(sch:Schedule)
                WHERE date(sch.scheduled_date) >= date($start_date) 
                AND date(sch.scheduled_date) <= date($end_date)

                MATCH (g:StudentGroup)-[:HAS_SCHEDULE]->(sch)

                WITH 
                course,
                c,
                COLLECT(DISTINCT g.postgres_id) as group_ids

                RETURN
                course.department_id,
                course.specialty_id,
                course.description,
                course.name,
                c.name,
                c.tags,
                c.type,
                c.tech_requirements,
                group_ids
            """

            with self.neo_driver.session() as session:
                result = session.run(
                    cypher,
                    start_date=start_date,
                    end_date=end_date
                )
                response = [dict(record) for record in result]

            logger.info(f"Найдено {len(response)} записей")
            return response

        except ValueError as ve:
            logger.error(f"Некорректный формат даты: {ve}")
            return []
        except Exception as e:
            logger.error(f"Ошибка при поиске расписаний: {e}")
            return []
        finally:
            if self.neo_driver:
                self.neo_driver.close()
                self.neo_driver = None

    def find_special_lectures_and_course_of_lectures(self, group_id: int, special_tag: str) -> list:
        """
        Поиск лекций, информации о курсе по специальному тэгу дисциплины и id группы
        """
        try:
            self.neo_driver = self._get_connection()

            cypher = """
                MATCH (g:StudentGroup {postgres_id: $group_id})-[:HAS_SCHEDULE]->(sch:Schedule)
                MATCH (sch)-[:FOR_CLASS]->(c:Class)-[:BELONGS_TO]->(course:Course)
                WHERE c.type = 'лекция'
                AND $special_tag IN c.tags
                RETURN
                course.postgres_id as course_id,
                course.specialty_id,
                course.name,
                course.description,
                COLLECT(sch.postgres_id) as schedule_ids
            """

            with self.neo_driver.session() as session:
                result = session.run(
                    cypher,
                    group_id=group_id,
                    special_tag=special_tag
                )
                response = [dict(record) for record in result]

            logger.info(f"Найдено {len(response)} записей")
            return response

        except Exception as e:
            logger.error(f"Ошибка при поиске расписаний: {e}")
            return []
        finally:
            if self.neo_driver:
                self.neo_driver.close()
                self.neo_driver = None


def main():
    tool = Neo4jTool()

    # Пример использования поиска по диапазону дат
    schedules = tool.find_lecture_schedules(
        class_ids=[1, 2, 3, 4, 5, 6],
        start_date="2023-09-01",
        end_date="2023-12-31",
    )

    for schedule in schedules:
        print(f"Лекция {schedule['class_id']} в аудитории {schedule['room']}")
        print(f"Дата: {schedule['scheduled_date']}")
        print(f"Время: {schedule['start_time']} - {schedule['end_time']}")
        print("-" * 50)


if __name__ == "__main__":
    main()
