import os
import environ
from pathlib import Path


# This sets the base directory of your project so you can refer to files easily
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()

environ.Env.read_env(
    os.path.join(BASE_DIR, '.env')
)

SECRET_KEY = env("SECRET_KEY")

# Debug mode means you see detailed error messages, only use in development
DEBUG = True

# Hosts/domain names that this Django site can serve
ALLOWED_HOSTS = []

# Installed apps - these are all the apps Django will use in your project
INSTALLED_APPS = [
    'django.contrib.admin',        # Admin site
    'django.contrib.auth',         # User authentication system
    'django.contrib.contenttypes',  # Content type framework
    'django.contrib.sessions',     # Session framework
    'django.contrib.messages',     # Message framework
    'django.contrib.staticfiles',  # Manage static files like CSS and JS
    'grabsomore',                  # Your custom app for auth
    'eCommerce',                   # Your custom app for eCommerce
]

# Middleware are layers that process requests/responses, like security and
# session management
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # Protects against CSRF attacks
    'django.middleware.csrf.CsrfViewMiddleware',
    # Adds user info to requests
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Prevents clickjacking attacks
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Root URL configuration points to the main urls.py
ROOT_URLCONF = 'AuthLog.urls'

# Template settings for locating and processing HTML files
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # You can add folders here if you keep templates outside apps
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Adds the 'request' object to templates
                'django.template.context_processors.request',
                # Adds user info to templates
                'django.contrib.auth.context_processors.auth',
                # Adds the message framework to templates
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI application: Entry point for WSGI-compatible web servers
WSGI_APPLICATION = 'AuthLog.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
    }
}


# Password validation helps make sure passwords are strong and safe
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'UserAttributeSimilarityValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.MinimumLengthValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.CommonPasswordValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.NumericPasswordValidator'
        ),
    },
]

# Internationalization settings (language and timezone)
LANGUAGE_CODE = 'en-us'  # English (United States)
TIME_ZONE = 'UTC'        # Coordinated Universal Time
USE_I18N = True          # Enable internationalization
USE_TZ = True            # Use timezone-aware datetimes

# Static files (CSS, JavaScript, images) URL prefix
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
# Default primary key type for models
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email settings to send emails (for example, password reset emails)
# You can switch to console backend for testing emails in your terminal
# instead of sending real emails
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# Use SMTP server to send real emails
EMAIL_FILE_PATH = "/emails/"  # Path to save emails if using file backend
EMAIL_HOST = 'smtp.gmail.com'  # Gmail SMTP server
EMAIL_PORT = 587  # SMTP port for TLS
EMAIL_USE_TLS = True  # Use TLS for security
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
LOGIN_URL = 'grabsomore:login'
