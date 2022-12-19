from ipaddress import IPv4Address, IPv4Interface, IPv4Network, AddressValueError

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django_wireguard.wireguard import PrivateKey, PublicKey

from django_wireguard.utils import clean_comma_separated_list


def validate_private_ipv4(value: str):
    """
    Validate private IPv4 address.

    :param value: Value to validate
    :type value: str
    :raises: ValidationError if value provided is not a valid IPv4 address
    """
    try:
        ip_address = IPv4Address(value)
        if not ip_address.is_private or ip_address.is_unspecified or ip_address.is_reserved:
            raise ValueError
    except (ValueError, AddressValueError):
        raise ValidationError(
            _('%(value)s is not a valid private IP Address.'),
            params={'value': value},
        )


def validate_allowed_private_ip_interface(value: str):
    """
    Validate IPv4 interfaces.

    :param value: Value to validate
    :type value: str
    :raises: ValidationError if value provided is not a valid list of IPv4 interfaces
    """

    try:
        ip_address = IPv4Interface(value)
        if not ip_address.is_private or ip_address.is_unspecified or ip_address.is_reserved:
            raise ValueError
    except (ValueError, AddressValueError):
        raise ValidationError(
            _('%(value)s is not a valid private IP Address.'),
            params={'value': value},
        )


def validate_allowed_ips(value: str):
    """
    Validate comma-separated list of allowed_ips (IPv4 address).

    :param value: Value to validate
    :type value: str
    :raises: ValidationError if value provided is not a valid list of IPv4 address
    """

    for ip in clean_comma_separated_list(value):
        try:
            ip_address = IPv4Address(ip)
            if ip_address.is_multicast or ip_address.is_unspecified or ip_address.is_reserved:
                raise ValueError
        except (ValueError, AddressValueError):
            raise ValidationError(
                _('%(value)s is not a valid IP Address.'),
                params={'value': ip},
            )


def validate_allowed_networks(value: str):
    """
    Validate comma-separated list of allowed_network (IPv4 Network).

    :param value: Value to validate
    :type value: str
    :raises: ValidationError if value provided is not a valid list of IPv4 Network
    """

    for address in clean_comma_separated_list(value):
        try:
            network = IPv4Network(address)
            if network.is_multicast or network.is_unspecified or network.is_reserved:
                raise ValueError
        except (ValueError, AddressValueError):
            raise ValidationError(
                _('%(value)s is not a valid IP Network.'),
                params={'value': address},
            )


def validate_wireguard_private_key(value: str):
    """
    Validate base64 encoded private key.

    :param value: Value to validate
    :raises: ValidationError if value provided is not a valid private key
    """
    try:
        PrivateKey(value)
    except ValueError:
        raise ValidationError(
            _('The value specified is not a valid WireGuard Private Key.'),
        )


def validate_wireguard_preshared_key(value):
    """
    Validate base64 encoded preshared key.

    :param value: Value to validate
    :raises: ValidationError if value provided is not a valid preshared key
    """
    try:
        PrivateKey(value)
    except ValueError:
        raise ValidationError(
            _('The value specified is not a valid WireGuard Pre-Shared Key.'),
        )
