from elasticsearch import Elasticsearch
import psycopg2
from typing import Dict, List
import json
from env import (DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT,
                 DB_USER)


def sync_lecture_sessions(
    es_host: str = "localhost",
    es_port: int = 9200,
    es_user: str = "elastic",
    es_password: str = "secret"
) -> None:
    """
    Sync lecture sessions data from PostgreSQL to Elasticsearch
    """
    pg_conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    pg_cur = pg_conn.cursor()
    es = Elasticsearch(
        hosts=[f"http://{es_host}:{es_port}"],
        basic_auth=(es_user, es_password),
        verify_certs=False
    )

    try:
        # Create Elasticsearch index for lecture sessions
        if not es.indices.exists(index="lecture_sessions"):
            es.indices.create(
                index="lecture_sessions",
                mappings={
                    "properties": {
                        "session_id": {"type": "integer"},
                        "topic": {
                            "type": "text",
                            "analyzer": "russian",
                            "fields": {"keyword": {"type": "keyword"}}
                        },
                        "description": {"type": "text", "analyzer": "russian"},
                        "duration_minutes": {"type": "integer"},
                        "course_name": {"type": "text", "analyzer": "russian"},
                        "session_type_id": {"type": "integer"},
                        "tags": {"type": "object"}
                    }
                }
            )

        # Get lecture sessions data with session type name
        pg_cur.execute("""
            SELECT
                ls.session_id,
                ls.topic,
                ls.description,
                ls.duration_minutes,
                ls.tags,
                c.name,
                ls.session_type_id
            FROM Lecture_Sessions ls
            JOIN Courses c ON ls.course_id = c.course_id
        """)
        sessions = pg_cur.fetchall()

        for session in sessions:
            session_id = session[0]

            # Parse JSON tags
            try:
                tags = json.loads(session[4]) if session[4] else {}
            except:
                tags = {}

            doc = {
                "session_id": session_id,
                "topic": session[1],
                "description": session[2],
                "duration_minutes": session[3],
                "tags": tags,
                "course_name": session[5],
                "session_type_id": session[6]
            }

            es.index(
                index="lecture_sessions",
                id=session_id,
                document=doc
            )

        print(f"Synced {len(sessions)} lecture sessions")
        es.indices.refresh(index="lecture_sessions")

    except Exception as e:
        print(f"Error during synchronization: {e}")
        raise
    finally:
        pg_cur.close()
        pg_conn.close()
        es.close()


class LectureSessionSearcher:
    def __init__(self, es_host="localhost", es_port=9200, es_user="elastic", es_password="secret"):
        self.es = Elasticsearch(
            hosts=[f"http://{es_host}:{es_port}"],
            basic_auth=(es_user, es_password),
            verify_certs=False
        )

    def search(self, query: str) -> List[Dict]:
        """
        Full-text search across topic, description and tags
        """
        response = self.es.search(
            index="lecture_sessions",
            query={
                "multi_match": {
                    "query": query,
                    "fields": ["course_name^3", "topic^3", "description^2", "tags"],
                    "type": "best_fields"
                }
            }
        )

        return self._format_results(response)

    def search_by_type(self, session_type_id: int) -> List[Dict]:
        """
        Search by session type (exact match)
        """
        response = self.es.search(
            index="lecture_sessions",
            query={
                "term": {
                    "session_type.keyword": session_type_id
                }
            }
        )
        return self._format_results(response)

    def search_by_duration(self, min_duration: int, max_duration: int) -> List[Dict]:
        """
        Search sessions in duration range
        """
        response = self.es.search(
            index="lecture_sessions",
            query={
                "range": {
                    "duration_minutes": {
                        "gte": min_duration,
                        "lte": max_duration
                    }
                }
            }
        )
        return self._format_results(response)

    def _format_results(self, response):
        return [{
            "session_id": hit["_source"]["session_id"],
            "topic": hit["_source"]["topic"],
            "description": hit["_source"]["description"],
            "duration": hit["_source"]["duration_minutes"],
            "session_type_id": hit["_source"]["session_type_id"],
            "course_name": hit["_source"]["course_name"],
            "tags": hit["_source"]["tags"]
        } for hit in response["hits"]["hits"]]


def main():
    sync_lecture_sessions()

    searcher = LectureSessionSearcher()

    print("\nПример поиска по ключевому слову 'Уголовное':")
    results = searcher.search("уголовное")
    for res in results:
        print(f"\nID: {res['session_id']}")
        print(f"Тема: {res['topic']}")
        print(f"Курс: {res['course_name']}")
        print(f"Тип: {res['session_type_id']}")
        print(
            f"Теги: {', '.join(res['tags'].keys()) if res['tags'] else 'нет'}")

    print("\nПоиск лекций длительностью 80-120 минут:")
    results = searcher.search_by_duration(80, 120)
    for res in results:
        print(f"{res['topic']} ({res['duration']} минут)")


if __name__ == "__main__":
    main()
