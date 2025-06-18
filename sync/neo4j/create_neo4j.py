# -*- coding: utf-8 -*-
import psycopg2
from neo4j import GraphDatabase
import datetime

# Конфигурация подключения
PG_CONFIG = {
    'dbname': "postgres_db",
    'user': "postgres_user",
    'password': "postgres_password",
    'host': 'localhost',
    'port': 5430,
}

NEO4J_URI = 'bolt://localhost:7687'  # Исправлен порт
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
        cypher = '''
        UNWIND $rows AS row
        MERGE (c:Course {postgres_id: row.id})
        SET c.name = row.name, c.description = row.description, 
            c.tech_requirements = row.tech_requirements, 
            c.department_id = row.department_id
        '''
        rows = list(self.fetch_all("""
            SELECT id, name, description, tech_requirements, department_id 
            FROM Course_of_lecture
        """))
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)

    def sync_student_groups(self):
        cypher = '''
        UNWIND $rows AS row
        MERGE (g:StudentGroup {postgres_id: row.id})
        SET g.name = row.name, g.course_year = row.course_year, 
            g.department_id = row.department_id
        '''
        rows = list(self.fetch_all("""
            SELECT id, name, course_year, department_id 
            FROM Student_Groups
        """))
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)

    def sync_lectures(self):
        cypher = '''
        UNWIND $rows AS row
        MATCH (c:Course {postgres_id: row.course_id})
        MERGE (l:Lecture {postgres_id: row.id})
        SET l.topic = row.topic, l.lecture_date = row.lecture_date, 
            l.duration = row.duration, l.tags = row.tags
        MERGE (l)-[:BELONGS_TO]->(c)
        '''
        rows = list(self.fetch_all("""
            SELECT id, course_id, topic, lecture_date, duration, tags 
            FROM Lecture
        """))
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)

    def sync_students(self):
        cypher = '''
        UNWIND $rows AS row
        MATCH (g:StudentGroup {postgres_id: row.student_group_id})
        MERGE (s:Student {postgres_id: row.id})
        SET s.name = row.name, s.enrollment_year = row.enrollment_year, 
            s.date_of_birth = row.date_of_birth, s.email = row.email, 
            s.book_number = row.book_number
        MERGE (s)-[:MEMBER_OF]->(g)
        '''
        rows = list(self.fetch_all("""
            SELECT id, student_group_id, name, enrollment_year, date_of_birth, email, book_number 
            FROM Students
        """))
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)

    def sync_schedule(self):
        cypher = '''
        UNWIND $rows AS row
        MATCH (g:StudentGroup {postgres_id: row.student_group_id})
        MATCH (l:Lecture {postgres_id: row.lecture_id})
        MERGE (sch:Schedule {postgres_id: row.id})
        SET sch.room = row.room, sch.scheduled_date = row.scheduled_date, 
            sch.lecture_time = row.lecture_time, sch.planned_hours = row.planned_hours
        MERGE (sch)-[:FOR_GROUP]->(g)
        MERGE (sch)-[:SCHEDULED_IN]->(l)
        '''
        rows = list(self.fetch_all("""
            SELECT id, student_group_id, lecture_id, room, scheduled_date, lecture_time, planned_hours 
            FROM Schedule
        """))
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)

    def sync_attendance(self):
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
            SELECT id, student_id, schedule_id, attended, attendance_date 
            FROM Attendance
        """))
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)

    def sync_material_of_lecture(self):
        cypher = '''
        UNWIND $rows AS row
        MATCH (l:Lecture {postgres_id: row.lecture_id})
        MERGE (m:LectureMaterial {postgres_id: row.id})
        SET m.file_path = row.file_path, m.uploaded_at = row.uploaded_at
        MERGE (l)-[:HAS]->(m)
        '''
        rows = list(self.fetch_all("""
            SELECT id, lecture_id, file_path, uploaded_at 
            FROM Material_of_lecture
        """))
        with self.neo_driver.session() as session:
            session.run(cypher, rows=rows)

    def run_all(self):
        self.sync_course_of_lecture()
        self.sync_student_groups()
        self.sync_lectures()
        self.sync_students()
        self.sync_schedule()
        self.sync_attendance()
        self.sync_material_of_lecture()
        print("Синхронизация завершена.")

if __name__ == '__main__':
    service = SyncService(PG_CONFIG, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        service.run_all()
    finally:
        service.close()