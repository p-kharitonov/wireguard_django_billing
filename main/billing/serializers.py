from rest_framework import serializers

from billing.models import User
from django_wireguard.models import WireguardPeer, WireguardDNS, WireguardAllowedNetworks


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'status', 'nickname', 'activity_until', 'balance', 'payment_per_month', 'number_of_peers')


class WireguardPeerSerializer(serializers.ModelSerializer):
    class Meta:
        model = WireguardPeer
        fields = ('id', 'status', 'name', 'address', 'dns', 'allowed_networks', 'is_active', 'get_latest_handshake')


class DNSSerializer(serializers.ModelSerializer):
    class Meta:
        model = WireguardDNS
        fields = ('id', 'name')


class AllowedNetworksSerializer(serializers.ModelSerializer):
    class Meta:
        model = WireguardAllowedNetworks
        fields = ('id', 'name')

