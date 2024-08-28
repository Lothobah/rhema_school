import environ
from pathlib import Path
import os
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
LOGIN_URL = 'login'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-8x8u%x6es+gp&!eexrn$vhec6@-2sdkw7rzntrfx90f%4iq22-'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['kingloth.pythonanywhere.com', '127.0.0.1']
# Application definition
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR,'media')

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'great_alliance_portal',
    'crispy_forms',
    'django.contrib.humanize', #adds comma to a thousand
    'django.contrib.sitemaps',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'great_alliance_portal.LoginCheckMiddleWare.LoginCheckMiddleWare',
    'great_alliance_portal.middleware.AutoLogoutMiddleware',
]

ROOT_URLCONF = 'great_alliance_management_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['great_alliance_portal/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'great_alliance_management_system.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
'''
DATABASES = {

    'default': {

        'ENGINE': 'django.db.backends.postgresql_psycopg2',

        'NAME': 'king-loth',

        'USER': 'postgres',

        'PASSWORD': 'King@Loth$123',

        'HOST': 'localhost',

        'PORT': '5432',

    }

}
'''
DATABASES = {
    'default':{
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
STATIC_URL ='/static/'
AUTH_USER_MODEL = "great_alliance_portal.CustomUser"
AUTHENTICATION_BACKENDS =['great_alliance_portal.EmailBackEnd.EmailBackEnd']

#EMAIL_BACKEND="django.core.mail.backends.filebased.EmailBackend"
#EMAIL_FILE_PATH=os.path.join(BASE_DIR,"sent_mails")
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#added.
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Initialize environment variables
env = environ.Env()
environ.Env.read_env(env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
#gmail smtp
EMAIL_HOST="smtp.gmail.com"
#EMAIL_PORT=587
EMAIL_PORT=465
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
#I added the below code
EMAIL_USE_SSL = True
EMAIL_USE_TLS=False
DEFAULT_FROM_EMAIL="Great Alliance Preparatory/JHS"
ADMIN_EMAIL = "lothobah@gmail.com" #email to receive approval notification.
import logging
logger = logging.getLogger('django')
logger.setLevel(logging.DEBUG)
# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# Session timeout in seconds (e.g., 30 sec)
SESSION_COOKIE_AGE = 1020

