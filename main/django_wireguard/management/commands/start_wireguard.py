from django.core.management.base import BaseCommand

from django_wireguard.models import WireguardInterface


class Command(BaseCommand):
    help = 'Start WireGuard interfaces'

    def handle(self, *args, **options):
        for interface in WireguardInterface.objects.all():
            interface.wg.set_interface(private_key=interface.private_key,
                                       listen_port=interface.listen_port)
            interface.wg.set_ip_addresses(interface.get_address_list())
            self.stderr.write(self.style.SUCCESS(f"Interface started: {interface.name}.\n"))
            for address in interface.addresses.all():
                for peer in address.peers.all():
                    if not peer.status:
                        continue
                    # update/create the wireguard peer
                    interface.wg.set_peer(peer.public_key, peer.preshared_key,
                                          peer.get_interface_allowed_ip())
                    self.stderr.write(self.style.SUCCESS(f"Peer added successfully: {peer.name}.\n"))



