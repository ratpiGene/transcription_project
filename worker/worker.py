import os
from redis import Redis
from rq import Worker, Queue, Connection

from api.settings import REDIS_URL


if __name__ == "__main__":
    redis_conn = Redis.from_url(REDIS_URL)
    with Connection(redis_conn):
        worker = Worker([Queue("transcription")])
        worker.work()
