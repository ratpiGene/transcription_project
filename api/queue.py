from rq import Queue
from redis import Redis

from api.settings import REDIS_URL


def get_queue() -> Queue:
    redis_conn = Redis.from_url(REDIS_URL)
    return Queue("transcription", connection=redis_conn, default_timeout=3600)
