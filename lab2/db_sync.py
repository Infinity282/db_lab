from neo4j import GraphDatabase
import psycopg2
from datetime import date
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class SyncService:
    def __init__(self, pg_config, neo4j_uri, neo4j_user, neo4j_password):
        self.pg_conn = psycopg2.connect(**pg_config)
        self.pg_cur = self.pg_conn.cursor()
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    def close(self):
        self.pg_cur.close()
        self.pg_conn.close()
        self.neo4j_driver.close()

    def _calculate_semester_dates(self, year: int, semester: int):
        logger.info(f"Calculating semester dates for year={year}, semester={semester}")
        if semester not in [1, 2]:
            raise ValueError("Semester must be 1 or 2")
        if semester == 1:
            start = date(year, 9, 1)
            end = date(year, 12, 31)
        else:
            start = date(year, 2, 1)
            end = date(year, 6, 30)
        return start, end

    def generate_audience_report(self, year: int, semester: int):
        logger.info(f"Generating audience report for year={year}, semester={semester}")
        start_date, end_date = self._calculate_semester_dates(year, semester)
        params = {'start': str(start_date), 'end': str(end_date)}
        cypher_query = '''
        MATCH (sch:Schedule)
        WHERE date(sch.scheduled_date) >= date($start) AND date(sch.scheduled_date) <= date($end)
        MATCH (sch)-[:FOR_GROUP]->(g:Student_Group)-[:HAS_STUDENT]->(s:Student)
        WITH sch, COUNT(DISTINCT s) AS total_students
        MATCH (c:Course_of_classes)-[:SCHEDULED_AS]->(sch)
        RETURN c.name AS course_name, sch.room AS room_name, 
               c.tech_requirements AS tech_requirements, total_students AS total_students
        ORDER BY course_name
        '''
        with self.neo4j_driver.session() as session:
            results = session.run(cypher_query, **params)
            report = [dict(record) for record in results]
            logger.info(f"Generated report with {len(report)} entries")
            return report

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
            SELECT id, department_id, specialty_id, name, description, tech_requirements 
            FROM Course_of_classes
        """))
        logger.info(f"Fetched {len(rows)} course_of_classes rows")
        with self.neo4j_driver.session() as session:
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
        with self.neo4j_driver.session() as session:
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
        with self.neo4j_driver.session() as session:
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
        with self.neo4j_driver.session() as session:
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
        with self.neo4j_driver.session() as session:
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
            SELECT id, student_id, schedule_id, attended, absence_reason 
            FROM Attendance
        """))
        logger.info(f"Fetched {len(rows)} attendance rows")
        with self.neo4j_driver.session() as session:
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
            SELECT id, class_id, (content->>'file_path') AS file_path, (content->>'uploaded_at') AS uploaded_at
            FROM Class_Materials
        """))
        logger.info(f"Fetched {len(rows)} class_materials rows")
        with self.neo4j_driver.session() as session:
            session.run(cypher, rows=rows)
        logger.info("Completed sync_class_materials")

    def fetch_all(self, query, params=None):
        """Fetch all rows from a PostgreSQL query and return as a list of dictionaries."""
        with self.pg_conn.cursor() as cur:
            cur.execute(query, params)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    def sync_data(self):
        logger.info("Clearing Neo4j database")
        with self.neo4j_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("Neo4j database cleared")
        self.sync_course_of_classes()
        self.sync_student_groups()
        self.sync_classes()
        self.sync_students()
        self.sync_schedule()
        self.sync_attendance()
        self.sync_class_materials()
        logger.info("Data synchronization completed.")