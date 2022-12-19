from ipaddress import IPv4Interface
from os import system
from datetime import datetime
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from django_wireguard import settings
from django_wireguard.signals import interface_created, interface_deleted
from django_wireguard.utils import clean_comma_separated_str
from django_wireguard.validators import validate_private_ipv4, validate_wireguard_private_key, \
    validate_wireguard_preshared_key, validate_allowed_ips, validate_allowed_networks, \
    validate_allowed_private_ip_interface
from django_wireguard.wireguard import WireGuard, PrivateKey


__all__ = ('WireguardInterface', 'WireguardPeer',
           'WireguardDNS', 'WireguardAllowedNetworks')


class WireguardInterface(models.Model):
    name = models.CharField(max_length=100,
                            validators=[RegexValidator(r'^[a-zA-Z0-9]+$',
                                                       _("Interface Name must be a string of alphanumeric chars."))],
                            unique=True,
                            verbose_name=_("Interface Name"))
    listen_port = models.PositiveSmallIntegerField(unique=True,
                                                   validators=[MinValueValidator(
                                                       1), MaxValueValidator(65535)],
                                                   verbose_name=_("Listen Port"))
    private_key = models.CharField(max_length=64,
                                   blank=True,
                                   validators=[validate_wireguard_private_key],
                                   verbose_name=_("Private Key (leave empty to auto generate)"))

    class Meta:
        verbose_name = _("Interface")
        verbose_name_plural = _("Interfaces")

    @property
    def public_key(self) -> str:
        return str(PrivateKey(self.private_key).public_key())

    @property
    def wg(self) -> WireGuard:
        interface, created = WireGuard.get_or_create_interface(self.name)
        if created:
            interface_created.send(sender=self.__class__, instance=self)
        return interface

    def __repr__(self):
        return f"{self._meta.verbose_name} {self.name}"

    def __str__(self):
        return f"{self.name}"

    def get_address_list(self):
        return list(self.addresses.all().values_list('address', flat=True))

    def get_endpoint(self):
        return f"{settings.WIREGUARD_ENDPOINT}:{self.listen_port}"


class WireguardIPAddress(models.Model):
    name = models.CharField(max_length=100,
                            blank=False, verbose_name=_("Name"))
    address = models.CharField(max_length=15, unique=True, validators=[validate_allowed_private_ip_interface],
                               verbose_name=_("Interface addresses"))
    interface = models.ForeignKey(WireguardInterface,
                                  on_delete=models.PROTECT,
                                  related_name='addresses',
                                  related_query_name='address',
                                  verbose_name=_("Interface"))

    class Meta:
        verbose_name = _("IP Address")
        verbose_name_plural = _("IP Addresses")

    def __repr__(self):
        return f"{self.interface}-{self.name} - {self.address}"

    def __str__(self):
        return f"{self.interface}-{self.name} - {self.address}"


class WireguardPeer(models.Model):
    status = models.BooleanField(default=True, verbose_name=_("Enabled"))
    interface_ip = models.ForeignKey(WireguardIPAddress,
                                     on_delete=models.PROTECT,
                                     related_name='peers',
                                     related_query_name='peer',
                                     verbose_name=_("Interface IP"))
    name = models.CharField(max_length=100,
                            blank=False, verbose_name=_("Name"))
    private_key = models.CharField(max_length=64,
                                   null=True,
                                   blank=True,
                                   validators=[validate_wireguard_private_key],
                                   verbose_name=_("Peer's Private Key"))
    preshared_key = models.CharField(max_length=64,
                                     unique=True,
                                     blank=True,
                                     validators=[
                                         validate_wireguard_preshared_key],
                                     verbose_name=_("Peer's Pre-Shared Key"))
    dns = models.ForeignKey('WireguardDNS', blank=True, null=True,
                            on_delete=models.SET_NULL, verbose_name=_("DNS"))
    address = models.GenericIPAddressField(protocol='IPv4', blank=True, null=True,
                                           validators=[validate_private_ipv4],
                                           verbose_name=_("IP-address"))
    allowed_networks = models.ForeignKey("WireguardAllowedNetworks", blank=True, null=True, on_delete=models.SET_NULL,
                                         related_name='peers',
                                         related_query_name='peer',
                                         verbose_name=_("Allowed list IP for Peer"))
    persistent_keepalive = models.PositiveSmallIntegerField(blank=True, default=0,
                                                            validators=[MinValueValidator(
                                                                0), MaxValueValidator(65535)],
                                                            verbose_name=_("Persistent Keepalive"))

    class Meta:
        verbose_name = _("Peer")
        verbose_name_plural = _("Peers")
        unique_together = ('interface_ip', 'name')

    def __repr__(self):
        return f"{self.name} - {self.address}"

    def __str__(self):
        return f"{self.name} - {self.address}"

    @property
    def public_key(self) -> str:
        return str(PrivateKey(self.private_key).public_key())

    @property
    def is_active(self):
        if self.status:
            try:
                if (datetime.now() - self.get_latest_handshake()).seconds < 3*60:
                    return True
            except Exception:
                return None
        return False

    def set_dns(self, pk: int):
        self.dns = WireguardDNS.objects.get(pk=pk)
        self.save()

    def set_allowed_networks(self, pk: int):
        self.allowed_networks = WireguardAllowedNetworks.objects.get(pk=pk)
        self.save()

    def get_latest_handshake(self):
        if self.status:
            try:
                return self.interface_ip.interface.wg.get_latest_handshake_of_peer(self.public_key)
            except Exception:
                return None
        else:
            return None

    def get_clean_dns(self) -> str:
        return clean_comma_separated_str(str(self.dns.addresses))

    def get_interface_allowed_ip(self) -> str:
        return f'{self.address}/32'

    def get_config(self) -> str:
        """
        Generate WireGuard configuration for peer as string.

        :return: Peer configuration as string.
        """
        private_key = self.private_key or _(
            '<INSERT-PRIVATE-KEY-FOR:%(pubkey)s>') % {'pubkey': self.public_key}

        config = f"[Interface]\n" \
                 f"Address={self.address}/32\n" \
                 f"PrivateKey={private_key}\n"

        if self.dns:
            config += f"DNS={self.get_clean_dns()}\n"

        config += f"[Peer]\n" \
                  f"Endpoint={self.interface_ip.interface.get_endpoint()}\n" \
                  f"PublicKey={self.interface_ip.interface.public_key}\n" \
                  f"PresharedKey={self.preshared_key}\n"
        if self.allowed_networks:
            config += f"AllowedIPs={self.allowed_networks.get_clean_allowed_networks()}\n"
        else:
            config += f"AllowedIPs=0.0.0.0/0\n"
        if self.persistent_keepalive:
            config += f"PersistentKeepalive={self.persistent_keepalive}\n"

        return config

    def update_keys(self):
        self.preshared_key = None
        self.private_key = None
        self.save()


class WireguardAllowedNetworks(models.Model):
    name = models.CharField(max_length=100,
                            blank=False, verbose_name=_("Name"))
    networks = models.TextField(validators=[validate_allowed_networks],
                                verbose_name=_("Allowed Networks"),
                                help_text=_("Comma separated list."))

    class Meta:
        verbose_name = _("Allowed Networks")
        verbose_name_plural = _("Allowed Networks")

    def __repr__(self):
        return f"{self.name}"

    def __str__(self):
        return f"{self.name}"

    def get_clean_allowed_networks(self) -> str:
        return clean_comma_separated_str(str(self.networks))


class WireguardDNS(models.Model):
    name = models.CharField(unique=True, max_length=100, blank=False)
    addresses = models.TextField(blank=True, verbose_name=_("DNS"),
                                 validators=[validate_allowed_ips],
                                 help_text=_("Comma separated list."))

    class Meta:
        verbose_name = _("DNS")
        verbose_name_plural = _("DNS")

    def __repr__(self):
        return f"{self.name}"

    def __str__(self):
        return f"{self.name} - {self.addresses}"

    def get_clean_dns(self) -> str:
        return clean_comma_separated_str(str(self.addresses))


@receiver(pre_save, sender=WireguardInterface)
def sync_wireguard_interface(sender, **kwargs):
    interface = kwargs['instance']
    if not interface.private_key:
        interface.private_key = str(PrivateKey.generate())

    interface.wg.set_interface(private_key=interface.private_key,
                               listen_port=interface.listen_port)
    # interface.wg.set_ip_addresses(interface.get_address_list())


@receiver(pre_save, sender=WireguardIPAddress)
def sync_wireguard_address(sender, **kwargs):
    address = kwargs['instance']
    interface = address.interface
    interface.wg.set_ip_addresses([address.address])


@receiver(pre_save, sender=WireguardPeer)
def sync_wireguard_peer(sender, **kwargs):
    peer: WireguardPeer = kwargs['instance']
    interface_ip = peer.interface_ip.address
    interface = peer.interface_ip.interface
    if not peer.address:
        address = IPv4Interface(interface_ip)
        interface_address = str(address.ip)
        subnet = address.network

        # fetch other peers for checks
        peers = WireguardPeer.objects.all().only('address')
        # auto assign IP address
        peer_addresses = [peer.address for peer in peers]
        peer_addresses.append(interface_address)
        if not peer.address:
            for host in subnet.hosts():
                if str(host) not in peer_addresses:
                    peer.address = str(host)
                    break
            else:
                raise RuntimeWarning(
                    "WireGuard interface's subnets have no available IP left")
        else:
            raise RuntimeWarning(
                "WireGuard interface's subnets have no available IP left")

    if not peer.private_key:
        peer.private_key = str(PrivateKey.generate())

    if not peer.preshared_key:
        peer.preshared_key = str(PrivateKey.generate())

    # update/create the wireguard peer
    if peer.status:
        interface.wg.set_peer(peer.public_key, peer.preshared_key,
                              peer.get_interface_allowed_ip())
    elif peer.pk and not peer.status and WireguardPeer.objects.get(pk=peer.pk):
        peer.interface_ip.interface.wg.remove_peers(peer.public_key)


@receiver(pre_delete, sender=WireguardInterface)
def delete_interface(sender, **kwargs):
    interface: WireguardInterface = kwargs['instance']
    interface.wg.delete()
    interface_deleted.send(sender, instance=interface)


@receiver(pre_delete, sender=WireguardIPAddress)
def del_wireguard_address(sender, **kwargs):
    address = kwargs['instance']
    interface = address.interface
    iptables_config = ''
    for network in interface.get_address_list():
        if address.address == network:
            continue
        iptables_config += f'iptables -D FORWARD -s {address.address} -d {network} -j REJECT;' \
                           f'iptables -D FORWARD -s {network} -d {address.address} -j REJECT;'
    iptables_config += f'iptables -D FORWARD -s {address.address} -d 10.8.88.253/32 -j REJECT'
    system(iptables_config)


@receiver(pre_delete, sender=WireguardPeer)
def delete_peer(sender, **kwargs):
    peer: WireguardPeer = kwargs['instance']
    peer.interface_ip.interface.wg.remove_peers(peer.public_key)


@receiver(interface_created, sender=WireguardInterface)
def postup_iptables_route(sender, **kwargs):
    interface: WireguardInterface = kwargs['instance']
    iptables_config = f"iptables -A FORWARD -i {interface.name} -j ACCEPT; " \
                      f"iptables -A FORWARD -o {interface.name} -j ACCEPT; "
    iptables_config += f"iptables -A INPUT -p udp -m udp --dport {interface.listen_port} -j ACCEPT"
    system(iptables_config)


@receiver(interface_deleted, sender=WireguardInterface)
def postdown_iptables_route(sender, **kwargs):
    interface: WireguardInterface = kwargs['instance']
    iptables_config = f"iptables -D FORWARD -i {interface.name} -j ACCEPT; " \
                      f"iptables -D FORWARD -o {interface.name} -j ACCEPT; "
    for network in interface.get_address_list():
        iptables_config += f"iptables -t nat -D POSTROUTING -s {network} -o {settings.WIREGUARD_OUTPUT_INTERFACE} -j MASQUERADE;"
    iptables_config += f"iptables -D INPUT -p udp -m udp --dport {interface.listen_port} -j ACCEPT"
    system(iptables_config)
