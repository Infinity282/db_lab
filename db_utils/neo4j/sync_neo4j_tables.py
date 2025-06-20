# -*- coding: utf-8 -*-
import psycopg2
from neo4j import GraphDatabase
import logging
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# Конфигурация логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        self.neo_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    def close(self):
        self.pg_conn.close()
        self.neo_driver.close()

    def fetch_all(self, query, params=None):
        with self.pg_conn.cursor() as cur:
            cur.execute(query, params)
            cols = [desc[0] for desc in cur.description]
            for row in cur.fetchall():
                yield dict(zip(cols, row))

    def clear_neo4j(self):
        logger.info("Clearing Neo4j database")
        with self.neo_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("Neo4j database cleared")

    def sync_course_of_classes(self):
        logger.info("Starting sync_course_of_classes")
        cypher = '''
        UNWIND $rows AS row
        MERGE (c:Course_of_classes {postgres_id: row.id})
        SET c.name = row.name, c.description = row.description, 
            c.tech_requirements = row.tech_requirements, 
            c.department_id = row.department_id, c.specialty_id = row.specialty_id
        '''
        rows = list(self.fetch_all("""
            SELECT id, name, description, tech_requirements, department_id, specialty_id 
            FROM Course_of_classes
        """))
        logger.info(f"Fetched {len(rows)} course_of_classes rows")
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)
        logger.info("Completed sync_course_of_classes")

    def sync_student_groups(self):
        logger.info("Starting sync_student_groups")
        cypher = '''
        UNWIND $rows AS row
        MERGE (g:Student_Group {postgres_id: row.id})
        SET g.name = row.name, g.course_year = row.course_year, 
            g.department_id = row.department_id, g.specialty_id = row.specialty_id
        '''
        rows = list(self.fetch_all("""
            SELECT id, name, course_year, department_id, specialty_id 
            FROM Student_Groups
        """))
        logger.info(f"Fetched {len(rows)} student_group rows")
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)
        logger.info("Completed sync_student_groups")

    def sync_classes(self):
        logger.info("Starting sync_classes")
        cypher = '''
        UNWIND $rows AS row
        MATCH (c:Course_of_classes {postgres_id: row.course_of_class_id})
        MERGE (cl:Class {postgres_id: row.id})
        SET cl.name = row.name, cl.type = row.type
        MERGE (c)-[:HAS_CLASS]->(cl)
        '''
        rows = list(self.fetch_all("""
            SELECT id, course_of_class_id, name, type
            FROM Class
        """))
        logger.info(f"Fetched {len(rows)} class rows")
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)
        logger.info("Completed sync_classes")

    def sync_students(self):
        logger.info("Starting sync_students")
        cypher = '''
        UNWIND $rows AS row
        MATCH (g:Student_Group {postgres_id: row.group_id})
        MERGE (s:Student {postgres_id: row.id})
        SET s.name = row.name, s.enrollment_year = row.enrollment_year, 
            s.date_of_birth = row.date_of_birth, s.email = row.email, 
            s.book_number = row.book_number
        MERGE (g)-[:HAS_STUDENT]->(s)
        '''
        rows = list(self.fetch_all("""
            SELECT id, group_id, name, enrollment_year, date_of_birth::text, email, book_number 
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
        MATCH (g:Student_Group {postgres_id: row.group_id})
        MATCH (c:Course_of_classes {postgres_id: row.course_of_class_id})
        MERGE (sch:Schedule {postgres_id: row.id})
        SET sch.room = row.room, sch.scheduled_date = row.scheduled_date, 
            sch.start_time = row.start_time, sch.end_time = row.end_time
        MERGE (sch)-[:FOR_GROUP]->(g)
        MERGE (c)-[:SCHEDULED_AS]->(sch)
        '''
        rows = list(self.fetch_all("""
            SELECT id, group_id, course_of_class_id, room, scheduled_date::text, 
                start_time::text, end_time::text
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
        SET a.attended = row.attended, a.absence_reason = row.absence_reason
        MERGE (s)-[:ATTENDS]->(a)
        MERGE (a)-[:FOR_SCHEDULE]->(sch)
        '''
        rows = list(self.fetch_all("""
            SELECT a.id, a.student_id, a.schedule_id, a.attended, a.absence_reason
            FROM Attendance a
        """))
        logger.info(f"Fetched {len(rows)} attendance rows")
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)
        logger.info("Completed sync_attendance")

    def sync_class_materials(self):
        logger.info("Starting sync_class_materials")
        cypher = '''
        UNWIND $rows AS row
        MATCH (cl:Class {postgres_id: row.class_id})
        MERGE (m:Class_Materials {postgres_id: row.id})
        SET m.file_path = row.file_path, m.uploaded_at = row.uploaded_at
        MERGE (cl)-[:HAS]->(m)
        '''
        rows = list(self.fetch_all("""
            SELECT 
                id, 
                class_id, 
                (content::json->>'file_path') AS file_path, 
                (content::json->>'uploaded_at') AS uploaded_at
            FROM Class_Materials
        """))
        logger.info(f"Fetched {len(rows)} class_materials rows")
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)
        logger.info("Completed sync_class_materials")

    def run_all(self):
        self.clear_neo4j()
        self.sync_course_of_classes()
        self.sync_student_groups()
        self.sync_classes()
        self.sync_students()
        self.sync_schedule()
        self.sync_attendance()
        self.sync_class_materials()
        logger.info("Синхронизация завершена.")

if __name__ == '__main__':
    service = SyncService(PG_CONFIG, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        service.run_all()
    finally:
        service.close()