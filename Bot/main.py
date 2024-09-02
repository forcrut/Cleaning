import telebot
from telebot import types
from .handlers import message_handler, calc_handlers
from Payment import Payment
from Schedule import ScheduleController

class TelegramBot:
	"""
	Взаимодействие пользователя с телеграм-ботом
	"""

	def __init__(self, token: str):
		"""
		:param token: токен телеграм бота, выданный BotFather
		"""
		self.bot = telebot.TeleBot(token)
		self.payment = Payment()
		self.order_states = {}
		# self.schedule = ScheduleController()
		self.create_static_keyboards()
		self.add_handlers()

	start = message_handler.start
	text_handler = message_handler.text_handler
	short_calc_handler = calc_handlers.short_calc_handler
	full_calc_handler = calc_handlers.full_calc_handler

	def create_static_keyboards(self):
		# главная клавиатура
		self.main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
		self.main_keyboard.add(types.KeyboardButton('Калькулятор'))
		for btn1, btn2 in [['Список услуг', 'История уборок'], ['Отзывы', 'О нас']]:
			self.main_keyboard.add(types.KeyboardButton(btn1), types.KeyboardButton(btn2))

	def add_handlers(self):
		# message
		self.bot.message_handler(commands=['start'])(self.start)
		self.bot.message_handler(content_types=['text'])(self.text_handler)
		# callback
		self.bot.callback_query_handler(func=lambda callback: callback.data.startswith(('комнат', 'сануз')))(self.short_calc_handler)
		self.bot.callback_query_handler(func=lambda callback: callback.data.startswith('заказ') or callback.data.endswith('заказ'))(self.full_calc_handler)

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
	