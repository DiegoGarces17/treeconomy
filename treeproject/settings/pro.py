import os
from .base import *

import environ
env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

SECRET_KEY = os.environ['SECRET_KEY']
DEBUG = False

ALLOWED_HOSTS = ["treeconomyapp.herokuapp.com"]
CSRF_TRUSTED_ORIGINS = ['https://treeconomyapp.herokuapp.com']

STATIC_ROOT = os.path.join(BASE_DIR , "static")

DATABASES = {
        'default': {
        'ENGINE': 'djongo',
        'NAME': 'treeconomy_pro',
        'HOST': os.environ['DB_HOST_PRO'],
    }
}

EMAIL_HOST = os.environ['EMAIL_HOST']
EMAIL_PORT = os.environ['EMAIL_PORT']
EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
EMAIL_USE_TLS =  os.environ['EMAIL_USE_TLS']
DEFAULT_FROM_EMAIL = 'alejocruzzz@gmail.com'

SOCIAL_AUTH_FACEBOOK_KEY= os.environ['SOCIAL_AUTH_FACEBOOK_KEY']
SOCIAL_AUTH_FACEBOOK_SECRET= os.environ['SOCIAL_AUTH_FACEBOOK_SECRET']

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY= os.environ['SOCIAL_AUTH_GOOGLE_OAUTH2_KEY']
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET= os.environ['SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET']