from django.contrib import admin
from .models import User, UserPeer, Tariff, Payment, PaymentGateway

class UserPeerInline(admin.TabularInline):
    model = UserPeer
    extra = 1

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('payment_name', 'tariff', 'activity_until', 'balance', 'status', 'admin')
    inlines = (UserPeerInline,)


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ('name', 'cost', 'cost_of_per_excess_peer', 'amount_peers')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'amount', 'user')


@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ('name', )


