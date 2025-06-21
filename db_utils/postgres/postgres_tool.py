import psycopg2
import logging
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgresTool:
    def __init__(self, pg_host=DB_HOST):
        self.conn = None
        self.pg_host = pg_host

        self.connect()

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=self.pg_host,
                port=DB_PORT
            )
            logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"PostgreSQL connection error: {str(e)}")
            raise

    def get_course_lectures(self, course_id, semester, year):
        try:
            with self.conn.cursor() as cur:
                query = """
                SELECT 
                    c.id AS course_id,
                    c.name AS course_name,
                    l.id AS lecture_id,
                    l.topic,
                    l.date,
                    l.duration
                FROM courses c
                JOIN lectures l ON c.id = l.course_id
                WHERE 
                    c.id = %s
                    AND c.semester = %s
                    AND c.year = %s
                """
                cur.execute(query, (course_id, semester, year))
                columns = [desc[0] for desc in cur.description]
                results = [dict(zip(columns, row)) for row in cur.fetchall()]
                return results
        except Exception as e:
            logger.error(f"Error fetching course lectures: {str(e)}")
            return []

    def get_student_count(self, course_id):
        try:
            with self.conn.cursor() as cur:
                query = """
                SELECT COUNT(*) 
                FROM enrollments 
                WHERE course_id = %s
                """
                cur.execute(query, (course_id,))
                return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Error fetching student count: {str(e)}")
            return 0

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("PostgreSQL connection closed")

    def __del__(self):
        self.close()
