# Django settings for elcid project.
import os
import sys

PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))

try:
    import dj_database_url

    DATABASES = {
        'default': dj_database_url.config(default='sqlite:///' + PROJECT_PATH + '/opal.sqlite')
    }
except ImportError:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(PROJECT_PATH, 'opal.sqlite'),
            'USER': '',
            'PASSWORD': '',
            'HOST': '',
            'PORT': '',
        }
    }

DEBUG = True
TEMPLATE_DEBUG = DEBUG
AUTOCOMPLETE_SEARCH = True

ADMINS = (
    ('Support', 'support@openhealthcare.org.uk',),
)

MANAGERS = ADMINS


# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'ec2-52-16-175-249.eu-west-1.compute.amazonaws.com',
    '.openhealthcare.org.uk',
    '.herokuapp.com'
    ]

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = 'static'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/assets/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(PROJECT_PATH, 'assets'),
)

# List of finder classes that know how to find static files in
# various locations
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
    'compressor.finders.CompressorFinder',
)

# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.CachedStaticFilesStorage'
# if 'test' in sys.argv:
#     STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'hq6wg27$1pnjvuesa-1%-wiqrpnms_kx+w4g&&o^wr$5@stjbu'

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'opal.middleware.AngularCSRFRename',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'opal.middleware.DjangoReversionWorkaround',
    'reversion.middleware.RevisionMiddleware',
#    'axes.middleware.FailedLoginMiddleware',
    'elcid.middleware.LoggingMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'elcid.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'elcid.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_PATH, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'opal.context_processors.settings',
                'opal.context_processors.models',
                'elcid.context_processors.permissions',
                'lab.context_processors.lab_tests',
            ],
        },
    },
]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'axes',
    'reversion',
    'apps.tb',
    'opal',
    'opal.core.pathway',
    'rest_framework',
    'rest_framework.authtoken',
    'compressor',
    'opal.core.search',
    'lab',
    'plugins.letters',
    'plugins.labtests',
    'intrahospital_api',
    'elcid',
    'django.contrib.admin',
    'djcelery',
    'obs',
)

#### API Settings

# The intrahospital api is what we use to connect to the rest of the hospital
INTRAHOSPITAL_API = 'intrahospital_api.apis.dev_api.DevApi'

# when running the batch load, this user needs to be set
API_USER = "needs to be set"

# this needs to be set to true on prod
ASYNC_API = False

# if the intrahospital api is prod, we need
# an ip address, a database, a username and a password for
# the hospital db
HOSPITAL_DB = dict(
    ip_address=None,
    database=None,
    username=None,
    password=None,
    view=None
)


# search with external demographics when adding a patient
ADD_PATIENT_DEMOGRAPHICS = True

# after we've added a patient, should we load in the labtests?
ADD_PATIENT_LAB_TESTS = True

#### END API Settings

if 'test' in sys.argv:
    INSTALLED_APPS += ('lab.tests',)
    PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.MD5PasswordHasher',
    )

V_FORMAT = '%(asctime)s %(process)d %(thread)d %(filename)s %(funcName)s \
%(levelname)s %(message)s'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': V_FORMAT
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': [],
            'class': 'logging.StreamHandler',
        },
        'console_detailed': {
            'level': 'INFO',
            'filters': [],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'opal.core.log.ConfidentialEmailer'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'elcid.requestLogger': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'error_emailer': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'intrahospital_api': {
            'handlers': ['console_detailed', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}

if 'test' not in sys.argv:
    LOGGING['loggers']['elcid.time_logger'] = {
        'handlers': ['console_detailed'],
        'level': 'INFO',
        'propagate': False,
    }

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
# (Heroku requirement)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

DATE_FORMAT = 'd/m/Y'
DATE_INPUT_FORMATS = ['%d/%m/%Y']
DATETIME_FORMAT = 'd/m/Y H:i:s'
DATETIME_INPUT_FORMATS = ['%d/%m/%Y %H:%M:%S']

CSRF_COOKIE_NAME = 'XSRF-TOKEN'
APPEND_SLASH = False

AXES_LOCK_OUT_AT_FAILURE = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# New modular settings!
# !!! TODO: Are these how we want to discover these ?
OPAL_OPTIONS_MODULE = 'elcid.options'
OPAL_BRAND_NAME = 'elCID Royal Free Hospital'
OPAL_LOG_OUT_MINUTES = 15
OPAL_LOG_OUT_DURATION = OPAL_LOG_OUT_MINUTES*60*1000

# Do we need this at all ?
OPAL_EXTRA_HEADER = 'elcid/print_header.html'

# ANALYTICS Settings
OPAL_ANALYTICS_ID = 'UA-XXXXXXX'
OPAL_ANALYTICS_NODOMAIN = True

CONTACT_EMAIL = ['david@openhealthcare.org.uk']
DEFAULT_FROM_EMAIL = 'elcid@openhealthcare.org.uk'
DEFAULT_DOMAIN = 'http://ELCIDL/'

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
if not DEBUG:
    EMAIL_HOST_USER = os.environ.get('SENDGRID_USERNAME', '')
    EMAIL_HOST= 'smtp.sendgrid.net'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_PASSWORD', '')
else:
    EMAIL_PORT = 1025
    EMAIL_HOST = 'localhost'


VERSION_NUMBER = '0.16'

#TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
#TEST_RUNNER = 'django_test_coverage.runner.CoverageTestSuiteRunner'

COVERAGE_EXCLUDE_MODULES = ('elcid.migrations', 'elcid.tests',
                            'elcid.settings',
                            'elcid.local_settings',
                            'opal.migrations', 'opal.tests',
                            'opal.wsgi')



# The intrahospital api is what we use to connect to the rest of the hospital
INTRAHOSPITAL_API = 'intrahospital_api.apis.dev_api.DevApi'

# search with external demographics when adding a patient
USE_UPSTREAM_DEMOGRAPHICS = True

# if the intrahospital api is prod, we need
# an ip address, a database, a username and a password for
# the hospital db
HOSPITAL_DB = dict(
    ip_address=None,
    database=None,
    username=None,
    password=None,
    view=None
)


EXTRACT_ASYNC = False


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    )
}

if 'test' not in sys.argv:
    try:
        from elcid.local_settings import *
    except ImportError:
        pass
