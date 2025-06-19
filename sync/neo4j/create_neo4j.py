# -*- coding: utf-8 -*-
import psycopg2
from neo4j import GraphDatabase
import logging

# Конфигурация логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация подключения
PG_CONFIG = {
    'dbname': "postgres_db",
    'user': "postgres_user",
    'password': "postgres_password",
    'host': 'localhost',
    'port': 5430,
}

NEO4J_URI = 'bolt://localhost:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'strongpassword'

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

    def sync_course_of_lecture(self):
        logger.info("Starting sync_course_of_lecture")
        cypher = '''
        UNWIND $rows AS row
        MERGE (c:Course_of_lecture {postgres_id: row.id})
        SET c.name = row.name, c.description = row.description, 
            c.tech_requirements = row.tech_requirements, 
            c.department_id = row.department_id
        '''
        rows = list(self.fetch_all("""
            SELECT id, name, description, tech_requirements, department_id 
            FROM Course_of_lecture
        """))
        logger.info(f"Fetched {len(rows)} course_of_lecture rows")
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)
        logger.info("Completed sync_course_of_lecture")

    def sync_student_groups(self):
        logger.info("Starting sync_student_groups")
        cypher = '''
        UNWIND $rows AS row
        MERGE (g:Student_Group {postgres_id: row.id})
        SET g.name = row.name, g.course_year = row.course_year, 
            g.department_id = row.department_id
        '''
        rows = list(self.fetch_all("""
            SELECT id, name, course_year, department_id 
            FROM Student_Groups
        """))
        logger.info(f"Fetched {len(rows)} student_group rows")
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)
        logger.info("Completed sync_student_groups")

    def sync_lectures(self):
        logger.info("Starting sync_lectures")
        cypher = '''
        UNWIND $rows AS row
        MATCH (c:Course_of_lecture {postgres_id: row.course_id})
        MERGE (l:Lecture {postgres_id: row.id})
        SET l.topic = row.topic, l.lecture_date = row.lecture_date, 
            l.duration = row.duration, l.tags = row.tags
        MERGE (c)-[:HAS_LECTURE]->(l)
        '''
        rows = list(self.fetch_all("""
            SELECT id, course_id, topic, lecture_date::text, duration, tags 
            FROM Lecture
        """))
        logger.info(f"Fetched {len(rows)} lecture rows")
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)
        logger.info("Completed sync_lectures")

    def sync_students(self):
        logger.info("Starting sync_students")
        cypher = '''
        UNWIND $rows AS row
        MATCH (g:Student_Group {postgres_id: row.student_group_id})
        MERGE (s:Student {postgres_id: row.id})
        SET s.name = row.name, s.enrollment_year = row.enrollment_year, 
            s.date_of_birth = row.date_of_birth, s.email = row.email, 
            s.book_number = row.book_number
        MERGE (g)-[:HAS_STUDENT]->(s)
        '''
        rows = list(self.fetch_all("""
            SELECT id, student_group_id, name, enrollment_year, date_of_birth::text, email, book_number 
            FROM Students
        """))
        logger.info(f"Fetched {len(rows)} student rows")
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)
        logger.info("Completed sync_students")

    def sync_schedule(self):
        logger.info("Starting sync_schedule")
        cypher = '''
        UNWIND $rows AS row
        MATCH (g:Student_Group {postgres_id: row.student_group_id})
        MATCH (l:Lecture {postgres_id: row.lecture_id})
        MERGE (sch:Schedule {postgres_id: row.id})
        SET sch.room = row.room, sch.scheduled_date = row.scheduled_date, 
            sch.lecture_time = row.lecture_time, sch.planned_hours = row.planned_hours
        MERGE (sch)-[:FOR_GROUP]->(g)
        MERGE (l)-[:SCHEDULED_AT]->(sch)
        '''
        rows = list(self.fetch_all("""
            SELECT id, student_group_id, lecture_id, room, scheduled_date::text, lecture_time::text, planned_hours 
            FROM Schedule
        """))
        logger.info(f"Fetched {len(rows)} schedule rows")
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)
        logger.info("Completed sync_schedule")

    def sync_attendance(self):
        logger.info("Starting sync_attendance")
        cypher = '''
        UNWIND $rows AS row
        MATCH (s:Student {postgres_id: row.student_id})
        MATCH (sch:Schedule {postgres_id: row.schedule_id})
        MERGE (a:Attendance {postgres_id: row.id})
        SET a.attended = row.attended, a.attendance_date = row.attendance_date
        MERGE (s)-[:ATTENDS]->(a)
        MERGE (a)-[:FOR_SCHEDULE]->(sch)
        '''
        rows = list(self.fetch_all("""
            SELECT id, student_id, schedule_id, attended, attendance_date::text 
            FROM Attendance
        """))
        logger.info(f"Fetched {len(rows)} attendance rows")
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)
        logger.info("Completed sync_attendance")

    def sync_material_of_lecture(self):
        logger.info("Starting sync_material_of_lecture")
        cypher = '''
        UNWIND $rows AS row
        MATCH (l:Lecture {postgres_id: row.lecture_id})
        MERGE (m:LectureMaterial {postgres_id: row.id})
        SET m.file_path = row.file_path, m.uploaded_at = row.uploaded_at
        MERGE (l)-[:HAS]->(m)
        '''
        rows = list(self.fetch_all("""
            SELECT id, lecture_id, file_path, uploaded_at::text 
            FROM Material_of_lecture
        """))
        logger.info(f"Fetched {len(rows)} material_of_lecture rows")
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)
        logger.info("Completed sync_material_of_lecture")

    def run_all(self):
        self.sync_course_of_lecture()
        self.sync_student_groups()
        self.sync_lectures()
        self.sync_students()
        self.sync_schedule()
        self.sync_attendance()
        self.sync_material_of_lecture()
        logger.info("Синхронизация завершена.")

if __name__ == '__main__':
    service = SyncService(PG_CONFIG, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        service.run_all()
    finally:
        service.close()