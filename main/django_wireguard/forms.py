from django import forms
from django.utils.translation import gettext_lazy as _

from django_wireguard import settings
from django_wireguard.models import WireguardPeer


class WireguardPeerForm(forms.ModelForm):
    class Meta:
        model = WireguardPeer
        if settings.WIREGUARD_STORE_PRIVATE_KEYS:
            fields = '__all__'

