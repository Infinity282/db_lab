import psycopg2
from neo4j import GraphDatabase
import datetime
from env import (DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT,
                 DB_USER, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

PG_CONFIG = {
    'dbname': DB_NAME,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'host': DB_HOST,
    'port': DB_PORT,
}


class SyncService:
    def __init__(self, pg_conf, neo4j_uri, neo4j_user, neo4j_password):
        self.pg_conn = psycopg2.connect(**pg_conf)
        self.neo_driver = GraphDatabase.driver(
            neo4j_uri, auth=(neo4j_user, neo4j_password))

    def close(self):
        self.pg_conn.close()
        self.neo_driver.close()

    def fetch_all(self, query, params=None):
        with self.pg_conn.cursor() as cur:
            cur.execute(query, params)
            cols = [desc[0] for desc in cur.description]
            for row in cur.fetchall():
                yield dict(zip(cols, row))

    def sync_courses(self):
        cypher = '''
        UNWIND $rows AS row
        MERGE (c:Course {postgres_id: row.course_id})
        SET c.name = row.name, c.description = row.description, 
            c.duration_weeks = row.duration_weeks, c.department_id = row.department_id
        '''
        rows = list(self.fetch_all("""
            SELECT course_id, name, description, duration_weeks, department_id 
            FROM Courses
        """))
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)

    def sync_student_groups(self):
        cypher = '''
        UNWIND $rows AS row
        MERGE (g:StudentGroup {postgres_id: row.group_id})
        SET g.name = row.name, g.course_year = row.course_year, 
            g.department_id = row.department_id, g.specialty_id = row.specialty_id
        '''
        rows = list(self.fetch_all("""
            SELECT group_id, name, course_year, department_id, specialty_id 
            FROM Student_Groups
        """))
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)

    def sync_group_courses(self):
        cypher = '''
        UNWIND $rows AS row
        MATCH (g:StudentGroup {postgres_id: row.group_id})
        MATCH (c:Course {postgres_id: row.course_id})
        MERGE (g)-[:TAKES_COURSE]->(c)
        '''
        rows = list(self.fetch_all("""
            SELECT group_id, course_id 
            FROM Group_Courses
        """))
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)

    def sync_students(self):
        cypher = '''
        UNWIND $rows AS row
        MATCH (g:StudentGroup {postgres_id: row.group_id})
        MERGE (s:Student {postgres_id: row.student_id})
        SET s.name = row.name, s.enrollment_year = row.enrollment_year, 
            s.date_of_birth = row.date_of_birth, s.email = row.email, 
            s.book_number = row.book_number
        MERGE (s)-[:MEMBER_OF]->(g)
        '''
        rows = list(self.fetch_all("""
            SELECT student_id, name, enrollment_year, date_of_birth, email, book_number, group_id 
            FROM Students
        """))
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)

    def run_all(self):
        self.sync_courses()  # Добавлена синхронизация Courses
        self.sync_student_groups()
        self.sync_group_courses()
        self.sync_students()
        print("Синхронизация завершена.")


if __name__ == '__main__':
    service = SyncService(PG_CONFIG, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        service.run_all()
    finally:
        service.close()
