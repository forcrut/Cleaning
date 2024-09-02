import threading
import time
from telebot.apihelper import ApiException
from Service.models import Order


def order_payment(instance: 'TelegramBot', user_id: int, message_id: int, order_id: int, minutes: int=1):
	"""
	Поток, который предназначен для ограничения времени на онлайн оплату заказа
	:param instance: экземпляр TelegramBot для редактирования сообщения,
	:param user_id: номер телеграм-id,
	:param message_id: номер сообщения,
	:param order_id: номер заказа,
	:param minutes: кол-во минут действия потока
	"""
	end_time = time.time() + minutes*60
	# главный процесс
	while time.time() < end_time:
		if instance.payment.was_paid(order_id):
			try:
				instance.bot.edit_message_text('<b>Смотрите подробности заказа в истории!</b>', chat_id=user_id, message_id=message_id, reply_markup=None, parse_mode='HTML')
				order = Order.objects.get(pk=order_id)
				order.status = 2
				order.save()
			except ApiException:
				pass
			except Exception as errs:
				print('Возникли ошибки в order_payment потоке: {}'.format(errs))
		time.sleep(30)
	# все равно в конце удаляем сообщение
	try:
		instance.bot.edit_message_text('<b>Смотрите подробности заказа в истории!</b>', chat_id=user_id, message_id=message_id, reply_markup=None, parse_mode='HTML')
	except ApiException:
		pass
