from Service.models import UserProfile, Order
import settings
from . import keyboards
from telebot.apihelper import ApiException


def start(self, message):
	try: 
		user = UserProfile.objects.get(pk=message.from_user.id).user
		if not user.is_active:
			self.bot.send_message(message.chat.id, 'Очень жаль, но вы заблокированы, успехов с уборкой!')
	except UserProfile.DoesNotExist:
		pass
	self.bot.send_message(message.chat.id, 'Добро пожаловать в OnlyFLab!', reply_markup=self.main_keyboard)

def text_handler(self, message):
	if message.text == 'Калькулятор':
		self.bot.send_message(message.chat.id, 'Итого: {}'.format(settings.BASE_PRICE + settings.ROOM_PRICE + settings.BATHROOM_PRICE), reply_markup=keyboards.short_calc_keyboards[0][0])
	elif message.text == 'Список услуг':
		self.bot.send_message(message.chat.id, settings.services, parse_mode="HTML")
	elif message.text == 'История уборок':
		text = '<b>История заказов:</b>\n'
		try:
			user_orders = UserProfile.objects.get(id=message.from_user.id).user.user_orders
			for order in user_orders.all():
				text += f"""
					<code>
						<b>ID:</b> {order.id},
						<b>Дата:</b> {order.cleaning_date},
						<b>Временной интервал:</b> {order.cleaning_start_time}-{order.cleaning_end_time},
						<b>Контекст:</b> {order.info},
						<b>Стоимость:</b> {order.price},
						<b>Статус:</b> {order.status},
						<b>Спасибо за заказ!</b>.
					</code>
				"""
		except UserProfile.DoesNotExist:
			text = '<code>\nВы еще не совершали заказов.\n</code>'
		self.bot.send_message(message.chat.id, text, parse_mode="HTML")
	elif message.text == 'Отзывы':
		pass
	elif message.text == 'О нас':
		self.bot.send_message(message.chat.id, settings.about, parse_mode="HTML")