from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MinLengthValidator
from django.conf import settings
from .models import UserProfile, Order
from datetime import timedelta
from settings import BASE_PRICE, ROOM_PRICE, BATHROOM_PRICE, KITCHEN_PRICE, HALL_PRICE, ROOM_TIME, BATHROOM_TIME, KITCHEN_TIME, HALL_TIME




class OrderForm(forms.ModelForm):

	class Meta:
		model = Order
		fields = ('cleaning_date', 'cleaning_start_time')

	def save(self, user: settings.AUTH_USER_MODEL, rooms: int, bathrooms: int, commit=True, options: dict|None=None) -> Order:
		"""
		Сохранение объекта формы
		:param user: пользователь, который осуществил заказ,
		:param rooms: количество комнат для уборки,
		:param bathrooms: количество санузлов для уборки,
		:param commit: сохранить ли объект в базу данных,
		:param options: допольнительные опции уборки, на данный момент: кухня и коридор
		"""
		order = super().save(commit=False)
		if commit:
			try:
				order.user = user
				order.price = BASE_PRICE + rooms*ROOM_PRICE + bathrooms*BATHROOM_PRICE + options['kitchen']*KITCHEN_PRICE + options['hall']*HALL_PRICE
				order.cleaning_end_time = order.cleaning_start_time + timedelta(minutes=
					rooms*ROOM_TIME + bathrooms*BATHROOM_TIME + options['kitchen']*KITCHEN_TIME + options['hall']*HALL_TIME
				)
				order.info = '{} к. {} с.'.format(rooms, bathrooms) + (' +' if options['kitchen'] or options['hall'] else '')
				if options['kitchen']: order.info += ' кухня'
				if options['hall']: order.info += ', коридор'
				order.save()
			except Exception as err:
				self.add_error(None, f"Ошибка при попытке сохранения заказа: {err}")
				return None
		# возвращаем объект
		return order

class UserForm(UserCreationForm):
	# адрес квартиры
	street = forms.CharField(
		max_length=25,
		required=True,
		widget=forms.TextInput(attrs={'placeholder': 'Улица'})
	)
	house_regex = RegexValidator(
		regex=r'^[1-9]?\w*$',
		message="Examples: 41a, 1108...",
	)
	house = forms.CharField(
		validators=[house_regex],
		required=True,
		widget=forms.TextInput(attrs={'placeholder': 'Дом'})
	)
	section = forms.PositiveIntegerField(
		validators=[MinValueValidator(1)],
		required=False,
		widget=forms.IntegerInput(attrs={'placeholder': 'Корпус'})
	)
	apartment = forms.PositiveIntegerField(
		validators=[MinValueValidator(1)],
		required=True,
		widget=forms.TextInput(attrs={'placeholder': 'Квартира'})
	)
	# контактная информация
	last_name = forms.CharField(
		max_length=30,
		required=True,
		widget=forms.TextInput(attrs={'placeholder': 'Фамилия'})
	)
	first_name = forms.CharField(
		max_length=25,
		required=True,
		widget=forms.TextInput(attrs={'placeholder': 'Имя'})
	)
	surname = forms.CharField(
		max_length=25,
		required=False,
		widget=forms.TextInput(attrs={'placeholder': 'Отчество'})
	)
	phone_regex = RegexValidator(
		regex=r'^\+375?\d{9}$',
		message="Phone number must be entered in the format: '+375999999999'. Only 9 digits allowed after +375.",
	)
	phone = forms.CharField(
		validators=[phone_regex], 
		max_length=13, 
		required=False,
		widget=forms.TextInput(attrs={'placeholder': 'Контактный телефон'}),
	)
	email = forms.EmailField(
		required=True,
		widget=forms.EmailInput(attrs={'placeholder': 'Email'}),
	)

	class Meta:
		model = settings.AUTH_USER_MODEL
		fields = ('last_name', 'first_name', 'surname', 'email')

	def save(self, commit=True, tg_id=None) -> settings.AUTH_USER_MODEL:
		"""
		Сохранение объекта формы
		:param commit: сохранить ли объект в базу данных,
		:param tg_id: телеграм id пользователя
		"""
		if not tg_id:
			raise ValueError('The tg_id must be transferred')
		user = super().save(commit=False)
		if commit:
			# сюда try USERNAME может быть None
			try:
				# транзакция
				with transaction.atomic():
					user_profile, created = UserProfile.objects.get_or_create(id=tg_id)
					# если новый пользователь
					if created:
						user.save()
						user_profile.user = user
					else:
						user = user_profile.user
						for field in self.cleaned_data:
							if hasattr(user, field) and self.cleaned_data[field]:
								setattr(user, field, self.cleaned_data[field])
						user.save()
					# телефон
					user_profile.phone = self.cleaned_data.get('phone')
					# адрес
					user_profile.address = 'Ул. {}, д. {}, кв. {}'.format(self.street, self.house, self.apartment)
					if self.section:
						user_profile.address += ', корп. {}'.format(self.section)
					# сохранить изменения
					user_profile.save()
			except Exception as err:
				self.add_error(None, f"Ошибка при попытке сохранения контактной информации: {err}")
				return None
		# возвращаем объект
		return user
