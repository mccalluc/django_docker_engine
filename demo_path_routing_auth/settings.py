import django

from .settings_common import *  # noqa: F403
from .utils import hostname

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': False,
        'DIRS': [__package__]
    },
]

STATIC_URL = '/static/'

ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1', hostname()]
# hostname() allows the docker containers to
# get files from the upload directory on this server.


auth_middleware = shared_middleware + (    # noqa: F405
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware')
if django.VERSION >= (2, 0):
    MIDDLEWARE = auth_middleware
else:
    MIDDLEWARE_CLASSES = auth_middleware

AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'database.sqlite',
    }
}

INSTALLED_APPS = INSTALLED_APPS + (  # noqa: F405
    'django.contrib.auth',
    'django.contrib.contenttypes'
)
