import telebot
from telebot import types
from settings import DJANGO_BASE_DIR, ROOM_PRICE, BATHROOM_PRICE, BASE_PRICE, default_info
from django.utils import timezone
from datetime import datetime, timedelta

import os
import sys
sys.path.insert(1, os.path.abspath(DJANGO_BASE_DIR))
# print(sys.path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Server.settings')
import django
django.setup()

from Service.models import UserProfile


order_states = {}

class TelegramBot:
	"""

	"""

	def __init__(self, token: str):
		"""
		:param token: токен телеграм бота, выданный BotFather
		"""
		self.bot = telebot.TeleBot(token)
		self.create_static_keyboards()
		self.add_handlers()

	def create_static_keyboards(self):
		# main
		self.main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
		self.main_keyboard.add(types.KeyboardButton('Калькулятор'))
		for btn1, btn2 in [['Список услуг', 'История уборок'], ['Отзывы', 'О нас']]:
			self.main_keyboard.add(types.KeyboardButton(btn1), types.KeyboardButton(btn2))
		# inlines
		self.full_history_keyboard = types.InlineKeyboardMarkup()
		self.full_history_keyboard.add(
			types.InlineKeyboardButton('Оставить отзыв', callback_data='отзыв'),
			types.InlineKeyboardButton('Оставить жалобу', callback_data='жалоба')
		)
		self.short_history_keyboard = types.InlineKeyboardMarkup()
		self.short_history_keyboard.add(
			types.InlineKeyboardButton('Оставить жалобу', callback_data='жалоба')
		)

	@staticmethod
	def create_date_field(sequence_id: int):
		field, date = types.InlineKeyboardMarkup(row_width=4), timezone.now().date()
		for _ in range(8):
			row = []
			for _ in range(4):
				date += timedelta(days=1)
				row.append(types.InlineKeyboardButton(date.strftime('%d-%m-%Y'), callback_data='{}:{} заказ'.format(sequence_id, date)))
			field.add(*row)
		return field

	@staticmethod
	def create_time_field(sequence_id: int):
		field = types.InlineKeyboardMarkup()
		time_strs = [f'{hour:02d}:{minute:02d}' for hour in range(9, 18) for minute in [0, 30]]
		for _ in range(6):
			row = []
			for _ in range(3):
				time_str = time_strs.pop(0)
				row.append(types.InlineKeyboardButton(time_str, callback_data='{}:{} заказ'.format(sequence_id, time_str)))
			field.add(*row)
		return field

	@staticmethod
	def create_bool_field():
		field = types.InlineKeyboardMarkup()
		field.add(types.InlineKeyboardButton('Да', callback_data=))

	@staticmethod
	def short_calc_keyboard(rooms: int=1, bathrooms: int=1):
		short_calc = types.InlineKeyboardMarkup()
		rooms_ending = 'а' if rooms == 1 else ('ы' if rooms < 5 else '')
		bathrooms_ending = 'ел' if bathrooms == 1 else ('ла' if bathrooms < 5 else 'лов')
		for value, place in [(rooms, 'комнат' + rooms_ending), (bathrooms, 'сануз' + bathrooms_ending)]:
			short_calc.add(
				types.InlineKeyboardButton('-', callback_data='{}-|{} {}'.format(place, rooms, bathrooms)), 
				types.InlineKeyboardButton('{} {}'.format(value, place), callback_data='no_action'), 
				types.InlineKeyboardButton('+', callback_data='{}+|{} {}'.format(place, rooms, bathrooms))
			)
		short_calc.add(types.InlineKeyboardButton('Рассчитать уборку', callback_data='заказ|{} {}'.format(rooms, bathrooms)))
		return short_calc

	# полный калькулятор
	def full_calc_keyboard(self, rooms: int=1, bathrooms: int=1):
		pass

	# ссылка для оплаты
	def pay_keyboard(self):
		pass

	def add_handlers(self):
		# message
		self.bot.message_handler(commands=['start'])(self.start)
		self.bot.message_handler(content_types=['text'])(self.text_handler)
		# callback
		self.bot.callback_query_handler(func=lambda callback: callback.data.startswith(('комнат', 'сануз')))(self.short_calc_handler)
		self.bot.callback_query_handler(func=lambda callback: callback.data.startswith('заказ') or callback.data.endswith('заказ'))(self.full_calc_handler)

	def start(self, message):
		try: 
			user_profile = UserProfile.objects.get(pk=message.from_user.id)
			# TODO показать
			# print(message.from_user.id)
			if not user_profile.is_active:
				self.bot.send_message(message.chat.id, 'Очень жаль, но вы заблокированы, успехов с уборкой!')
		except UserProfile.DoesNotExist:
			pass
		self.bot.send_message(message.chat.id, 'Добро пожаловать в OnlyFLab!', reply_markup=self.main_keyboard)

	def short_calc_handler(self, callback):
		price, diff = int(callback.message.text.split()[1]), 1 if '+' in callback.data else -1
		rooms, bathrooms = map(int, callback.data.split('|')[1].split())
		if callback.data.startswith('комнат'):
			if 0 < rooms + diff <= 10:
				price += diff * ROOM_PRICE
				rooms += diff
			else:
				self.bot.answer_callback_query(callback.id)
				return
		elif callback.data.startswith('санузел'):
			if 0 < bathrooms + diff <= 10:
				price += diff * BATHROOM_PRICE
				bathrooms += diff
			else:
				self.bot.answer_callback_query(callback.id)
				return
		self.bot.edit_message_text('Итого: {}'.format(price), chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=TelegramBot.short_calc_keyboard(rooms, bathrooms))
		self.bot.answer_callback_query(callback.id)

	def full_calc_handler(self, callback):
		if callback.data.startswith('заказ'):
			rooms, bathrooms = map(int, callback.data.split('|')[1].split())
			order_states[callback.message.chat.id] = default_info.copy() | {'message_id': callback.message.message_id, 'rooms': rooms, 'bathrooms': bathrooms}
			self.bot.edit_message_text('Выберите дату уборки:', chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=TelegramBot.create_date_field(2))
			self.bot.answer_callback_query(callback.id)
		else:
			sequence_id, value = callback.data.split()[0].split(':', 1)
			order_states[callback.message.chat.id][field] = value
			sequence_id += 1
			match field:
				case 'cleaning_date':
					text, keyboard = 'Выберите дату уборки:', TelegramBot.create_time_field()
				case 'cleaning_start_time':
					text, keyboard = 'Выбрать дополнительно кухню:', TelegramBot.create_bool_field(sequence_id)
			self.bot.edit_message_text(text, chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=keyboard)
			self.bot.answer_callback_query(callback.id)


	def text_handler(self, message):
		if message.text == 'Калькулятор':
			if order_states.get(message.chat.id):
				del order_states[message.chat.id]
			self.bot.send_message(message.chat.id, 'Итого: {}'.format(BASE_PRICE + ROOM_PRICE + BATHROOM_PRICE), reply_markup=TelegramBot.short_calc_keyboard())

	def run(self):
		try:
			self.bot.polling(none_stop=True, interval=1)
		except KeyboardInterrupt:
			self.bot.stop_polling()
			self.bot.remove_webhook()


if __name__ == '__main__':
	from telebot import apihelper
	from settings import BOT_TOKEN

	# сессия живет 5 минут
	apihelper.SESSION_TIME_TO_LIVE = 300
	# создание и запуск бота
	bot = TelegramBot(BOT_TOKEN)
	bot.run()
	