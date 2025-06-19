from neo4j import GraphDatabase
import psycopg2
from datetime import date
import redis

class SyncService:
    def __init__(self, pg_config, neo4j_uri, neo4j_user, neo4j_password, redis_host, redis_port):
        # Подключение к PostgreSQL
        self.pg_conn = psycopg2.connect(**pg_config)
        self.pg_cur = self.pg_conn.cursor()
        # Подключение к Neo4j
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        # Подключение к Redis
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

    def close(self):
        self.pg_cur.close()
        self.pg_conn.close()
        self.neo4j_driver.close()
        self.redis_client.close()

    def sync_data(self):
        # Синхронизация Universities
        self.pg_cur.execute("SELECT id, name, address, founded_date FROM Universities")
        with self.neo4j_driver.session() as session:
            for uni_id, uni_name, uni_address, uni_founded in self.pg_cur.fetchall():
                session.run(
                    "MERGE (u:University {id: $id}) "
                    "SET u.name = $name, u.address = $address, u.founded_date = $founded",
                    id=uni_id, name=uni_name, address=uni_address, founded=uni_founded.isoformat() if uni_founded else None
                )
        # Синхронизация Student_Groups
        self.pg_cur.execute("SELECT id, name, department_id, course_year FROM Student_Groups")
        with self.neo4j_driver.session() as session:
            for sg_id, sg_name, dept_id, course_year in self.pg_cur.fetchall():
                session.run(
                    "MATCH (d:Department {id: $did}) "
                    "MERGE (g:Student_Group {id: $gid}) "
                    "SET g.name = $name, g.course_year = $year "
                    "MERGE (d)-[:FORMS]->(g)",
                    did=dept_id, gid=sg_id, name=sg_name, year=course_year
                )
        # Синхронизация Students (с Redis)
        self.pg_cur.execute("SELECT id, name, book_number, student_group_id FROM Students")
        for std_id, std_name, book_num, sg_id in self.pg_cur.fetchall():
            with self.neo4j_driver.session() as session:
                session.run(
                    "MATCH (g:Student_Group {id: $gid}) "
                    "MERGE (s:Student {id: $sid}) "
                    "SET s.name = $name, s.book_number = $book "
                    "MERGE (g)-[:HAS_STUDENT]->(s)",
                    gid=sg_id, sid=std_id, name=std_name, book=book_num
                )
            self.redis_client.hset(f"student:{std_id}", mapping={
                "id": std_id, "name": std_name, "book_number": book_num, "group_id": sg_id
            })
        # Синхронизация Course_of_lecture
        self.pg_cur.execute("SELECT id, name, department_id, description, tech_requirements FROM Course_of_lecture")
        with self.neo4j_driver.session() as session:
            for course_id, course_name, dept_id, desc, tech_req in self.pg_cur.fetchall():
                session.run(
                    "MATCH (d:Department {id: $did}) "
                    "MERGE (c:Course_of_lecture {id: $cid}) "
                    "SET c.name = $name, c.description = $desc, c.tech_requirements = $tech "
                    "MERGE (d)-[:OFFERS]->(c)",
                    did=dept_id, cid=course_id, name=course_name, desc=desc, tech=tech_req
                )
        # Синхронизация Lecture
        self.pg_cur.execute("SELECT id, course_id, topic, lecture_date, duration, tags FROM Lecture")
        with self.neo4j_driver.session() as session:
            for lect_id, course_id, topic, lect_date, duration, tags in self.pg_cur.fetchall():
                session.run(
                    "MATCH (c:Course_of_lecture {id: $cid}) "
                    "MERGE (l:Lecture {id: $lid}) "
                    "SET l.topic = $topic, l.lecture_date = $date, l.duration = $dur, l.tags = $tags "
                    "MERGE (c)-[:HAS_LECTURE]->(l)",
                    cid=course_id, lid=lect_id, topic=topic, date=lect_date.isoformat() if lect_date else None,
                    dur=duration, tags=tags
                )
        # Синхронизация Schedule
        self.pg_cur.execute("SELECT id, student_group_id, lecture_id, scheduled_date, lecture_time, planned_hours FROM Schedule")
        with self.neo4j_driver.session() as session:
            for sch_id, sg_id, lect_id, sch_date, lect_time, planned_hours in self.pg_cur.fetchall():
                session.run(
                    "MATCH (g:Student_Group {id: $gid}), (l:Lecture {id: $lid}) "
                    "MERGE (s:Schedule {id: $sid}) "
                    "SET s.scheduled_date = $date, s.lecture_time = $time, s.planned_hours = $hours "
                    "MERGE (l)-[:SCHEDULED_AT]->(s) "
                    "MERGE (s)-[:FOR_GROUP]->(g)",
                    gid=sg_id, lid=lect_id, sid=sch_id, date=sch_date.isoformat() if sch_date else None,
                    time=lect_time, hours=planned_hours
                )
        # Синхронизация Attendance
        self.pg_cur.execute("SELECT id, student_id, schedule_id, attended, attendance_date FROM Attendance")
        with self.neo4j_driver.session() as session:
            for att_id, std_id, sch_id, attended, att_date in self.pg_cur.fetchall():
                session.run(
                    "MATCH (s:Student {id: $sid}), (sch:Schedule {id: $schid}) "
                    "MERGE (a:Attendance {id: $aid}) "
                    "SET a.attended = $att, a.attendance_date = $date "
                    "MERGE (s)-[:RECORDS]->(a) "
                    "MERGE (a)-[:LOGS]->(sch)",
                    sid=std_id, schid=sch_id, aid=att_id, att=attended,
                    date=att_date.isoformat() if att_date else None
                )

    def generate_group_report(self, group_id: int):
        """Генерирует отчет по группе студентов с учетом лекций с тегом специальной дисциплины."""
        # 1. Информация о группе
        with self.neo4j_driver.session() as session:
            group_rec = session.run(
                "MATCH (g:Student_Group {id: $gid}) "
                "RETURN g.id AS id, g.name AS name, g.department_id AS dept_id",
                gid=group_id
            ).single()
            if not group_rec:
                return []
            group_info = {
                'id': group_rec['id'],
                'name': group_rec['name'],
                'department_id': group_rec['dept_id']
            }

            # Студенты группы
            students = [dict(r) for r in session.run(
                "MATCH (g:Student_Group {id: $gid})-[:HAS_STUDENT]->(s:Student) "
                "RETURN s.id AS id, s.name AS name",
                gid=group_id
            )]

            # Расписания с лекциями, содержащими тег специальной дисциплины (например, 'special')
            schedules = [dict(r) for r in session.run(
                "MATCH (g:Student_Group {id: $gid})-[:FOR_GROUP]->(s:Schedule)-[:SCHEDULED_AT]->(l:Lecture) "
                "WHERE ANY(tag IN l.tags WHERE tag = 'special') "
                "MATCH (c:Course_of_lecture)-[:HAS_LECTURE]->(l) "
                "RETURN s.id AS schedule_id, c.id AS course_id, c.name AS course_name, s.planned_hours AS planned_hours",
                gid=group_id
            )]

        if not students or not schedules:
            return []

        schedule_ids = [s['schedule_id'] for s in schedules]
        student_ids = [s['id'] for s in students]
        course_map = {(s['schedule_id'], s['course_id']): s['course_name'] for s in schedules}
        planned_hours_map = {s['schedule_id']: s['planned_hours'] for s in schedules}

        # 2. Получение данных о посещаемости из PostgreSQL
        self.pg_cur.execute(
            "SELECT student_id, schedule_id, SUM((attended::int) * planned_hours) AS attended_hours "
            "FROM Attendance a "
            "JOIN Schedule s ON a.schedule_id = s.id "
            "WHERE student_id = ANY(%s) AND schedule_id = ANY(%s) "
            "GROUP BY student_id, schedule_id",
            (student_ids, schedule_ids)
        )
        attendance_data = { (r[0], r[1]): r[2] for r in self.pg_cur.fetchall() }

        # 3. Формирование отчета
        report = []
        for student in students:
            student_id = student['id']
            student_name = student['name']
            for schedule_id in schedule_ids:
                course_id = next(k[1] for k in course_map.keys() if k[0] == schedule_id)
                course_name = course_map.get((schedule_id, course_id))
                planned_hours = planned_hours_map.get(schedule_id, 0)
                attended_hours = attendance_data.get((student_id, schedule_id), 0)
                report.append({
                    'group_info': group_info,
                    'student_info': {'id': student_id, 'name': student_name},
                    'course_info': {'id': course_id, 'name': course_name},
                    'planned_hours': planned_hours,
                    'attended_hours': attended_hours
                })

        return report