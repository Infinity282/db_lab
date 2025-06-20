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

        # Синхронизация Institutes
        self.pg_cur.execute("SELECT id, university_id, name FROM Institutes")
        with self.neo4j_driver.session() as session:
            for inst_id, uni_id, inst_name in self.pg_cur.fetchall():
                session.run(
                    "MATCH (u:University {id: $uid}) "
                    "MERGE (i:Institute {id: $iid}) "
                    "SET i.name = $name "
                    "MERGE (u)-[:HAS_INSTITUTE]->(i)",
                    uid=uni_id, iid=inst_id, name=inst_name
                )

        # Синхронизация Departments
        self.pg_cur.execute("SELECT id, institute_id, name FROM Departments")
        with self.neo4j_driver.session() as session:
            for dept_id, inst_id, dept_name in self.pg_cur.fetchall():
                session.run(
                    "MATCH (i:Institute {id: $iid}) "
                    "MERGE (d:Department {id: $did}) "
                    "SET d.name = $name "
                    "MERGE (i)-[:HAS_DEPARTMENT]->(d)",
                    iid=inst_id, did=dept_id, name=dept_name
                )

        # Синхронизация Specialties
        self.pg_cur.execute("SELECT id, name FROM Specialties")
        with self.neo4j_driver.session() as session:
            for spec_id, spec_name in self.pg_cur.fetchall():
                session.run(
                    "MERGE (sp:Specialty {id: $sid}) "
                    "SET sp.name = $name",
                    sid=spec_id, name=spec_name
                )

        # Синхронизация Student_Groups
        self.pg_cur.execute("SELECT id, name, department_id, course_year, specialty_id FROM Student_Groups")
        with self.neo4j_driver.session() as session:
            for sg_id, sg_name, dept_id, course_year, spec_id in self.pg_cur.fetchall():
                session.run(
                    "MATCH (d:Department {id: $did}), (sp:Specialty {id: $sid}) "
                    "MERGE (g:Student_Group {id: $gid}) "
                    "SET g.name = $name, g.course_year = $year "
                    "MERGE (d)-[:FORMS]->(g) "
                    "MERGE (g)-[:BELONGS_TO_SPECIALTY]->(sp)",
                    did=dept_id, sid=spec_id, gid=sg_id, name=sg_name, year=course_year
                )

        # Синхронизация Course_of_classes (сохраняем как Course_of_lecture)
        self.pg_cur.execute("SELECT id, name, department_id, description, tech_requirements, specialty_id FROM Course_of_classes")
        with self.neo4j_driver.session() as session:
            for course_id, course_name, dept_id, desc, tech_req, spec_id in self.pg_cur.fetchall():
                session.run(
                    "MATCH (d:Department {id: $did}), (sp:Specialty {id: $sid}) "
                    "MERGE (c:Course_of_lecture {id: $cid}) "
                    "SET c.name = $name, c.description = $desc, c.tech_requirements = $tech "
                    "MERGE (d)-[:OFFERS]->(c) "
                    "MERGE (c)-[:BELONGS_TO_SPECIALTY]->(sp)",
                    did=dept_id, sid=spec_id, cid=course_id, name=course_name, desc=desc, tech=tech_req
                )

        # Синхронизация Class (сохраняем как Lecture)
        self.pg_cur.execute("""
            SELECT c.id, c.course_of_class_id, c.name, c.type, s.scheduled_date,
                   EXTRACT(EPOCH FROM (s.end_time - s.start_time))/3600 AS hours
            FROM Class c
            JOIN Schedule s ON c.course_of_class_id = s.course_of_class_id
        """)
        with self.neo4j_driver.session() as session:
            for class_id, course_id, name, class_type, sch_date, hours in self.pg_cur.fetchall():
                session.run(
                    "MATCH (c:Course_of_lecture {id: $cid}) "
                    "MERGE (l:Lecture {id: $lid}) "
                    "SET l.topic = $topic, l.lecture_date = $date, l.hours = $hours, l.tags = $tags "
                    "MERGE (c)-[:HAS_LECTURE]->(l)",
                    cid=course_id, lid=class_id, topic=name, date=sch_date.isoformat() if sch_date else None,
                    hours=hours, tags=class_type
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

        # Синхронизация Schedule
        self.pg_cur.execute("SELECT id, student_group_id, course_of_class_id, room, scheduled_date, start_time, end_time FROM Schedule")
        with self.neo4j_driver.session() as session:
            for sch_id, sg_id, course_id, room, sch_date, start_time, end_time in self.pg_cur.fetchall():
                session.run(
                    "MATCH (g:Student_Group {id: $gid}), (c:Course_of_lecture {id: $cid}) "
                    "MERGE (s:Schedule {id: $sid}) "
                    "SET s.room = $room, s.scheduled_date = $date, s.start_time = $start, s.end_time = $end "
                    "MERGE (c)-[:SCHEDULED_FOR]->(s) "
                    "MERGE (s)-[:FOR_GROUP]->(g)",
                    gid=sg_id, cid=course_id, sid=sch_id, room=room, date=sch_date.isoformat() if sch_date else None,
                    start=start_time, end=end_time
                )

        # Синхронизация Attendance
        self.pg_cur.execute("SELECT id, student_id, schedule_id, attended, absence_reason FROM Attendance")
        with self.neo4j_driver.session() as session:
            for att_id, std_id, sch_id, attended, absence_reason in self.pg_cur.fetchall():
                session.run(
                    "MATCH (s:Student {id: $sid}), (sch:Schedule {id: $schid}) "
                    "MERGE (a:Attendance {id: $aid}) "
                    "SET a.attended = $att, a.absence_reason = $reason "
                    "MERGE (s)-[:RECORDS]->(a) "
                    "MERGE (a)-[:LOGS]->(sch)",
                    sid=std_id, schid=sch_id, aid=att_id, att=attended, reason=absence_reason
                )

        # Синхронизация Class_Materials (сохраняем как LectureMaterial)
        self.pg_cur.execute("SELECT id, class_id, (content->>'file_path') AS file_path, (content->>'uploaded_at') AS uploaded_at FROM Class_Materials")
        with self.neo4j_driver.session() as session:
            for mat_id, class_id, file_path, uploaded_at in self.pg_cur.fetchall():
                session.run(
                    "MATCH (l:Lecture {id: $lid}) "
                    "MERGE (m:LectureMaterial {id: $mid}) "
                    "SET m.file_path = $path, m.uploaded_at = $uploaded "
                    "MERGE (l)-[:HAS_MATERIAL]->(m)",
                    lid=class_id, mid=mat_id, path=file_path, uploaded=uploaded_at
                )

    def generate_group_report(self, group_id: int):
        """Генерирует отчет по группе студентов с учетом лекций с тегом 'lecture'."""
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

            # Студенты группы (из Redis для оптимизации)
            student_keys = self.redis_client.keys(f"student:*")
            students = []
            for key in student_keys:
                student_data = self.redis_client.hgetall(key)
                if int(student_data['group_id']) == group_id:
                    students.append({
                        'id': int(student_data['id']),
                        'name': student_data['name']
                    })

            # Расписания с лекциями, содержащими тег 'lecture'
            schedules = [dict(r) for r in session.run(
                """
                MATCH (g:Student_Group {id: $gid})-[:FOR_GROUP]->(s:Schedule)-[:SCHEDULED_FOR]->(c:Course_of_lecture)
                MATCH (l:Lecture)-[:SCHEDULED_AT]->(s)
                WHERE l.tags = 'lecture'
                RETURN s.id AS schedule_id, c.id AS course_id, c.name AS course_name, l.hours AS planned_hours
                """,
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
            """
            SELECT a.student_id, a.schedule_id, a.attended, s.course_of_class_id,
                   EXTRACT(EPOCH FROM (s.end_time - s.start_time))/3600 AS hours
            FROM Attendance a
            JOIN Schedule s ON a.schedule_id = s.id
            WHERE a.student_id = ANY(%s) AND a.schedule_id = ANY(%s)
            """,
            (student_ids, schedule_ids)
        )
        attendance_data = {}
        for student_id, schedule_id, attended, course_id, hours in self.pg_cur.fetchall():
            if attended:
                attendance_data[(student_id, schedule_id)] = hours

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