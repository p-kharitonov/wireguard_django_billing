from django.apps import AppConfig
from django.db import DatabaseError


class DjangoWireguardConfig(AppConfig):
    name = 'django_wireguard'
    verbose_name = "Django WireGuard"

    # def ready(self):
    #     """
    #     Sync WireGuard interfaces with system's.
    #
    #     Does nothing if any DatabaseError arises.
    #     """
    #     from django_wireguard.sync_wg import sync_wireguard_interfaces
    #     try:
    #         sync_wireguard_interfaces()
    #     except DatabaseError:
    #         pass

