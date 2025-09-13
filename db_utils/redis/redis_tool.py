import redis
import logging
from env import REDIS_HOST, REDIS_PORT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RedisTool:
    def __init__(self, host=REDIS_HOST):
        self.client = None
        self.host = host
        self.connect()

    def connect(self):
        try:
            self.client = redis.Redis(
                host=self.host,
                port=REDIS_PORT,
                decode_responses=True
            )
            if self.client.ping():
                logger.info("Connected to Redis")
            else:
                raise ConnectionError("Redis connection failed")
        except Exception as e:
            logger.error(f"Redis connection error: {str(e)}")
            raise

    def get_students_info_by_group_id(self, group_id: int):
        """
        Получает список студентов по ID группы

        :param group_id: ID группы
        :return: Список ID студентов или пустой список, если группа не найдена
        """
        try:
            index_key = f"index:student:group_id:{group_id}"

            if not self.client.exists(index_key):
                logger.warning(f"Индекс группы {group_id} не найден в Redis")
                return []

            student_ids = self.client.smembers(index_key)

            pipe = self.client.pipeline()
            for sid in student_ids:
                pipe.hgetall(f"student:{sid}")
            students_data = pipe.execute()

            result = []
            for data in students_data:
                if data:
                    data["id"] = int(data["id"])
                    data["group_id"] = int(data.get("group_id", 0))
                    result.append(data)

            result.sort(key=lambda x: x["id"])
            logger.info(f"Получены данные студента {group_id} из Redis")
            logger.info(f"Студент: {result}")

            return result

        except Exception as e:
            logger.error(
                f"Ошибка при получении студентов группы {group_id}: {str(e)}")
            return []

    def get_student_count_by_group_id(self, group_id: int):
        """
        Получает количество студентов по ID группы

        :param group_id: ID группы
        :return: Количество студентов или 0, если группа не найдена
        """
        try:
            index_key = f"index:student:group_id:{group_id}"

            if not self.client.exists(index_key):
                logger.warning(f"Индекс группы {group_id} не найден в Redis")
                return 0

            # Получаем количество студентов в множестве
            student_count = self.client.scard(index_key)

            logger.info(
                f"В группе {group_id} найдено {student_count} студентов")
            return student_count

        except Exception as e:
            logger.error(
                f"Ошибка при подсчете студентов группы {group_id}: {str(e)}")
            return 0

    def close(self):
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")

    def __del__(self):
        self.close()


def main():
    redis_tool = RedisTool()
    # Получаем данные студента
    student = redis_tool.get_student_info(student_id=8)

    if student:
        print(
            f"\nИнформация о студенте:\n"
            f"{'-'*50}\n"
            f"{'ID:':<15} {student['id']}\n"
            f"{'Группа ID:':<15} {student['group_id']}\n"
            f"{'ФИО:':<15} {student['name']}\n"
            f"{'Год поступления:':<15} {student['enrollment_year']}\n"
            f"{'Дата рождения:':<15} {student['date_of_birth']}\n"
            f"{'Email:':<15} {student['email']}\n"
            f"{'Номер зачётки:':<15} {student['book_number']}\n"
            f"{'-'*50}"
        )
    else:
        print("Студент не найден")


if __name__ == "__main__":
    main()
