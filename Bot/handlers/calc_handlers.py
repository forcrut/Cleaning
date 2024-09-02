from telebot import types
from . import keyboards
from Service.models import CustomUser, UserProfile, Order
from Service.forms import UserForm, OrderForm
import settings
from datetime import datetime
from telebot.apihelper import ApiException
import threading
from . import threads


def resend_message(self, message, text: str):
	try:
		self.bot.delete_message(message.from_user.id, self.order_states[message.from_user.id]['message_id'])
	except ApiException:
		self.order_states[message.from_user.id]['message_id'] = None
	self.order_states[message.from_user.id]['message_id'] = self.bot.send_message(message.chat.id, text, reply_markup=None, parse_mode='HTML').message_id

def short_calc_handler(self, callback):
	price, diff = int(callback.message.text.split()[1]), 1 if '+' in callback.data else -1
	rooms, bathrooms = map(int, callback.data.split('|')[1].split())
	if callback.data.startswith('комнат'):
		if 0 < rooms + diff <= 10:
			price += diff * settings.ROOM_PRICE
			rooms += diff
		else:
			self.bot.answer_callback_query(callback.id)
			return
	elif callback.data.startswith('сануз'):
		if 0 < bathrooms + diff <= 10:
			price += diff * settings.BATHROOM_PRICE
			bathrooms += diff
		else:
			self.bot.answer_callback_query(callback.id)
			return
	self.bot.edit_message_text('Итого: {}'.format(price), chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=keyboards.short_calc_keyboards[rooms-1][bathrooms-1], parse_mode='HTML')
	self.bot.answer_callback_query(callback.id)

def process_street(self, message, text: str):
	try:
		# TODO обработчик улицы
		street = ' '.join(message.text.split())
	except ValueError:
		text = '\n'.join(text.split('\n')[:-1]) + '\nОшибка, улица не может иметь вид {}. Введите улицу:'.format(message.text)
		resend_message(self, message, text)
		self.bot.register_next_step_handler(message, lambda message: process_street(self, message, text=text))
		return
	self.order_states[message.from_user.id]['street'] = street
	text = '\n'.join(text.split('\n')[:-1]) + '\n{}: {}'.format(settings.data_humanize['street'], street) + '\nВведите дом:'
	resend_message(self, message, text)
	self.bot.register_next_step_handler(message, lambda message: process_house(self, message, text=text))

def process_house(self, message, text: str):
	try:
		# TODO обработчик дома
		house = ' '.join(message.text.split())
	except ValueError:
		text = '\n'.join(text.split('\n')[:-1]) + '\nОшибка, дом не может иметь вид {}. Введите дом:'.format(message.text)
		resend_message(self, message, text)
		self.bot.register_next_step_handler(message, lambda message: process_house(self, message, text=text))
		return
	self.order_states[message.from_user.id]['house'] = house
	text = '\n'.join(text.split('\n')[:-1]) + '\n{}: {}'.format(settings.data_humanize['house'], house) + '\nВведите корпус(если его нет, то поставьте -):'
	resend_message(self, message, text)
	self.bot.register_next_step_handler(message, lambda message: process_section(self, message, text=text))

def process_section(self, message, text: str):
	try:
		# TODO обработчик корпуса
		section = message.text.strip().replace(' ', '')
		section = None if section == '-' else int(section)
	except ValueError:
		text = '\n'.join(text.split('\n')[:-1]) + '\nОшибка, корпус не может иметь вид {}. Введите корпус(если его нет, то поставьте -):'.format(message.text)
		resend_message(self, message, text)
		self.bot.register_next_step_handler(message, lambda message: process_section(self, message, text=text))
		return
	self.order_states[message.from_user.id]['section'] = section
	text = '\n'.join(text.split('\n')[:-1]) + '\n{}: {}'.format(settings.data_humanize['section'], section or '-') + '\nВведите квартиру:'
	resend_message(self, message, text)
	self.bot.register_next_step_handler(message, lambda message: process_apartment(self, message, text=text))

def process_apartment(self, message, text: str):
	try:
		# TODO обработчик квартиры
		apartment = int(message.text.strip())
	except ValueError:
		text = '\n'.join(text.split('\n')[:-1]) + '\nОшибка, квартира не может иметь вид {}. Введите квартиру:'.format(message.text)
		resend_message(self, message, text)
		self.bot.register_next_step_handler(message, lambda message: process_apartment(self, message, text=text))
		return
	self.order_states[message.from_user.id]['apartment'] = apartment
	text = '\n'.join(text.split('\n')[:-1]) + '\nОбработка...'
	try:
		self.bot.delete_message(message.from_user.id, self.order_states[message.from_user.id]['message_id'])
	except ApiException:
		self.order_states[message.from_user.id]['message_id'] = None
	bot_message = self.bot.send_message(message.chat.id, text, reply_markup=None, parse_mode='HTML')
	self.order_states[message.from_user.id]['message_id'] = bot_message.message_id
	fake_call = types.CallbackQuery(
		id='fake_call',
		from_user=message.from_user, 
		chat_instance='fake_call',
		message=bot_message, 
		data='apartment:{}|заказ'.format(apartment),
		json_string={}
	)
	full_calc_handler(self, fake_call)

def process_last_name(self, message, text: str):
	try:
		# TODO обработчик фамилии
		last_name = message.text.strip().replace(' ', '')
	except ValueError:
		text = '\n'.join(text.split('\n')[:-1]) + '\nОшибка, фамилия не может иметь вид {}. Введите фамилию:'.format(message.text)
		resend_message(self, message, text)
		self.bot.register_next_step_handler(message, lambda message: process_last_name(self, message, text=text))
		return
	self.order_states[message.from_user.id]['last_name'] = last_name
	text = '\n'.join(text.split('\n')[:-1]) + '\n{}: {}'.format(settings.data_humanize['last_name'], last_name or '-') + '\nВведите имя:'
	resend_message(self, message, text)
	self.bot.register_next_step_handler(message, lambda message: process_first_name(self, message, text=text))

def process_first_name(self, message, text: str):
	try:
		# TODO обработчик имени
		first_name = message.text.strip().replace(' ', '')
	except ValueError:
		text = '\n'.join(text.split('\n')[:-1]) + '\nОшибка, имя не может иметь вид {}. Введите имя:'.format(message.text)
		resend_message(self, message, text)
		self.bot.register_next_step_handler(message, lambda message: process_first_name(self, message, text=text))
		return
	self.order_states[message.from_user.id]['first_name'] = first_name
	text = '\n'.join(text.split('\n')[:-1]) + '\n{}: {}'.format(settings.data_humanize['first_name'], first_name or '-') + '\nВведите отчество(или поставьте -):'
	resend_message(self, message, text)
	self.bot.register_next_step_handler(message, lambda message: process_surname(self, message, text=text))

def process_surname(self, message, text: str):
	try:
		# TODO обработчик отчества
		surname = message.text.strip()
		surname = None if surname == '-' else surname
	except ValueError:
		text = '\n'.join(text.split('\n')[:-1]) + '\nОшибка, отчество не может иметь вид {}. Введите отчество(или поставьте -):'.format(message.text)
		resend_message(self, message, text)
		self.bot.register_next_step_handler(message, lambda message: process_surname(self, message, text=text))
		return
	self.order_states[message.from_user.id]['surname'] = surname
	text = '\n'.join(text.split('\n')[:-1]) + '\nОбработка...'
	try:
		self.bot.delete_message(message.from_user.id, self.order_states[message.from_user.id]['message_id'])
	except ApiException:
		self.order_states[message.from_user.id]['message_id'] = None
	bot_message = self.bot.send_message(message.chat.id, text, reply_markup=None, parse_mode='HTML')
	self.order_states[message.from_user.id]['message_id'] = bot_message.message_id
	fake_call = types.CallbackQuery(
		id='fake_call',
		from_user=message.from_user, 
		chat_instance='fake_call',
		message=bot_message, 
		data='surname:{}|заказ'.format(surname or '-'),
		json_string={}
	)
	full_calc_handler(self, fake_call)

def process_phone(self, message, text: str):
	try:
		# TODO обработчик телефона
		phone = message.text.strip().replace(' ', '').replace('-', '')
		if not phone.startswith('+375'):
			raise ValueError('телефон не начинается с +375')
	except ValueError:
		text = '\n'.join(text.split('\n')[:-1]) + '\nОшибка, телефон не может иметь вид {}. Введите телефон:'.format(message.text)
		resend_message(self, message, text)
		self.bot.register_next_step_handler(message, lambda message: process_phone(self, message, text=text))
		return
	self.order_states[message.from_user.id]['phone'] = phone
	text = '\n'.join(text.split('\n')[:-1]) + '\nОбработка...'
	try:
		self.bot.delete_message(message.from_user.id, self.order_states[message.from_user.id]['message_id'])
	except ApiException:
		self.order_states[message.from_user.id]['message_id'] = None
	bot_message = self.bot.send_message(message.chat.id, text, reply_markup=None, parse_mode='HTML')
	self.order_states[message.from_user.id]['message_id'] = bot_message.message_id
	fake_call = types.CallbackQuery(
		id='fake_call',
		from_user=message.from_user, 
		chat_instance='fake_call',
		message=bot_message, 
		data='phone:{}|заказ'.format(phone),
		json_string={}
	)
	full_calc_handler(self, fake_call)

def process_email(self, message, text: str):
	try:
		# TODO обработчик имейла
		email = message.text.strip().replace(' ', '')
		if not email.endswith('@gmail.com'):
			raise ValueError('имейл не заканчивается на @gmail.com')
	except ValueError:
		text = '\n'.join(text.split('\n')[:-1]) + '\nОшибка, имейл не может иметь вид {}. Введите имейл:'.format(message.text)
		resend_message(self, message, text)
		self.bot.register_next_step_handler(message, lambda message: process_email(self, message, text=text))
		return
	self.order_states[message.from_user.id]['email'] = email
	text = '\n'.join(text.split('\n')[:-1]) + '\nОбработка...'
	try:
		self.bot.delete_message(message.from_user.id, self.order_states[message.from_user.id]['message_id'])
	except ApiException:
		self.order_states[message.from_user.id]['message_id'] = None
	bot_message = self.bot.send_message(message.chat.id, text, reply_markup=None, parse_mode='HTML')
	self.order_states[message.from_user.id]['message_id'] = bot_message.message_id
	fake_call = types.CallbackQuery(
		id='fake_call',
		from_user=message.from_user, 
		chat_instance='fake_call',
		message=bot_message, 
		data='email:{}|заказ'.format(email),
		json_string={}
	)
	full_calc_handler(self, fake_call)

def full_calc_handler(self, callback):
	if callback.data.startswith('заказ'):
		# одновременно существует только один полный калькулятор
		if self.order_states.get(callback.from_user.id):
			try:
				self.bot.delete_message(callback.from_user.id, self.order_states[callback.from_user.id]['message_id'])
			except ApiException:
				pass
			del self.order_states[callback.from_user.id]
		# заполнение полей rooms, bathrooms и их отображение вместе со следующим шагом калькулятора
		rooms, bathrooms = map(int, callback.data.split('|')[1].split())
		self.order_states.setdefault(callback.from_user.id, settings.data_default | {'message_id': None})
		self.order_states[callback.from_user.id]['message_id'] = callback.message.message_id
		self.order_states[callback.from_user.id]['rooms'] = rooms
		self.order_states[callback.from_user.id]['bathrooms'] = bathrooms
		message = '<b>Информация об уборке</b>\n<b>{}</b>: {}\n<b>{}</b>: {}\n'.format(settings.data_humanize['rooms'], rooms, settings.data_humanize['bathrooms'], bathrooms)
		self.bot.edit_message_text(message + 'Выберите дату уборки:', chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=keyboards.create_date_field(callback_data='cleaning_date:{}|заказ'), parse_mode='HTML')
	else:
		if callback.data.startswith('назад'):
			_, next_field = callback.data.split('|')[0].split(':', 1)
			message = '\n'.join(callback.message.text.split('\n')[:-2]) + '\n'
			# удаление значения поля
			self.order_states[callback.from_user.id][next_field] = None
			field = settings.data_prev_field[next_field]
		else:
			field, value = callback.data.split('|')[0].split(':', 1)
			message = '\n'.join(callback.message.text.split('\n')[:-1]) + '\n'
			# предобработка значения поля и сохранение значения поля
			try:
				settings.data_field_type[field]
			except KeyError:
				# обработка других полей
				value = bool(value)
				if field == 'адрес':
					if value:
						address = UserProfile.objects.get(id=callback.from_user.id).address.split(',')
						self.order_states[callback.from_user.id]['street'] = street = ' '.join(address.pop(0).split()[1:])
						self.order_states[callback.from_user.id]['house'] = house = ' '.join(address.pop(0).split()[1:])
						if address[0].startswith(' корп.'):
							section = int(address.pop(0).split()[1])
						else:
							section = None
						self.order_states[callback.from_user.id]['section'] = section
						message += '<b>{}</b>: {}\n'.format(settings.data_humanize['street'], street) +\
									'<b>{}</b>: {}\n'.format(settings.data_humanize['house'], house) + '<b>{}</b>: {}\n'.format(settings.data_humanize['section'], section or '-')
						field, value = 'apartment', int(address.pop(0).split()[1])
						address = section = None
					else:
						text = message + '<b>Введите улицу</b>:'
						self.bot.edit_message_text(text, chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=None, parse_mode='HTML')
						self.bot.register_next_step_handler(callback.message, lambda message: process_street(self, message, text=text))
						self.bot.answer_callback_query(callback.id)
						return
				elif field == 'фио':
					if value:
						user =  UserProfile.objects.get(id=callback.from_user.id).user
						self.order_states[callback.from_user.id]['last_name'] = user.last_name
						self.order_states[callback.from_user.id]['first_name'] = user.first_name
						message += '<b>{}</b>: {}\n'.format(settings.data_humanize['last_name'], user.last_name) +\
									'<b>{}</b>: {}\n'.format(settings.data_humanize['first_name'], user.first_name)
						field, value = 'surname', user.surname
						user = None
					else:
						text = message + '<b>Введите фамилию</b>:'
						self.bot.edit_message_text(text, chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=None, parse_mode='HTML')
						self.bot.register_next_step_handler(callback.message, lambda message: process_last_name(self, message, text=text))
						self.bot.answer_callback_query(callback.id)
						return
				elif field == 'телефон':
					if value:
						phone = UserProfile.objects.get(id=callback.from_user.id).phone
						field, value = 'phone', phone
						phone = None
					else:
						text = message + '<b>Введите телефон</b>:'
						self.bot.edit_message_text(text, chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=None, parse_mode='HTML')
						self.bot.register_next_step_handler(callback.message, lambda message: process_phone(self, message, text=text))
						self.bot.answer_callback_query(callback.id)
						return
				elif field == 'имейл':
					if value:
						email = UserProfile.objects.get(id=callback.from_user.id).user.email
						field, value = 'email', email
						email = None
					else:
						text = message + '<b>Введите имейл</b>:'
						self.bot.edit_message_text(text, chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=None, parse_mode='HTML')
						self.bot.register_next_step_handler(callback.message, lambda message: process_email(self, message, text=text))
						self.bot.answer_callback_query(callback.id)
						return
			# сохранить значение поля
			self.order_states[callback.from_user.id][field] = value
			# формирование сообщения
			message += '<b>{}</b>: {}\n'.format(settings.data_humanize[field], value or '-')
			try:
				next_field = settings.data_next_field[field]
			except KeyError:
				next_field = 'заказ'

		match next_field:
			case 'cleaning_date':
				add_text, keyboard = '<b>Выберите дату уборки</b>:', keyboards.create_date_field(callback_data='cleaning_date:{}|заказ')
			case 'cleaning_start_time':
				add_text, keyboard = '<b>Выберите время уборки</b>:', keyboards.create_time_field(callback_data='cleaning_start_time:{}|заказ')
			case 'kitchen':
				add_text, keyboard = '<b>Убрать кухню?</b>', keyboards.create_bool_field(callback_data='kitchen:{}|заказ')
			case 'hall':
				add_text, keyboard = '<b>Убрать коридор?</b>', keyboards.create_bool_field(callback_data='hall:{}|заказ')
			case 'street':
				try:
					address = UserProfile.objects.get(id=callback.from_user.id).address
					add_text, keyboard = '<b>{}</b> - оставить данный адрес уборки?'.format(address), keyboards.create_bool_field(callback_data='адрес:{}|заказ')
					address = None
				except UserProfile.DoesNotExist:
					text = message + '<b>Введите улицу</b>:'
					self.bot.edit_message_text(text, chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=None, parse_mode='HTML')
					self.bot.register_next_step_handler(callback.message, lambda message: process_street(self, message, text=text))
					self.bot.answer_callback_query(callback.id)
					return
			case 'last_name':
				try:
					user = UserProfile.objects.get(id=callback.from_user.id).user
					add_text, keyboard = '<b>{} {} {}</b> - это вы?'.format(user.last_name, user.first_name, user.surname or ''), keyboards.create_bool_field(callback_data='фио:{}|заказ')
					user = None
				except UserProfile.DoesNotExist:
					text = message + '<b>Введите фамилию</b>:'
					self.bot.edit_message_text(text, chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=None, parse_mode='HTML')
					self.bot.register_next_step_handler(callback.message, lambda message: process_last_name(self, message, text=text))
					if callback.id != 'fake_call':
						self.bot.answer_callback_query(callback.id)
					return
			case 'phone':
				try:
					phone = UserProfile.objects.get(id=callback.from_user.id).phone
					add_text, keyboard = '<b>{}</b> - оставить данный телефон для связи?'.format(phone), keyboards.create_bool_field(callback_data='телефон:{}|заказ')
					phone = None
				except UserProfile.DoesNotExist:
					text = message + '<b>Введите телефон</b>:'
					self.bot.edit_message_text(text, chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=None, parse_mode='HTML')
					self.bot.register_next_step_handler(callback.message, lambda message: process_phone(self, message, text=text))
					if callback.id != 'fake_call':
						self.bot.answer_callback_query(callback.id)
					return
			case 'email':
				try:
					email = UserProfile.objects.get(id=callback.from_user.id).user.email
					add_text, keyboard = '<b>{}</b> - оставить данную почту?'.format(email), keyboards.create_bool_field(callback_data='имейл:{}|заказ')
					email = None
				except UserProfile.DoesNotExist:
					text = message + '<b>Введите имейл</b>:'
					self.bot.edit_message_text(text, chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=None, parse_mode='HTML')
					self.bot.register_next_step_handler(callback.message, lambda message: process_email(self, message, text=text))
					if callback.id != 'fake_call':
						self.bot.answer_callback_query(callback.id)
					return
			case 'заказ':
				data = self.order_states.pop(callback.from_user.id)
				message_id = data.pop('message_id')
				if data['surname'] == '-':
					data['surname'] = None
				for field in data.keys():
					match settings.data_field_type[field]:
						case 'bool':
							data[field] = bool(data[field])
						case 'date':
							data[field] = datetime.strptime(data[field], settings.DATE_FORMAT).date()
						case 'time':
							data[field] = datetime.strptime(data[field], settings.TIME_FORMAT).time()
						case 'int':
							if field == 'section' and data[field] is None:
								continue
							data[field] = int(data[field])
				rooms, bathrooms = data.pop('rooms'), data.pop('bathrooms')
				kitchen, hall = data.pop('kitchen'), data.pop('hall')
				try:
					add_text, keyboard = 'Ваш заказ оформлен!\nЖелаете оплатить онлайн?', keyboards.pay_keyboard(callback.from_user.id)
					try:
						user = UserProfile.objects.get(id=callback.from_user.id).user
					except UserProfile.DoesNotExist:
						user = None
					# инициализация форм
					user_form = UserForm(data, instance=user)
					order_form = OrderForm(data)
					user = user_form.save(tg_id=callback.from_user.id)
					order = order_form.save(user=user, rooms=rooms, bathrooms=bathrooms, address=user.profile.address, options={'kitchen': kitchen, 'hall': hall})
					# оплата
					payment_url = self.payment.create_payment(amount=order.price, order_message=message, order_id=order.pk)
					keyboard.add(types.InlineKeyboardButton('Оплатить сейчас', url=payment_url))
					threading.Thread(target=lambda: threads.order_payment(self, callback.from_user.id, message_id, order.pk)).start()
					# self.schedule.add_order(order)
				except Exception as errs:
					raise errs
					print('Ошибки ({}) при оформлении заказа {} пользователя {}'.format(errs, data, callback.from_user.id))
					add_text, keyboard = 'Возникли ошибки при формировании заказа,\nпопробуйте вновь позже или сообщите нам о проблеме!', None

		if next_field not in {settings.data_fields[2], 'заказ'}:
			keyboard.add(types.InlineKeyboardButton('Назад', callback_data='назад:{}|заказ'.format(field)))
		self.bot.edit_message_text(message + add_text, chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=keyboard, parse_mode='HTML')
	if callback.id != 'fake_call':
		self.bot.answer_callback_query(callback.id)
