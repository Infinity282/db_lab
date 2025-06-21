import psycopg2
from neo4j import GraphDatabase
from contextlib import closing
from datetime import datetime
import logging
from env import (DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT,
                 DB_USER, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Neo4jSynchronizer:
    def __init__(self) -> None:
        self.pg_conn = None
        self.neo_driver = None
        self.stats = {
            'courses': 0,
            'groups': 0,
            'group_courses': 0,
            'students': 0,
            'start_time': None
        }

        self.connect_postgres()
        self.connect_neo4j()

    def connect_postgres(self) -> bool:
        """Установка соединения с PostgreSQL"""
        try:
            self.pg_conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            logger.info("Успешное подключение к PostgreSQL")
            return True
        except psycopg2.Error as e:
            logger.error(f"Ошибка подключения к PostgreSQL: {e}")
            return False

    def connect_neo4j(self) -> bool:
        """Установка соединения с Neo4j"""
        try:
            self.neo_driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            with self.neo_driver.session() as session:
                session.run("RETURN 1")
            logger.info("Успешное подключение к Neo4j")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к Neo4j: {e}")
            return False

    def close_connections(self) -> None:
        """Закрытие всех соединений"""
        if self.pg_conn:
            self.pg_conn.close()
            logger.info("Соединение с PostgreSQL закрыто")
        if self.neo_driver:
            self.neo_driver.close()
            logger.info("Соединение с Neo4j закрыто")

    def fetch_data(self, query: str, params=None) -> list:
        """Извлечение данных из PostgreSQL"""
        try:
            with closing(self.pg_conn.cursor()) as cursor:
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except psycopg2.Error as e:
            logger.error(f"Ошибка при выполнении запроса: {e}")
            return []

    def sync_courses(self) -> bool:
        """Синхронизация курсов в Neo4j"""
        logger.info("Синхронизация курсов...")
        cypher = """
        UNWIND $rows AS row
        MERGE (c:Course {postgres_id: row.id})
        SET c.name = row.name,
            c.description = row.description,
            c.department_id = row.department_id,
            c.specialty_id = row.specialty_id,
            c.tech_requirements = row.tech_requirements
        """
        rows = self.fetch_data("""
            SELECT
                id,
                department_id,
                specialty_id,
                name,
                description,
                tech_requirements
            FROM Course_of_classes
        """)
        self.stats['courses'] = len(rows)

        if not rows:
            logger.warning("Не найдено данных о курсах")
            return False

        try:
            with self.neo_driver.session() as session:
                result = session.run(cypher, rows=rows)
                summary = result.consume()
                logger.debug(
                    f"Курсов создано/обновлено: {summary.counters.nodes_created}")
            logger.info(f"Синхронизировано {len(rows)} курсов")
            return True
        except Exception as e:
            logger.error(f"Ошибка синхронизации курсов: {e}")
            return False

    def sync_classes(self) -> bool:
        """Синхронизация учебных занятий в Neo4j"""
        logger.info("Синхронизация учебных занятий...")
        cypher = """
        UNWIND $rows AS row
        MERGE (cls:Class {postgres_id: row.id})
        SET cls.name = row.name,
            cls.tags = row.tags,
            cls.type = row.type
            
        // Связь с курсом
        WITH cls, row
        MATCH (course:Course {postgres_id: row.course_of_class_id})
        MERGE (cls)-[:BELONGS_TO]->(course)
        """
        rows = self.fetch_data("""
            SELECT 
                id, 
                name, 
                course_of_class_id, 
                tags, 
                type 
            FROM Class
        """)
        self.stats['classes'] = len(rows)

        if not rows:
            logger.warning("Не найдено данных о занятиях")
            return False

        try:
            with self.neo_driver.session() as session:
                result = session.run(cypher, rows=rows)
                summary = result.consume()
                logger.debug(
                    f"Занятий создано: {summary.counters.nodes_created}, "
                    f"Связей с курсами создано: {summary.counters.relationships_created}"
                )
            logger.info(f"Синхронизировано {len(rows)} занятий")
            return True
        except Exception as e:
            logger.error(f"Ошибка синхронизации занятий: {e}")
            return False

    def sync_student_groups(self) -> bool:
        """Синхронизация учебных групп"""
        logger.info("Синхронизация учебных групп...")
        cypher = """
        UNWIND $rows AS row
        MERGE (g:StudentGroup {postgres_id: row.id})
        SET g.name = row.name,
            g.course_year = row.course_year,
            g.department_id = row.department_id
        """
        rows = self.fetch_data("""
            SELECT 
                id, 
                name, 
                course_year, 
                department_id 
            FROM Student_Groups
        """)
        self.stats['groups'] = len(rows)

        if not rows:
            logger.warning("Не найдено данных о группах")
            return False

        try:
            with self.neo_driver.session() as session:
                result = session.run(cypher, rows=rows)
                summary = result.consume()
                logger.debug(
                    f"Групп создано/обновлено: {summary.counters.nodes_created}")
            logger.info(f"Синхронизировано {len(rows)} групп")
            return True
        except Exception as e:
            logger.error(f"Ошибка синхронизации групп: {e}")
            return False

    def sync_students(self) -> bool:
        """Синхронизация студентов"""
        logger.info("Синхронизация студентов...")
        cypher = """
        UNWIND $rows AS row
        MATCH (g:StudentGroup {postgres_id: row.group_id})
        MERGE (s:Student {postgres_id: row.id})
        SET s.name = row.name,
            s.enrollment_year = row.enrollment_year,
            s.date_of_birth = row.date_of_birth,
            s.email = row.email,
            s.book_number = row.book_number
        MERGE (s)-[:MEMBER_OF]->(g)
        """
        rows = self.fetch_data("""
            SELECT 
                id,
                group_id,
                name, 
                enrollment_year, 
                date_of_birth, 
                email, 
                book_number 
            FROM Students
        """)
        self.stats['students'] = len(rows)

        if not rows:
            logger.warning("Не найдено данных о студентах")
            return False

        try:
            with self.neo_driver.session() as session:
                result = session.run(cypher, rows=rows)
                summary = result.consume()
                logger.debug(
                    f"Студентов создано: {summary.counters.nodes_created}, "
                    f"Связей с группами создано: {summary.counters.relationships_created}"
                )
            logger.info(f"Синхронизировано {len(rows)} студентов")
            return True
        except Exception as e:
            logger.error(f"Ошибка синхронизации студентов: {e}")
            return False

    def sync_schedules(self) -> bool:
        """Синхронизация расписания занятий"""
        logger.info("Синхронизация расписания...")
        cypher = """
        UNWIND $rows AS row
        // Создаем узел расписания
        MERGE (sch:Schedule {postgres_id: row.id})
        SET sch.room = row.room,
            sch.scheduled_date = row.scheduled_date,
            sch.start_time = row.start_time,
            sch.end_time = row.end_time
            
        // Связь с группой
        WITH sch, row
        MATCH (g:StudentGroup {postgres_id: row.group_id})
        MERGE (g)-[:HAS_SCHEDULE]->(sch)
        
        // Связь с занятием
        WITH sch, row
        MATCH (c:Class {postgres_id: row.class_id})
        MERGE (sch)-[:FOR_CLASS]->(c)
        """
        rows = self.fetch_data("""
            SELECT 
                id, 
                group_id, 
                class_id, 
                room, 
                scheduled_date, 
                start_time, 
                end_time 
            FROM Schedule
        """)
        self.stats['schedules'] = len(rows)

        if not rows:
            logger.warning("Не найдено данных о расписании")
            return False

        try:
            with self.neo_driver.session() as session:
                result = session.run(cypher, rows=rows)
                summary = result.consume()
                logger.debug(
                    f"Расписаний создано: {summary.counters.nodes_created}, "
                    f"Связей создано: {summary.counters.relationships_created}"
                )
            logger.info(f"Синхронизировано {len(rows)} записей расписания")
            return True
        except Exception as e:
            logger.error(f"Ошибка синхронизации расписания: {e}")
            return False

    def run_sync(self) -> bool:
        """Основной метод выполнения синхронизации"""
        self.stats['start_time'] = datetime.now()
        logger.info("Начало синхронизации данных в Neo4j")

        if not all([self.pg_conn, self.neo_driver]):
            logger.error("Отсутствуют необходимые соединения")
            return False

        try:
            success = all([
                self.sync_courses(),
                self.sync_classes(),
                self.sync_student_groups(),
                self.sync_students(),
                self.sync_schedules()
            ])

            duration = (datetime.now() -
                        self.stats['start_time']).total_seconds()
            if success:
                logger.info(
                    f"Синхронизация успешно завершена за {duration:.2f} секунд")
                logger.info(f"Статистика: {self.stats}")
            else:
                logger.error(
                    f"Синхронизация завершена с ошибками за {duration:.2f} секунд")

            return success
        except Exception as e:
            logger.exception(f"Критическая ошибка при синхронизации: {e}")
            return False
        finally:
            self.close_connections()


def main():
    synchronizer = Neo4jSynchronizer()
    if not synchronizer.run_sync():
        logger.error("Синхронизация завершена с ошибками")
        exit(1)


if __name__ == "__main__":
    main()
