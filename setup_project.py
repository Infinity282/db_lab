from time import sleep
from db_utils.postgres.drop_postgres_tables import drop_tables
from db_utils.postgres.create_postgres_tables import create_tables
from db_utils.postgres.generate_postgres_data import seed_database
from db_utils.postgres.check_postgres_tables import check_tables
from db_utils.elastic.sync_elastic_tables import sync_lecture_sessions
from db_utils.mongo.sync_mongo_tables import sync_university_hierarchy
from db_utils.redis.sync_redis_tables import sync_session_types_to_redis


if __name__ == "__main__":
    drop_tables()
    create_tables()
    sleep(5)
    seed_database()
    sleep(5)
    check_tables()
    sync_lecture_sessions
    sync_university_hierarchy()
    sync_session_types_to_redis()
