from time import sleep
from sync.mongo import create_mongo
from data_generator import seed_database
from database_check_data import check_database_data_simple
from clean_postgres import drop_tables
from sync.redis import create_redis
from sync.elastic import create_elastic
from setup_postgre_tables import setup_tables


if __name__ == "__main__":
    drop_tables()
    setup_tables()
    sleep(5)
    seed_database()
    sleep(5)
    check_database_data_simple()
    create_elastic.main()
    create_mongo.main()
    create_redis.main()
