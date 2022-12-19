from django.contrib import admin
from django.utils.safestring import mark_safe

from django_wireguard.models import WireguardPeer, WireguardInterface,\
    WireguardIPAddress, WireguardAllowedNetworks,WireguardDNS
from django_wireguard.forms import WireguardPeerForm


class WireguardIPAddressInline(admin.TabularInline):
    model = WireguardIPAddress
    extra = 1

@admin.register(WireguardInterface)
class WireguardInterfaceAdmin(admin.ModelAdmin):
    model = WireguardInterface
    list_display = ('name', 'listen_port', 'public_key')
    inlines = (WireguardIPAddressInline,)


@admin.register(WireguardIPAddress)
class WireguardInterfaceAdmin(admin.ModelAdmin):
    model = WireguardIPAddress
    list_display = ('name', 'address', 'interface')


@admin.register(WireguardPeer)
class WireguardPeerAdmin(admin.ModelAdmin):
    model = WireguardPeer
    form = WireguardPeerForm
    change_form_template = 'django_wireguard/wireguardpeer_change_form.html'
    list_display = ('name', 'address', 'status', 'is_active')
    list_filter = ()

    def is_active(self, obj):
        return obj.is_active

    is_active.boolean = True

    def config(self, obj):
        return mark_safe(f'<pre>{obj.get_config()}</pre>')
    config.short_description = 'Config'


@admin.register(WireguardAllowedNetworks)
class WireguardAllowedNetworksAdmin(admin.ModelAdmin):
    list_display = ('name', )


@admin.register(WireguardDNS)
class WireguardDNSAdmin(admin.ModelAdmin):
    list_display = ('name', 'addresses')
