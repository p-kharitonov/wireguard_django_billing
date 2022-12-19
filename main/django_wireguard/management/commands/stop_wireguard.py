from django.core.management.base import BaseCommand

from django_wireguard.models import WireguardInterface
from django_wireguard.signals import interface_deleted


class Command(BaseCommand):
    help = 'Start WireGuard interfaces'

    def handle(self, *args, **options):
        for interface in WireguardInterface.objects.all():
            interface.wg.delete()
            interface_deleted.send(WireguardInterface, instance=interface)




