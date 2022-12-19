from requests import post
from requests.structures import CaseInsensitiveDict
import json
from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import date
from dateutil.relativedelta import relativedelta
import math
from billing.settings import CURRENCY, PAYMENTS_START_TIME
from django_wireguard.models import WireguardPeer

class User(models.Model):
    admin = models.BooleanField(default=False, verbose_name=_('Administrator'))
    status = models.BooleanField(default=True, verbose_name=_('Status'))
    payment_name = models.CharField(max_length=150, unique=True, verbose_name=_('Payment name'),
                                    help_text=_('For Payment'))
    nickname = models.CharField(max_length=150, unique=True, verbose_name=_('NickName'), help_text=_('For Config'))
    tariff = models.ForeignKey('Tariff', on_delete=models.PROTECT, related_name='persons', related_query_name='persons',
                               verbose_name=_('Tariff'))
    created_at = models.DateField(verbose_name=_('Date of creation'))
    activity_until = models.DateField(verbose_name=_('Activity until'))
    balance = models.PositiveSmallIntegerField(default=0, verbose_name=_('Balance'))
    telegram_id = models.CharField(max_length=100, null=True, unique=True, blank=True, verbose_name=_('Telegram ID'))
    peers = models.ManyToManyField(WireguardPeer, through='UserPeer', verbose_name=_('Peers'))

    def __repr__(self):
        return f'{self.nickname}'

    def __str__(self):
        return f'{self.nickname}'

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-nickname']

    @property
    def number_of_peers(self):
        return self.peers.all().count()

    @property
    def payment_per_month(self):
        tariff = self.tariff
        peers = self.peers
        number_of_excess_peers = peers.count() - tariff.amount_peers if (peers.count() - tariff.amount_peers) > 0 else 0
        final_cost_for_per_month = tariff.cost + tariff.cost_of_per_excess_peer * number_of_excess_peers
        return final_cost_for_per_month

    def block(self):
        if self.status:
            self.status = False
            self.save()

    def add_money(self, amount):
        balance = self.balance + amount
        self.balance = balance % self.payment_per_month
        months = balance // self.payment_per_month
        if months:
            if self.activity_until < date.today():
                start_date = date.today()
            else:
                start_date = self.activity_until
            self.activity_until = start_date + relativedelta(months=months)
            if not self.status:
                self.status = True
        self.save()

    def get_cost_for_adding_peer(self):
        # cost_of_per_excess_peer = self.tariff.cost_of_per_excess_peer
        # cost_for_adding_peer = int((self.activity_until - date.today()).days % 30 / 30 * cost_of_per_excess_peer)
        # if cost_for_adding_peer == 0:
        #     cost_for_adding_peer = cost_of_per_excess_peer
        return self.tariff.cost_of_per_excess_peer

    def get_new_balance_for_adding_peer(self):
        tariff = self.tariff
        if tariff.amount_peers <= self.number_of_peers:
            cost_for_adding_peer = self.get_cost_for_adding_peer()
            balance = self.balance - cost_for_adding_peer
            if balance < 0:
                balance = -balance
                count_month = math.ceil(balance / cost_for_adding_peer)
                balance = count_month * tariff.cost - balance
            return balance
        return self.balance

    def get_new_date_activity_until_for_adding_peer(self):
        tariff = self.tariff
        if tariff.amount_peers <= self.number_of_peers:
            cost_for_adding_peer = self.get_cost_for_adding_peer()
            balance = self.balance - cost_for_adding_peer
            if balance < 0:
                # balance = -balance
                # count_month = math.ceil(balance / cost_for_adding_peer)
                return self.activity_until - relativedelta(months=1)
        return self.activity_until

    def get_new_payment_for_adding_peer(self):
        tariff = self.tariff
        new_payment = self.payment_per_month
        if tariff.amount_peers <= self.number_of_peers:
            new_payment += tariff.cost_of_per_excess_peer
        return new_payment

    def set_new_balance_and_date_after_add_peer(self):
        self.activity_until = self.get_new_date_activity_until_for_adding_peer()
        self.balance = self.get_new_balance_for_adding_peer()
        self.save()

    def check_for_adding_peer(self):
        if self.get_new_date_activity_until_for_adding_peer() <= date.today():
            text = _("An additional config costs %(cost_of_per_excess_peer)s %(CURRENCY)s/month, "
                     "now you need pay %(cost_for_adding_peer)s %(CURRENCY)s.") % {
                       'cost_of_per_excess_peer': self.tariff.cost_of_per_excess_peer,
                       'cost_for_adding_peer': self.get_cost_for_adding_peer(),
                       'CURRENCY': CURRENCY
                   }
            return False, text
        elif self.tariff.max_peers <= self.number_of_peers:
            text = _("You have max number of configs.")
            return False, text
        else:
            return True, ''

    def add_peer(self):
        peers = self.peers.all()
        peers_count = peers.count()
        interface_ip = peers.first().interface_ip
        while True:
            name = f'{self.nickname}{peers_count + 1}'
            if WireguardPeer.objects.filter(name=name):
                peers_count += 1
            else:
                break
        peer = WireguardPeer.objects.create(interface_ip=interface_ip, name=name)
        UserPeer.objects.create(user=self, peer=peer)
        self.set_new_balance_and_date_after_add_peer()
        return peer

class UserPeer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('User'))
    peer = models.OneToOneField(WireguardPeer, unique=True, on_delete=models.CASCADE, verbose_name=_('Peer'))

    class Meta:
            verbose_name = _('Peer')
            verbose_name_plural = _('Peers')

    def __repr__(self):
        return f'{self.peer}'

    def __str__(self):
        return f'{self.peer}'


class Tariff(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name=_('Name'))
    cost = models.PositiveSmallIntegerField(verbose_name=_('Cost'))
    amount_peers = models.PositiveSmallIntegerField(verbose_name=_('Number of peers'))
    max_peers = models.PositiveSmallIntegerField(default=10, verbose_name=_('Max number of peers'))
    cost_of_per_excess_peer = models.PositiveSmallIntegerField(verbose_name=_('Cost of per excess peer'))

    def __repr__(self):
        return f'{self.name} - {self.cost}'

    def __str__(self):
        return f'{self.name} - {self.cost}'

    class Meta:
        verbose_name = _('Tariff')
        verbose_name_plural = _('Tariffs')
        ordering = ['-name']


class PaymentGateway(models.Model):
    YOOMONEY = 'YO'
    QIWI = 'QI'
    PROVIDER_CHOICES = [
        (YOOMONEY, 'Yoomoney'),
        (QIWI, 'QIWI'),
    ]
    name = models.CharField(max_length=2, choices=PROVIDER_CHOICES, unique=True, verbose_name=_('Name'))
    token = models.TextField(max_length=500, verbose_name=_('Token'))

    def __repr__(self):
        return f'{self.name}'

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name = _('Payment Gateway')
        verbose_name_plural = _('Payment Gateways')

    def get_last_payments(self, from_time: str = '') -> list:
        payments = []
        if not from_time:
            from_time = PAYMENTS_START_TIME
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/x-www-form-urlencoded"
        headers["Authorization"] = f"Bearer {self.token}"
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        if self.name == self.YOOMONEY:
            url = 'https://yoomoney.ru/api/operation-history'
            resp = post(url, headers=headers, data=f'type=deposition&from={from_time}')
            if resp.status_code == 200:
                payments_dirty = json.loads(resp.content)['operations']
                for payment in payments_dirty:
                    if payment['status'] != 'success':
                        continue
                    payments.append({
                        'operation_id': payment['operation_id'],
                        'title': payment['title'],
                        'amount': payment['amount'],
                        'amount_currency': payment['amount_currency'],
                        'datetime': payment['datetime'],
                    })
        elif self.name == self.QIWI:
            pass
        return payments

    @classmethod
    def get_all_last_payments(cls, from_time: str = '') -> list:
        payments = []
        payment_gateways = PaymentGateway.objects.all()
        for provider in payment_gateways:
            payments += provider.get_last_payments(from_time=from_time)
        return payments


class Payment(models.Model):
    operation_id = models.CharField(max_length=150, unique=True, verbose_name=_('Operation ID'))
    created_at = models.DateTimeField(verbose_name=_('Date of creation'))
    amount = models.PositiveSmallIntegerField(verbose_name=_('Amount'))
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='users',
                             related_query_name='user', verbose_name=_('User'))
    comment = models.CharField(null=True, blank=True, max_length=150, verbose_name=_('Comment'))

    def __str__(self):
        return f'{self.operation_id}'

    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-created_at']
