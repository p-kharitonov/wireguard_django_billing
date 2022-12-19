from typing import Union, Optional

from django.db.models import QuerySet

from django_wireguard.models import WireguardInterface


def sync_wireguard_interfaces(queryset: Optional[Union[QuerySet, WireguardInterface]] = None):
    """
    Sync database WireguardInterface queryset or instance to WireGuard devices on the system.

    :param queryset: WireguardInterfaces to sync with the system
    :type queryset: WireguardInterface queryset or instance
    """
    if queryset is None:
        queryset = WireguardInterface.objects.all()
    elif isinstance(queryset, WireguardInterface):
        queryset = [queryset]

    for interface in queryset:
        interface.wg.set_interface(private_key=interface.private_key,
                                   listen_port=interface.listen_port)

        if interface.addresses:
            interface.wg.set_ip_addresses(interface.get_address_list())

        for address in interface.addresses.all():
            for peer in address.peers.all():
                if not peer.status:
                    continue
                # update/create the wireguard peer
                interface.wg.set_peer(peer.public_key, peer.preshared_key,
                                      peer.get_interface_allowed_ip())
