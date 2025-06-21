import logging
from neo4j import GraphDatabase
from env import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Neo4jTool:
    def __init__(self, connect_uri: str = NEO4J_URI):
        """Инициализация класса, но соединение пока не устанавливаем"""
        self.neo_driver = None
        self.connect_uri = connect_uri

    def _get_connection(self, ):
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

    def find_lecture_schedules(self, class_ids: list, start_time: str, end_time: str) -> list:
        """
        Поиск расписаний лекций для указанных Class ID в заданном временном интервале

        :param class_ids: Список ID классов (лекций)
        :param start_time: Начальное время в формате 'HH:MM:SS'
        :param end_time: Конечное время в формате 'HH:MM:SS'
        :return: Список расписаний или пустой список при ошибке
        """
        try:
            self.neo_driver = self._get_connection()

            cypher = """
                MATCH (c:Class)-[:FOR_CLASS]-(sch:Schedule)
                WHERE
                    c.id IN $class_ids
                    AND c.type = 'лекция'
                    AND sch.start_time >= $start_time
                    AND sch.end_time <= $end_time
                RETURN
                    sch.id AS id,
                    c.id AS class_id,
                    sch.room AS room,
                    sch.scheduled_date AS scheduled_date,
                    sch.start_time AS start_time,
                    sch.end_time AS end_time
                ORDER BY sch.scheduled_date, sch.start_time
            """

            with self.neo_driver.session() as session:
                result = session.run(
                    cypher,
                    class_ids=class_ids,
                    start_time=start_time,
                    end_time=end_time
                )
                schedules = [dict(record) for record in result]

            logger.info(f"Найдено {len(schedules)} расписаний лекций")
            return schedules

        except Exception as e:
            logger.error(f"Ошибка при поиске расписаний: {e}")
            return []
        finally:
            if self.neo_driver:
                self.neo_driver.close()
                self.neo_driver = None


def main():
    tool = Neo4jTool()

    # Пример использования
    schedules = tool.find_lecture_schedules(
        class_ids=[1, 2, 3],
        start_time="09:00:00",
        end_time="18:00:00"
    )

    for schedule in schedules:
        print(f"Лекция {schedule['class_id']} в аудитории {schedule['room']}")
        print(f"Дата: {schedule['scheduled_date']}")
        print(f"Время: {schedule['start_time']} - {schedule['end_time']}")
        print("-" * 50)


if __name__ == "__main__":
    main()
