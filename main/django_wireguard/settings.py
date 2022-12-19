"""
Default settings for `django_wireguard` package.
"""
from django.conf import settings

WIREGUARD_ENDPOINT = getattr(settings, 'WIREGUARD_ENDPOINT', 'localhost')
"""The endpoint for the peer configuration. Set it to the server Public IP address or domain."""

WIREGUARD_STORE_PRIVATE_KEYS = getattr(settings, 'WIREGUARD_STORE_PRIVATE_KEYS', True)
"""Set this option to False to prevent storing peer private keys in the database."""

WIREGUARD_WAGTAIL_SHOW_IN_SETTINGS = getattr(settings, 'WIREGUARD_WAGTAIL_SHOW_IN_SETTINGS', True)
"""Set this to False to show WireGuard models in root sidebar instead of settings panel."""

WIREGUARD_OUTPUT_INTERFACE = getattr(settings, 'WIREGUARD_OUTPUT_INTERFACE', 'eth0')
