import redis
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisTool:
    def __init__(self):
        self.client = None
        self.connect()
    
    def connect(self):
        try:
            self.client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'redis'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                password=os.getenv('REDIS_PASSWORD', ''),
                db=0,
                decode_responses=True
            )
            if self.client.ping():
                logger.info("Connected to Redis")
            else:
                raise ConnectionError("Redis connection failed")
        except Exception as e:
            logger.error(f"Redis connection error: {str(e)}")
            raise
    
    def get_student_count(self, course_id):
        try:
            key = f"course:{course_id}:students"
            count = self.client.get(key)
            return int(count) if count else None
        except Exception as e:
            logger.error(f"Redis get error: {str(e)}")
            return None
    
    def set_student_count(self, course_id, count):
        try:
            key = f"course:{course_id}:students"
            self.client.set(key, count, ex=3600)  # Кэш на 1 час
            logger.info(f"Set Redis cache for {key}: {count}")
        except Exception as e:
            logger.error(f"Redis set error: {str(e)}")
    
    def close(self):
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")
    
    def __del__(self):
        self.close()