"""
Django testing settings for ColdMail project.
"""

from .base import *

DEBUG = False

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Database - SQLite in memory for fast tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Password hasher - faster for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable email verification in tests
ACCOUNT_EMAIL_VERIFICATION = 'none'

# Celery - eager mode for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
