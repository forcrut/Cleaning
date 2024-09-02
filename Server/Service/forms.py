from django import forms
from django.db import transaction
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MinLengthValidator
from django.conf import settings
from .models import UserProfile, Order
from datetime import datetime, timedelta
from settings import BASE_PRICE, ROOM_PRICE, BATHROOM_PRICE, KITCHEN_PRICE, HALL_PRICE, ROOM_TIME, BATHROOM_TIME, KITCHEN_TIME, HALL_TIME
from django.contrib.auth import get_user_model


class OrderForm(forms.ModelForm):

	class Meta:
		model = Order
		fields = ('cleaning_date', 'cleaning_start_time')

	def save(self, user: settings.AUTH_USER_MODEL, rooms: int, bathrooms: int, address: str, options: dict|None=None, commit: bool=True) -> Order:
		"""
		Сохранение объекта формы
		:param user: пользователь, который осуществил заказ,
		:param rooms: количество комнат для уборки,
		:param bathrooms: количество санузлов для уборки,
		:param address: адрес уборки 'Ул. *, д. *, (корп. *, )кв *',
		:param options: допольнительные опции уборки, на данный момент: кухня и коридор,
		:param commit: сохранить ли объект в базу данных
		"""
		self.is_valid()
		order = Order(
			cleaning_date=self.cleaned_data.get('cleaning_date'),
			cleaning_start_time=self.cleaned_data.get('cleaning_start_time'),
			user=user,
			status=1
		)
		if commit:
			try:
				order.price = BASE_PRICE + rooms*ROOM_PRICE + bathrooms*BATHROOM_PRICE + options['kitchen']*KITCHEN_PRICE + options['hall']*HALL_PRICE
				order.cleaning_end_time = (
					datetime.combine(datetime.today(), order.cleaning_start_time) + timedelta(minutes=
					rooms*ROOM_TIME + bathrooms*BATHROOM_TIME + options['kitchen']*KITCHEN_TIME + options['hall']*HALL_TIME)
				).time()
				order.info = '{} к. {} с.'.format(rooms, bathrooms) + (' +' if options['kitchen'] or options['hall'] else '')
				if options['kitchen']: order.info += ' кухня'
				if options['hall']: order.info += ', коридор'
				order.address = address
				order.save()
			except Exception as errs:
				print(errs)
				self.add_error(None, f"Ошибка при попытке сохранения заказа: {errs}")
				return None
		# возвращаем объект
		return order

class UserForm(forms.ModelForm):
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
	section = forms.IntegerField(
		validators=[MinValueValidator(1)],
		required=False,
		widget=forms.NumberInput(attrs={'placeholder': 'Корпус'})
	)
	apartment = forms.IntegerField(
		validators=[MinValueValidator(1)],
		required=True,
		widget=forms.NumberInput(attrs={'placeholder': 'Квартира'})
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
	phone = forms.CharField(
		max_length=13, 
		required=False,
		widget=forms.TextInput(attrs={'placeholder': 'Контактный телефон'}),
	)
	email = forms.EmailField(
		required=True,
		widget=forms.EmailInput(attrs={'placeholder': 'Email'}),
	)

	class Meta:
		model = get_user_model()
		fields = ('last_name', 'first_name', 'surname', 'email')

	def __init__(self, *args, ** kwargs):
		"""
		Инициализация формы, установка значений по умолчанию
		:param instance: пользователь
		"""
		# получение user, если передан
		instance = kwargs.get('instance', None)
		super().__init__(*args, **kwargs)
		if instance:
			profile = instance.profile
			address = profile.address.split(',')
			self.fields['street'].initial = ' '.join(address.pop(0).split()[1:])
			self.fields['house'].initial = ' '.join(address.pop(0).split()[1:])
			if address[0].startswith(' корп.'):
				self.fields['section'].initial = int(address.pop(0).split()[1])
			self.fields['apartment'].initial = int(address.pop(0).split()[1])

	def save(self, commit=True, tg_id=None) -> settings.AUTH_USER_MODEL:
		"""
		Сохранение объекта формы
		:param commit: сохранить ли объект в базу данных,
		:param tg_id: телеграм id пользователя
		"""
		self.is_valid()
		if not tg_id:
			raise ValueError('The tg_id must be transferred')
		user = get_user_model()(
			last_name=self.cleaned_data.get('last_name'),
			first_name=self.cleaned_data.get('first_name'),
			surname=self.cleaned_data.get('surname'),
			email=self.cleaned_data.get('email')
		)
		if commit:
			try:
				# транзакция
				with transaction.atomic():
					try:
						user_profile = UserProfile.objects.get(id=tg_id)
						user = user_profile.user
						for field in self.cleaned_data:
							if hasattr(user, field) and self.cleaned_data[field]:
								setattr(user, field, self.cleaned_data[field])
						user.save()
					except UserProfile.DoesNotExist:
						# если новый пользователь
						user.save()
						user_profile = UserProfile.objects.create(id=tg_id, user=user)
					# телефон
					user_profile.phone = self.cleaned_data.get('phone')
					# адрес
					user_profile.address = 'Ул. {}, д. {}'.format(self.cleaned_data.get('street'), self.cleaned_data.get('house'))
					if self.cleaned_data.get('section'):
						user_profile.address += ', корп. {}'.format(self.cleaned_data.get('section'))
					user_profile.address += ', кв. {}'.format(self.cleaned_data.get('apartment'))
					# сохранить изменения
					user_profile.save()
			except Exception as err:
				self.add_error(None, f"Ошибка при попытке сохранения контактной информации: {err}")
				return None
		# возвращаем объект
		return user
