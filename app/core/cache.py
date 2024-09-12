import os
from redis import Redis

USE_REDIS = os.environ.get('USE_REDIS', 'True').lower() == 'true'

if USE_REDIS:
    redis_client = Redis(host='localhost', port=6379, db=0)
else:
    redis_client = None
