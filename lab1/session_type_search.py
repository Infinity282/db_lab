from typing import Dict, List
import redis

class SessionTypeSearch:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.r = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True)

    def get_by_id(self, session_type_id: str) -> Dict:
        """Получить тип занятия по ID"""
        return self.r.hgetall(f"class_type:{session_type_id}")

    def get_by_name(self, name: str) -> List[Dict]:
        """Поиск по точному названию типа занятия"""
        session_ids = self.r.smembers(f"index:class_type:name:{name.lower()}")
        return [self.r.hgetall(f"class_type:{id}") for id in session_ids]