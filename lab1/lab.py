from neo4j import GraphDatabase
from typing import List, Dict, Optional
import psycopg2
from const import PG_CONFIG

class AttendanceFinder:
    def __init__(
        self,
        uri: str = 'bolt://neo4j:7687',
        user: str = 'neo4j',
        password: str = 'strongpassword'
    ):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.pg_conn = psycopg2.connect(**PG_CONFIG)
        self.pg_conn.autocommit = True

    def close(self):
        self.driver.close()
        self.pg_conn.close()

    def find_worst_attendees(
        self,
        class_ids: List[int],
        top_n: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        return self._compute_attendance(
            class_ids,
            worst=True,
            limit=top_n,
            start_date=start_date,
            end_date=end_date
        )

    def get_attendance_summary(
        self,
        class_ids: List[int],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        return self._compute_attendance(
            class_ids,
            worst=False,
            limit=None,
            start_date=start_date,
            end_date=end_date
        )

    def _compute_attendance(
        self,
        class_ids: List[int],
        worst: bool,
        limit: Optional[int],
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> List[Dict]:
        if not class_ids:
            return []

        # 1. Находим расписания для указанных занятий в заданном периоде
        sql = """
            SELECT s.id AS schedule_id
            FROM Schedule s
            WHERE s.course_of_class_id = ANY(%s)
              AND (%s::date IS NULL OR s.scheduled_date >= %s::date)
              AND (%s::date IS NULL OR s.scheduled_date <= %s::date)
        """
        with self.pg_conn.cursor() as cur:
            cur.execute(sql, (class_ids, start_date, start_date, end_date, end_date))
            rows = cur.fetchall()
        if not rows:
            return []

        schedule_ids = [r[0] for r in rows]

        # 2. Находим студентов через Neo4j
        cypher = """
        UNWIND $schedule_ids AS sid
        MATCH (sch:Schedule {postgres_id: sid})-[:FOR_GROUP]->(g:Student_Group)
        MATCH (g)-[:HAS_STUDENT]->(s:Student)
        RETURN DISTINCT s.postgres_id AS student_id, s.name AS student_name,
                        s.enrollment_year AS enrollment_year, s.date_of_birth AS date_of_birth,
                        s.email AS email, s.book_number AS book_number,
                        g.postgres_id AS group_id, g.name AS group_name
        """
        with self.driver.session() as session:
            neo4j_results = session.run(cypher, schedule_ids=schedule_ids)
            students = [rec.data() for rec in neo4j_results]

        if not students:
            return []

        student_ids = [s["student_id"] for s in students]

        # 3. Вычисляем статистику посещаемости
        stats_sql = """
            SELECT student_id,
                   SUM((attended)::int) AS attended_count,
                   COUNT(*) AS total_count
            FROM Attendance
            WHERE student_id = ANY(%s)
              AND schedule_id = ANY(%s)
            GROUP BY student_id
        """
        with self.pg_conn.cursor() as cur:
            cur.execute(stats_sql, (student_ids, schedule_ids))
            stats = cur.fetchall()

        stat_map = {sid: (att, tot) for sid, att, tot in stats}

        results = []
        for s in students:
            sid = s["student_id"]
            attended_count, total_count = stat_map.get(sid, (0, 0))
            if total_count == 0:
                continue
            pct = round(attended_count / total_count * 100, 2)
            results.append({
                "studentId": sid,
                "studentName": s["student_name"],
                "attendedCount": attended_count,
                "totalCount": total_count,
                "attendancePercent": pct,
                "enrollment_year": s["enrollment_year"],
                "date_of_birth": s["date_of_birth"],
                "email": s["email"],
                "book_number": s["book_number"],
                "group_id": s["group_id"],
                "group_name": s["group_name"]
            })

        if worst:
            results.sort(key=lambda x: x["attendancePercent"])
        else:
            results.sort(key=lambda x: x["studentName"])

        if limit:
            results = results[:limit]

        return results

if __name__ == '__main__':
    from lecture_session import LectureMaterialSearcher
    term = "физика"
    searcher = LectureMaterialSearcher(es_host='localhost', es_port=9200, es_user='elastic', es_password='secret')
    class_ids = searcher.search_by_course_and_session_type(term, 'lecture')
    print(f"Найдены занятия: {class_ids}")

    finder = AttendanceFinder()

    start = "2023-09-01"
    end = "2023-12-31"

    try:
        worst = finder.find_worst_attendees(class_ids, top_n=10, start_date=start, end_date=end)
        if worst:
            print("\n10 студентов с худшей посещаемостью:")
            for idx, rec in enumerate(worst, 1):
                print(f"{idx}. {rec['studentName']} — {rec['attendancePercent']}% ({rec['attendedCount']}/{rec['totalCount']})")
        else:
            print("Нет данных о посещаемости.")

    finally:
        finder.close()