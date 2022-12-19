from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from telebot import TeleBot, types
import json
import qrcode

from bot.models import Bot
from bot.settings import PHONE_NUMBER, CURRENCY, TELEGRAM_USERBOT_TOKEN, TELEGRAM_ADMINBOT_TOKEN, TELEGRAM_ADMIN_ID


bot = TeleBot(TELEGRAM_USERBOT_TOKEN, threaded=False)
adminbot = TeleBot(TELEGRAM_ADMINBOT_TOKEN, threaded=False)
STATUS = {True: '✅', False: '⛔'}


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print('[INFO] Bot is started! ')
        bot.enable_save_next_step_handlers(delay=2)  # Сохранение обработчиков
        bot.load_next_step_handlers()  # Загрузка обработчиков
        bot.infinity_polling()


@bot.message_handler(commands=['start', 'status'])
def send_welcome(message):
    try:
        if message.chat.type == 'private':
            user = Bot.get_user(message.from_user.id)
            if user:
                keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, )
                buttons_text = [_("👨 Profile"), _("💾 Download config"), _("🔑 Update config"),
                                _("💪 Additional config"), _("📖 Instruction"), _("💰 How to pay")]
                keyboard.add(*[types.KeyboardButton(str(button)) for button in buttons_text])
                text = _("📃 Use the keyboard below.")
                bot.send_message(message.from_user.id, str(text), reply_markup=keyboard)
            else:
                pass
    except Exception as e:
        from_user = f'{message.from_user.id} {message.from_user.first_name} {message.from_user.last_name} ({message.from_user.username})'
        adminbot.send_message(TELEGRAM_ADMIN_ID, f'{from_user}\n{message.text}\n[ERROR] - {e}'[:1000])


@bot.message_handler(func=lambda message: True, content_types=['text'])
def user_menu(message):
    try:
        if message.chat.type == 'private':
            user = Bot.get_user(message.from_user.id)
            if user:
                sending_data = {}
                if message.text == _("👨 Profile"):
                    text = _(
                        '%(status)s <b>%(name)s</b>\n📅 Active until: %(activity_until)s\n'
                        '💰 Balance: %(balance)s %(CURRENCY)s\n🍀 Payment: %(tariff)s %(CURRENCY)s/month\n'
                        '📱 Number of configs: %(number_of_peers)s') % {
                               'status': STATUS[user['status']], 'name': user['nickname'].title(), 'activity_until': user['activity_until'],
                               'balance': user['balance'], 'CURRENCY': CURRENCY, 'tariff': user['payment_per_month'],
                               'number_of_peers': user['number_of_peers']}
                    bot.send_message(message.from_user.id, str(text), parse_mode="HTML")
                elif message.text == _("📖 Instruction"):
                    text = _('To use the config, you need to install the WireGuard VPN client '
                             'and upload the resulting file to it.\nOn the sent file, click "Save to download", '
                             'then run the WireGuard program, click the add icon ("+" icon), '
                             'select the configuration file (it will be saved to download to the Telegram folder), '
                             'and everything is ready, turn it on, and you can work!\n'
                             'Link to installers for all devices is here ->\n'
                             'https://www.wireguard.com/install/')
                    bot.send_message(message.from_user.id, str(text))
                elif message.text == _("💾 Download config"):
                    peers = Bot.get_peers_of_user(message.from_user.id)
                    if not peers:
                        text = _("You don't have config files.")
                        bot.send_message(message.from_user.id, str(text))
                    else:
                        markup = types.InlineKeyboardMarkup()
                        sending_data = {}
                        text = _('Set config:')
                        sending_data['type'] = 'd_c'
                        for peer in peers:
                            sending_data['peer_n'] = peer['id']
                            callback_data = json.dumps(sending_data)
                            markup.add(types.InlineKeyboardButton(text=peer['name'], callback_data=callback_data))
                        markup.add(types.InlineKeyboardButton(text=str(_('-Cancel-')), callback_data='{"type": "exit"}'))
                        bot.send_message(message.chat.id, text=str(text), reply_markup=markup)
                elif message.text == _("🔑 Update config"):
                    peers = Bot.get_peers_of_user(message.from_user.id)
                    if not peers:
                        text = _("You don't have config files.")
                        bot.send_message(message.from_user.id, str(text))
                    else:
                        markup = types.InlineKeyboardMarkup()
                        text = _('Set config:')
                        sending_data['type'] = 'u_c'
                        for peer in peers:
                            sending_data['peer_n'] = peer['id']
                            callback_data = json.dumps(sending_data)
                            markup.add(types.InlineKeyboardButton(text=str(peer['name']), callback_data=callback_data))
                        markup.add(types.InlineKeyboardButton(text=str(_('-Cancel-')), callback_data='{"type": "exit"}'))
                        bot.send_message(message.chat.id, text=str(text), reply_markup=markup)
                elif message.text == _("💰 How to pay"):
                    text = _("I accept a payment on SBP of Yoomoney on my phone %(phone)s") % {'phone': PHONE_NUMBER}
                    bot.send_message(message.chat.id, text=str(text))
                elif message.text == _("💪 Additional config"):
                    sending_data['type'] = 'a_c'
                    check = Bot.check_user_for_adding_peer(message.chat.id)
                    if check['permit']:
                        markup = types.InlineKeyboardMarkup()
                        text = _("An additional config costs %(cost_of_per_excess_peer)s %(CURRENCY)s/month, "
                                 "now %(cost)s %(CURRENCY)s will be debited from the balance, "
                                 "the payment will %(payment)s %(CURRENCY)s/month, "
                                 "the date activity will %(activity_until)s, "
                                 "and the balance will %(balance)s %(CURRENCY)s.") % {
                                   'cost_of_per_excess_peer': check['cost_of_per_excess_peer'],
                                   'CURRENCY': CURRENCY,
                                   'cost': check['cost'],
                                   'payment': check['payment'],
                                   'activity_until': check['activity_until'],
                                   'balance': check['balance']}
                        sending_data['confirm'] = True
                        callback_data = json.dumps(sending_data)
                        text_button = _("Yes, I want an additional config")
                        markup.add(types.InlineKeyboardButton(text=str(text_button),
                                                              callback_data=callback_data))
                        sending_data['confirm'] = False
                        callback_data = json.dumps(sending_data)
                        markup.add(types.InlineKeyboardButton(text=str(_("No")), callback_data=callback_data))
                        bot.send_message(message.chat.id, text=str(text), reply_markup=markup)
                    else:
                        text = _("%(text_check)s") % {'text_check': check['text']}
                        bot.send_message(message.chat.id, text=str(text))
                else:
                    adminbot.send_message(TELEGRAM_ADMIN_ID, f'{message.from_user.first_name} {message.from_user.last_name} '
                                            f'(<b>{message.from_user.username}</b>) написал:\n"<i>{message.text}</i>"',
                         parse_mode="HTML")
            else:
                adminbot.send_message(TELEGRAM_ADMIN_ID, f'{message.from_user.first_name} {message.from_user.last_name} '
                                            f'(<b>{message.from_user.username}</b>) написал:\n"<i>{message.text}</i>"',
                         parse_mode="HTML")
    except Exception as e:
        from_user = f'{message.from_user.id} {message.from_user.first_name} {message.from_user.last_name} ({message.from_user.username})'
        adminbot.send_message(TELEGRAM_ADMIN_ID,f'{from_user}\n{message.text}\n[ERROR] - {e}'[:1000])


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    try:
        if call.message.chat.type == 'private':
            user = Bot.get_user(call.message.chat.id)
            if user:
                bot.delete_message(call.message.chat.id, call.message.message_id)
                sending_data = json.loads(call.data)
                # Update DNS
                if sending_data['type'] == 'u_d':
                    markup = types.InlineKeyboardMarkup()
                    peer = Bot.get_peer(sending_data['peer_n'])
                    text = _('Set DNS (<u>%(name)s</u>):') % {'name': peer['name']}
                    for dns in Bot.get_dns(call.message.chat.id):
                        sending_data['type'] = 'd_or_u_c'
                        sending_data['dns_n'] = f'{dns["id"]}'
                        callback_data = json.dumps(sending_data)
                        markup.add(types.InlineKeyboardButton(text=dns["name"], callback_data=callback_data))
                    markup.add(types.InlineKeyboardButton(text=str(_('-Cancel-')), callback_data='{"type": "exit"}'))
                    bot.send_message(call.message.chat.id, text=str(text), reply_markup=markup, parse_mode="HTML")
                # Update Networks
                elif sending_data['type'] == 'u_n':
                    markup = types.InlineKeyboardMarkup()
                    peer = Bot.get_peer(sending_data['peer_n'])
                    text = _('Set networks for VPN (<u>%(name)s</u>):') % {'name': peer['name']}
                    for networks in Bot.get_allowed_networks():
                        sending_data['type'] = 'd_or_u_c'
                        sending_data['network_n'] = f'{networks["id"]}'
                        callback_data = json.dumps(sending_data)
                        markup.add(types.InlineKeyboardButton(text=networks['name'], callback_data=callback_data))
                    markup.add(types.InlineKeyboardButton(text=str(_('-Cancel-')), callback_data='{"type": "exit"}'))
                    bot.send_message(call.message.chat.id, text=str(text), reply_markup=markup, parse_mode="HTML")
                # Update Keys
                elif sending_data['type'] == 'u_k':
                    markup = types.InlineKeyboardMarkup()
                    peer = Bot.get_peer(sending_data['peer_n'])
                    text = _("Are you sure? After updating the keys, the old config will no longer work (<u>%(name)s</u>). Use it if you really need it.") % {'name': peer['name']}
                    sending_data['type'] = 'd_or_u_c'
                    sending_data['key_b'] = True
                    callback_data = json.dumps(sending_data)
                    markup.add(types.InlineKeyboardButton(text=str(_('Yes')), callback_data=callback_data))
                    markup.add(types.InlineKeyboardButton(text=str(_('No!!!')), callback_data='{"type": "exit"}'))
                    bot.send_message(call.message.chat.id, text=str(text), reply_markup=markup, parse_mode="HTML")
                # Update or download config
                elif sending_data['type'] == 'd_or_u_c':
                    res = None
                    if sending_data.get('dns_n', False):
                        res = Bot.set_dns(int(sending_data['peer_n']), int(sending_data['dns_n']))
                    elif sending_data.get('network_n', False):
                        res = Bot.set_allowed_networks(int(sending_data['peer_n']), int(sending_data['network_n']))
                    elif sending_data.get('key_b', False):
                        res = Bot.update_keys(int(sending_data['peer_n']))
                    if res:
                        peer = Bot.get_peer(sending_data['peer_n'])
                        text = _("It's update (<u>%(name)s</u>)! What's next?")  % {'name': peer['name']}
                        markup = types.InlineKeyboardMarkup()
                        sending_data = {'type': 'd_c', 'peer_n': sending_data['peer_n']}
                        callback_data = json.dumps(sending_data)
                        markup.add(types.InlineKeyboardButton(text=str(_('Download config')), callback_data=callback_data))
                        sending_data = {'type': 'u_c', 'peer_n': sending_data['peer_n']}
                        callback_data = json.dumps(sending_data)
                        markup.add(types.InlineKeyboardButton(text=str(_('Update more')), callback_data=callback_data))
                        markup.add(types.InlineKeyboardButton(text=str(_('Exit')), callback_data='{"type": "exit"}'))
                        bot.send_message(call.message.chat.id, text=str(text),
                                        reply_markup=markup, parse_mode="HTML")
                # Download Config
                elif sending_data['type'] == 'd_c':
                    config = Bot.get_config(call.message.chat.id, sending_data['peer_n'])
                    name_config = config['name']
                    text = config['config']
                    qr = qrcode.QRCode(
                        version=None,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data(text)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")
                    img.save(f"qr/{name_config}.png")
                    file = text.encode('utf-8')
                    bot.send_photo(call.message.chat.id, open(f"qr/{name_config}.png", "rb"), caption=f'{name_config}.conf')
                    bot.send_document(call.message.chat.id, document=file, visible_file_name=f'{name_config}.conf')
                # Update Config
                elif sending_data['type'] == 'u_c':
                    peer = Bot.get_peer(sending_data['peer_n'])
                    text = _('What to update (<u>%(name)s</u>)?') % {'name': peer['name']}
                    markup = types.InlineKeyboardMarkup()
                    type_update_configs = (('u_d', _('Update DNS')), ('u_n', _('Update Allowed networks')),
                                           ('u_k', _('Update Keys')))
                    for type_update_config in type_update_configs:
                        sending_data['type'] = type_update_config[0]
                        callback_data = json.dumps(sending_data)
                        markup.add(
                            types.InlineKeyboardButton(text=str(type_update_config[1]), callback_data=callback_data))
                    markup.add(types.InlineKeyboardButton(text=str(_('-Cancel-')), callback_data='{"type": "exit"}'))
                    bot.send_message(call.message.chat.id,
                                     text=str(text),
                                     reply_markup=markup, parse_mode="HTML")
                # Additional config
                elif sending_data['type'] == 'a_c':
                    if sending_data['confirm']:
                        peer = Bot.make_excess_peer(call.message.chat.id)
                        if peer:
                            text = _("Config %(name)s is added.") % {'name': peer['name']}
                            markup = types.InlineKeyboardMarkup()
                            sending_data = {'type': 'd_c', 'peer_n': peer['id']}
                            callback_data = json.dumps(sending_data)
                            markup.add(types.InlineKeyboardButton(text=str(_('Download config')), callback_data=callback_data))
                            markup.add(types.InlineKeyboardButton(text=str(_('-Cancel-')), callback_data='{"type": "exit"}'))
                            bot.send_message(call.message.chat.id, text=str(text),
                                            reply_markup=markup)

                elif sending_data['type'] == 'exit':
                    pass
                else:
                    pass
    except Exception as e:
        from_user = f'{call.message.chat.id} - {call.message.chat.first_name} ' \
                    f'{call.message.chat.last_name} {call.message.chat.username}'
        adminbot.send_message(TELEGRAM_ADMIN_ID,f'{from_user}\n{call.message.text}\n[ERROR] - {e}'[:1000])
