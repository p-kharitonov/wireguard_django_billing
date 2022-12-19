from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from celery import shared_task
from telebot import TeleBot
from core.settings import PAYMENTS_ALL, TELEGRAM_ADMIN_ID, \
    PAYMENTS_START_TIME
from billing.models import Payment, User, PaymentGateway
from bot.settings import TELEGRAM_USERBOT_TOKEN, TELEGRAM_ADMINBOT_TOKEN


bot = TeleBot(TELEGRAM_USERBOT_TOKEN, threaded=False)
adminbot = TeleBot(TELEGRAM_ADMINBOT_TOKEN, threaded=False)

@shared_task
def watch_payments():
    try:
        from_time_dirty = Payment.objects.values_list('created_at').first()
        if from_time_dirty:
            from_time = datetime.strftime(from_time_dirty[0], "%Y-%m-%dT%H:%M:%SZ")
        else:
            from_time = PAYMENTS_START_TIME
        payments = PaymentGateway.get_all_last_payments(from_time=from_time)
        for payment in payments:
            operation_id = payment['operation_id']
            if Payment.objects.filter(operation_id=operation_id).exists():
                break
            name = payment['title']
            user = User.objects.filter(payment_name__icontains=name).first()
            amount = int(payment['amount'])
            created_at = payment['datetime']
            currency = payment['amount_currency']
            if not user and PAYMENTS_ALL:
                new_payment = Payment(operation_id=operation_id, created_at=created_at, amount=amount, comment=name)
                new_payment.save()
                adminbot.send_message(TELEGRAM_ADMIN_ID,
                                      f'[INFO] Неизвестный пользователь {name} пополнил баланс на сумму {amount} {currency}.')
            elif user:
                new_payment = Payment(operation_id=operation_id, created_at=created_at, amount=amount,
                                      user=user)
                new_payment.save()
                adminbot.send_message(TELEGRAM_ADMIN_ID,
                                      f'[INFO] Пользователь {name} пополнил баланс на сумму {amount} {currency}.')
                if user.telegram_id:
                    bot.send_message(user.telegram_id, f'Баланс пополнен на сумму {amount} {currency}.')
    except Exception as e:
        error = f'{e}'[:500]
        print(error)
        adminbot.send_message(TELEGRAM_ADMIN_ID, f'[ERROR] send_status - {error}')


@shared_task
def block_or_notification_user():
    try:
        for user in User.objects.filter(status=True, activity_until__lte=(date.today() + relativedelta(days=1))):
            if user.activity_until == date.today() + relativedelta(days=1):
                if user.telegram_id:
                    bot.send_message(user.telegram_id, f'Добрый день! Сегодня последний оплаченый день.')
            else:
                user.block()
    except Exception as e:
        error = f'{e}'[:500]
        print(error)
        adminbot.send_message(TELEGRAM_ADMIN_ID, f'[ERROR] send_status - {error}')
