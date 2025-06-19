import psycopg2
import redis
from env import (DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT,
                 DB_USER, REDIS_HOST, REDIS_PORT)
from typing import Dict, List


class RedisSessionManager:
    """Класс для работы с сессиями в Redis"""

    def __init__(self):
        self.redis = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )
        self.pg_conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

    def sync_session_types(self) -> None:
        """Основной метод синхронизации"""
        print("Синхронизация типов сессий из PostgreSQL в Redis")

        with self.pg_conn.cursor() as pg_cur:
            try:
                self._clear_redis_data()
                session_types = self._fetch_session_types(pg_cur)
                self._store_in_redis(session_types)
                print(
                    f"Успешно синхронизировано {len(session_types)} типов сессий")

            except Exception as e:
                self.pg_conn.rollback()
                print(f"Ошибка синхронизации: {e}")
                raise

    def _clear_redis_data(self) -> None:
        """Очистка старых данных в Redis"""
        for key in self.redis.scan_iter("session_type:*"):
            self.redis.delete(key)
        for key in self.redis.scan_iter("index:session_type:*"):
            self.redis.delete(key)

    def _fetch_session_types(self, cursor) -> List[tuple]:
        """Получение типов сессий из PostgreSQL"""
        cursor.execute("SELECT session_type_id, name FROM Session_Types")
        return cursor.fetchall()

    def _store_in_redis(self, session_types: List[tuple]) -> None:
        """Сохранение данных в Redis"""
        for session_type_id, name in session_types:
            session_key = f"session_type:{session_type_id}"
            self.redis.hset(session_key, mapping={
                'id': session_type_id,
                'name': name
            })
            self.redis.sadd(
                f"index:session_type:name:{name.lower()}", session_type_id)

    def get_by_id(self, session_type_id: int) -> Dict:
        """Получить тип сессии по ID"""
        return self.redis.hgetall(f"session_type:{session_type_id}")

    def get_by_name(self, name: str) -> List[Dict]:
        """Поиск по точному названию типа"""
        session_ids = self.redis.smembers(
            f"index:session_type:name:{name.lower()}")
        return [self.redis.hgetall(f"session_type:{id}") for id in session_ids]

    def close(self):
        """Закрытие соединений"""
        self.pg_conn.close()
        self.redis.close()


if __name__ == "__main__":
    manager = RedisSessionManager()
    try:
        manager.sync_session_types()
        print("Пример лекций:", manager.get_by_name("Лекция"))
    finally:
        manager.close()
