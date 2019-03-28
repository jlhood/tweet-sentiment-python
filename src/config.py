"""Environment configuration values used by lambda functions."""

import os

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
SEARCH_TEXT = os.getenv('SEARCH_TEXT')
