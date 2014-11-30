"""
Django settings for imagr_site project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# settings for MailGun email
import credentials
credentials.set_credentials()
EMAIL_HOST = os.environ['EMAIL_HOST']
EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
EMAIL_PORT = 25

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

import deployment
deployment.setup_deployment()
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ['DEBUG']

TEMPLATE_DEBUG = os.environ['TEMPLATE_DEBUG']

ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS']

CONN_MAX_AGE = os.environ['CONN_MAX_AGE']

# set up in deployment.py now
# ALLOWED_HOSTS = []
# CONN_MAX_AGE = 60

# Application definition
LOGIN_REDIRECT_URL = "imagr_app:front_page"

#LOGIN_URL = "RegistrationView"

#LOGOUT_URL

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'imagr_app',
    'registration',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'imagr_site.urls'

WSGI_APPLICATION = 'imagr_site.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'imagr',
        'USER': 'imagr',
        'PASSWORD': os.environ['DATABASE_PASSWORD'],
        'HOST': 'localhost',
    }
}
# Thanks to Hybrid at:
# http://stackoverflow.com/questions/21978562/django-test-error-permission-denied-to-create-database-using-heroku-postgres
import sys
if 'test' in sys.argv:
    DATABASES['default'] = {'ENGINE': 'django.db.backends.sqlite3'}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Los_Angeles'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'

AUTH_USER_MODEL = 'imagr_app.ImagrUser'

#LOGIN_URL = "/"

ACCOUNT_ACTIVATION_DAYS = 60



# These variables are set this way for deployment (overwriting values
#  set above (like DEBUG="True")

STATIC_ROOT = "static/"

MEDIA_ROOT = "media/"



    # There is a risk that the greater security of setting
    #  these to True will not work unless we get an SSL
    #  certificate, and we don't know yet whether Amazon EC2
    #  will give us a certificate or let us use one of theirs

# CSRF_COOKIE_SECURE = "True"

# SESSION_COOKIE_SECURE = "True"

    # Performance Optimizations


