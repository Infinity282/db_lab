from time import sleep
from db_utils.postgres.drop_postgres_tables import drop_tables
from db_utils.postgres.create_postgres_tables import create_tables
from db_utils.postgres.generate_postgres_data import insert_data
from db_utils.postgres.check_postgres_tables import check_tables
from db_utils.elastic.sync_elastic_tables import ElasticLectureSessionSynchronizer
from db_utils.mongo.sync_mongo_tables import MongoSynchronizer
from db_utils.redis.sync_redis_tables import RedisStudentSynchronizer
from db_utils.neo4j.sync_neo4j_tables import Neo4jSynchronizer

if __name__ == "__main__":
    drop_tables()
    sleep(1)
    create_tables()
    sleep(2)
    insert_data()
    sleep(2)
    check_tables()

    mongo_sync = MongoSynchronizer()
    if not mongo_sync.run_sync():
        print("Синхронизация MongoDB завершена с ошибками")

    redis_sync = RedisStudentSynchronizer()
    if not redis_sync.run_sync():
        print("Синхронизация Redis завершена с ошибками")

    elastic_sync = ElasticLectureSessionSynchronizer()
    if not elastic_sync.run_sync():
        print("Синхронизация Elastic завершена с ошибками")

    neo4j_sync = Neo4jSynchronizer()
    if not neo4j_sync.run_sync():
        print("Синхронизация Neo4j завершена с ошибками")
