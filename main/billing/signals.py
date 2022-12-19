from django.db.models.signals import pre_save
from django.dispatch import receiver
from telebot import TeleBot
from billing.models import User, Payment
from bot.settings import TELEGRAM_USERBOT_TOKEN

STATUS = {True: "возобновлен", False: "заблокирован"}


@receiver(pre_save, sender=User)
def pre_save_user(sender, **kwargs):
    user: User = kwargs['instance']
    if not user.status and user.admin:
        user.status = True
    elif user.id:
        pre_user = User.objects.get(pk=user.pk)
        peers = user.peers.all()
        print(peers)
        if user.status != pre_user.status:
            print(user.status, pre_user.status)
            if user.telegram_id:
                bot = TeleBot(TELEGRAM_USERBOT_TOKEN, threaded=False)
                bot.send_message(user.telegram_id, f'Доступ к VPN {STATUS[user.status]}.')
            for peer in peers:
                peer.status = user.status
                peer.save()


@receiver(pre_save, sender=Payment)
def pre_save_payment(sender, **kwargs):
    payment: Payment = kwargs['instance']
    user = payment.user
    if not payment.id and user:
        user.add_money(payment.amount)




