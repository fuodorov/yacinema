import os
from logging import config as logging_config

from core.logger import LOGGING

logging_config.dictConfig(LOGGING)

PROJECT_NAME = 'Movies Async API v1'

CACHE_EXPIRATION = 60 * 5

PAGE_SIZE = 50

TIME_LIMIT = 5

REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

ELASTIC_HOST = os.getenv('ELASTICSEARCH_HOST', '127.0.0.1')
ELASTIC_PORT = int(os.getenv('ELASTICSEARCH_PORT', 9200))

AUTH_HOST = os.getenv('AUTH_HOST', '127.0.0.1')
AUTH_PORT = int(os.getenv('AUTH_PORT', 5000))
AUTH_TOKEN_VALIDATION_URL = 'http://{host}:{port}/auth/v1/auth_token/validation'.format(host=AUTH_HOST,
                                                                                        port=AUTH_PORT)
AUTH_PERMISSIONS_AND_TOKEN_VALIDATION_URL = \
    'http://{host}:{port}/auth/v1/users/{{user_id}}/combined_permissions/validation'.format(host=AUTH_HOST,
                                                                                            port=AUTH_PORT)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
