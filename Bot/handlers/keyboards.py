from telebot import types
from django.utils import timezone
from datetime import datetime, timedelta
from settings import DATE_FORMAT

# Keybord-function

# поля
def create_date_field(callback_data: str):
	field, date = types.InlineKeyboardMarkup(row_width=4), timezone.now().date()
	for _ in range(8):
		row = []
		for _ in range(4):
			date += timedelta(days=1)
			row.append(types.InlineKeyboardButton(date.strftime(DATE_FORMAT), callback_data=callback_data.format(date.strftime(DATE_FORMAT))))
		field.add(*row)
	return field

def create_time_field(callback_data: str):
	field = types.InlineKeyboardMarkup()
	time_strs = [f'{hour:02d}:{minute:02d}' for hour in range(9, 18) for minute in [0, 30]]
	for _ in range(6):
		row = []
		for _ in range(3):
			time_str = time_strs.pop(0)
			row.append(types.InlineKeyboardButton(time_str, callback_data=callback_data.format(time_str)))
		field.add(*row)
	return field

def create_bool_field(callback_data: str):
	field = types.InlineKeyboardMarkup()
	field.add(
		types.InlineKeyboardButton('Да', callback_data=callback_data.format('Да')),
		types.InlineKeyboardButton('Нет', callback_data=callback_data.format(''))
	)
	return field

# оплата
def pay_keyboard(profile_id: int):
	keyboard = types.InlineKeyboardMarkup()
	return keyboard

def history_keyboard(order_id: int, review: bool=True):
	keyboard = types.InlineKeyboardMarkup()
	if review:
		keyboard.add(
			types.InlineKeyboardButton('Оставить отзыв', callback_data='отзыв|{}'.format(order_id))
		)
	keyboard.add(
		types.InlineKeyboardButton('Оставить жалобу', callback_data='жалоба|{}'.format(order_id))
	)
	return keyboard

def order_take_keyboard(order_id: int, callback_data='взять|{}'):
	keyboard = types.InlineKeyboardMarkup()
	keyboard.add(
		types.InlineKeyboardButton('Взять заказ', callback_data=callback_data.format(order_id))
	)
	return keyboard

# Factory

def keyboard_factory(rooms: int=1, bathrooms: int=1, callback_data='{}|{} {}'):
	short_calc = types.InlineKeyboardMarkup()
	rooms_ending = 'а' if rooms == 1 else ('ы' if rooms < 5 else '')
	bathrooms_ending = 'ел' if bathrooms == 1 else ('ла' if bathrooms < 5 else 'лов')
	for value, place in [(rooms, 'комнат' + rooms_ending), (bathrooms, 'сануз' + bathrooms_ending)]:
		short_calc.add(
			types.InlineKeyboardButton('-', callback_data=callback_data.format(place + '-', rooms, bathrooms)), 
			types.InlineKeyboardButton('{} {}'.format(value, place), callback_data='no_action'), 
			types.InlineKeyboardButton('+', callback_data=callback_data.format(place + '+', rooms, bathrooms))
		)
	short_calc.add(types.InlineKeyboardButton('Рассчитать уборку', callback_data=callback_data.format('заказ', rooms, bathrooms)))
	return short_calc
short_calc_keyboards = [[keyboard_factory(i, j) for j in range(1, 11)] for i in range(1, 11)]
keyboard_factory = None
