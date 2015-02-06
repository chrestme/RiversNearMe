"""
Django settings for RiversNearMe project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
with open('/etc/rivers_django_secret.key') as f:
	SECRET_KEY = f.read().strip()
#SECRET_KEY = 'l-l*fj_a6!0gwozejlk0f!1a1a#^occitm=sn^)15^tm29w0v%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
TEMPLATE_DEBUG = False
CRISPY_FAIL_SILENTLY = not DEBUG

ALLOWED_HOSTS = ['www.riversnearme.com',
		 'riversnearme.com',
		 'riversnear.me',
		 'www.riversnear.me',
		 '54.84.44.58']

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

SITE_ID = 1

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sites',
    #'django.contrib.comments',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'crispy_forms',
    'tagging',
    'mptt',
    'zinnia',
    'registration',
    'Rivers',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
  'django.contrib.auth.context_processors.auth',
  'django.core.context_processors.i18n',
  'django.core.context_processors.request',
  'django.core.context_processors.static',
  'zinnia.context_processors.version',  # Optional
)

TEMPLATE_LOADERS = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
    'app_namespace.Loader',
]

ROOT_URLCONF = 'RiversNearMe.urls'

WSGI_APPLICATION = 'RiversNearMe.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db/placemark.db'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

CRISPY_TEMPLATE_PACK = 'bootstrap3'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/RiversNearMe/static/' #'/opt/RiversNearMe/RiversNearMe/static/'
STATICFILES_DIRS = ( os.path.join(BASE_DIR, "static"), )

LOGIN_REDIRECT_URL = '/'
ACCOUNT_ACTIVATION_DAYS = 7

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'riversnearme@gmail.com'
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_USE_TLS = True
with open('/etc/rivers_gmail.key', 'r') as gk:
    EMAIL_HOST_PASSWORD = gk.read().strip()

SERVER_EMAIL = 'webmaster@riversnearme.com'
ADMINS = (('Admin','riversnearme@gmail.com'),)

#ZINNIA_AUTO_MODERATE_COMMENTS = True
ZINNIA_SPAM_CHECKER_BACKENDS = ('zinnia.spam_checker.backends.automattic',
				'zinnia_akismet.akismet',)
with open('/etc/rivers_akismet.key','r') as ak:
	AKISMET_SECRET_API_KEY = ak.read().strip()
	AKISMET_API_KEY = AKISMET_SECRET_API_KEY
