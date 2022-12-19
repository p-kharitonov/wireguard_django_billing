"""
Default settings for `bot` package.
"""
from django.conf import settings
from billing.settings import CURRENCY

WEB_LOGIN = getattr(settings, 'WEB_LOGIN', 'admin')
WEB_PASSWORD = getattr(settings, 'WEB_PASSWORD', 'admin')
TELEGRAM_USERBOT_TOKEN = getattr(settings, 'TELEGRAM_USERBOT_TOKEN', None)
TELEGRAM_ADMINBOT_TOKEN = getattr(settings, 'TELEGRAM_ADMINBOT_TOKEN', None)
TELEGRAM_ADMIN_ID = getattr(settings, 'TELEGRAM_ADMIN_ID', None)
PHONE_NUMBER = getattr(settings, 'PHONE_NUMBER', None)
CURRENCY = CURRENCY
URL_API = getattr(settings, 'URL_API', 'http://127.0.0.1:8000/api/')
