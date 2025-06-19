from neo4j import GraphDatabase
import psycopg2
from datetime import date

class SyncService:
    def __init__(self, pg_config, neo4j_uri, neo4j_user, neo4j_password):
        # Подключение к PostgreSQL
        self.pg_conn = psycopg2.connect(**pg_config)
        self.pg_cur = self.pg_conn.cursor()
        # Подключение к Neo4j
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    def close(self):
        self.pg_cur.close()
        self.pg_conn.close()
        self.neo4j_driver.close()

    def _calculate_semester_dates(self, year: int, semester: int):
        """Вычисляет даты начала и конца семестра."""
        if semester == 1:
            start = date(year, 2, 1)
            end = date(year, 6, 30)
        else:
            start = date(year, 9, 1)
            end = date(year + 1, 1, 31)
        return start, end

    def generate_audience_report(self, year: int, semester: int):
        """Генерирует отчет о необходимом объеме аудитории для заданного семестра."""
        start_date, end_date = self._calculate_semester_dates(year, semester)
        params = {
            'start': str(start_date),
            'end': str(end_date)
        }
        cypher_query = """
        MATCH (sch:Schedule)
        WHERE date(sch.scheduled_date) >= date($start) AND date(sch.scheduled_date) <= date($end)
        MATCH (sch)-[:FOR_GROUP]->(g:Student_Group)-[:HAS_STUDENT]->(s:Student)
        WITH sch, COUNT(DISTINCT s) AS total_students
        MATCH (l:Lecture)-[:SCHEDULED_AT]->(sch)
        MATCH (c:Course_of_lecture)-[:HAS_LECTURE]->(l)
        RETURN 
            c.name AS course_name,
            l.topic AS lecture_name,
            c.tech_requirements AS tech_requirements,
            total_students
        ORDER BY course_name, lecture_name
        """
        with self.neo4j_driver.session() as session:
            results = session.run(cypher_query, **params)
            return [dict(record) for record in results]

    # Синхронизация данных (опционально, если нужно обновлять граф перед отчетом)
    def sync_data(self):
        # Синхронизация Universities
        self.pg_cur.execute("SELECT id, name, address, founded_date FROM Universities")
        with self.neo4j_driver.session() as session:
            for uni_id, uni_name, uni_address, uni_founded in self.pg_cur.fetchall():
                session.run(
                    "MERGE (u:University {id: $id}) "
                    "SET u.name = $name, u.address = $address, u.founded_date = $founded",
                    id=uni_id, name=uni_name, address=uni_address, founded=date.isoformat() if uni_founded else None
                )
        # Дополнительные синхронизации (Institutes, Departments, etc.) можно добавить аналогично