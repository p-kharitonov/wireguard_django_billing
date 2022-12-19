"""
Default settings for `billing` package.
"""
from django.conf import settings

PAYMENTS_START_TIME = getattr(settings, 'PAYMENTS_START_TIME', '2022-11-06T13:45:16Z')
CURRENCY = getattr(settings, 'CURRENCY', 'RUB')
