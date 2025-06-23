import psycopg2
import logging
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PostgresTool:
    def __init__(self, host=DB_HOST):
        self.conn = None
        self.host = host
        self.connect()

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=self.host,
                port=DB_PORT
            )
            logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"PostgreSQL connection error: {str(e)}")
            raise

    def get_courses_lectures(self, start_date, end_date):
        try:
            with self.conn.cursor() as cur:
                query = """
                SELECT
                    c.id AS course_id,
                    c.name AS course_name,
                    cl.id AS lecture_id,
                    cl.name AS topic,
                    s.scheduled_date AS date,
                    s.start_time,
                    s.end_time,
                    cl.tech_requirements
                FROM course_of_classes c
                JOIN class cl ON c.id = cl.course_of_class_id
                JOIN schedule s ON cl.id = s.class_id
                WHERE
                    cl.type = 'лекция'
                    AND s.scheduled_date >= %s
                    AND s.scheduled_date <= %s
                ORDER BY c.id, s.scheduled_date, s.start_time
                """
                cur.execute(query, (start_date, end_date))
                columns = [desc[0] for desc in cur.description]
                results = [dict(zip(columns, row)) for row in cur.fetchall()]
                logger.info(f"Fetched {len(results)} courses and lectures")
                return results
        except Exception as e:
            logger.error(f"Error fetching courses and lectures: {str(e)}")
            return []

    def get_student_count(self, course_id):
        try:
            with self.conn.cursor() as cur:
                query = """
                SELECT COUNT(DISTINCT s.id)
                FROM students s
                JOIN student_groups g ON s.group_id = g.id
                JOIN schedule sch ON g.id = sch.group_id
                JOIN class cl ON sch.class_id = cl.id
                WHERE cl.course_of_class_id = %s
                """
                cur.execute(query, (course_id,))
                count = cur.fetchone()[0]
                logger.info(f"Student count for course {course_id}: {count}")
                return count
        except Exception as e:
            logger.error(f"Error fetching student count: {str(e)}")
            return 0

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("PostgreSQL connection closed")

    def __del__(self):
        self.close()