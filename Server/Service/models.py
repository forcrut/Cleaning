from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import uuid
from django.conf import settings
from django.core.validators import RegexValidator
from django.core.validators import MinValueValidator, MinLengthValidator
from django.core.exceptions import ValidationError
from settings import ORDER_STATUSES, SCHEDULE_DB_COLUMNS, DAY_CHOICES, STUFF_TYPES

# Custom user manager

class UserProfile:
	pass

class StaffStorage:
	pass

class CustomUserManager(BaseUserManager):
	def create_user(self, username=None, password=None, tg_id=None, **extra_fields):
		# валидатор
		if not username and (self.is_staff or self.is_superuser):
			raise ValueError('The Username field must be set')
		if not extra_fields.get('email'):
			raise ValueError('The Email field must be set')
		if not tg_id and not self.is_superuser:
			raise ValueError('The telegram id must be sent')
		extra_fields.setdefault('is_staff', False)
		extra_fields.setdefault('is_superuser', False)
		extra_fields.setdefault('is_active', True)
		user = self.model(username=username, **extra_fields)
		# установка пароля только суперпользователю
		if user.is_superuser:
			if not password:
				raise ValueError('The Password field must be set for superusers')
			user.set_password(password)
		else:
			user.password = None
		user.save(using=self._db)
		# дополнительные сущности
		if not user.is_staff:
			UserProfile.objects.create(id=tg_id, user=user)
		elif not user.is_superuser:
			StaffStorage.objects.create(id=tg_id, staff=user)
		return user

	def create_staff(self, username, password=None, tg_id=None, **extra_fields):
		extra_fields['is_staff'] = True
		extra_fields['is_superuser'] = False
		return self.create_user(username, password, tg_id, **extra_fields)

	def create_superuser(self, username, password=None, **extra_fields):
		extra_fields['is_staff'] = extra_fields['is_superuser'] = True
		return self.create_user(username, password, **extra_fields)

# Create your models here.

class CustomUser(AbstractUser):
	username = models.CharField(max_length=15, verbose_name='Логин', null=True, unique=True)
	email_regex = RegexValidator(
		regex=r'@gmail.com$',
		message="Email must be from the domain 'gmail.com'.",
	)
	email = models.EmailField(max_length=40, validators=[email_regex], verbose_name="Почта", unique=True)
	last_name = models.CharField(max_length=30, verbose_name='Фамилия')
	first_name = models.CharField(max_length=30, verbose_name='Имя')
	surname = models.CharField(max_length=30, verbose_name='Отчество', blank=True, null=True)
	creation_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания', blank=True, null=True)
	objects = CustomUserManager()

	class Meta:
		verbose_name = "Пользователь"
		verbose_name_plural = "Пользователи"

	def ban(self):
		if self.is_staff or self.is_superuser:
			raise ValueError('You can not ban employee')
		self.is_active = False

	def __str__(self):
		role = 'User'
		if self.is_superuser:
			role = 'Superuser'
		elif self.is_staff:
			role = 'Staff'
		return '{}: {} {} {}'.format(role, self.last_name, self.first_name, self.surname)

	def save(self, *args, **kwargs):
		super().clean()
		user = super().save(*args, **kwargs)
		# TODO создание рабочих дней, если таковых нет
		# # рабочие дни, если пользователь - сотрудник
		# if not self.pk and self.is_staff and not self.is_superuser:
		# 	[WorkDay.objects.create(staff=user, day=day, is_working=not(day in ('Sat', 'Sun'))) for day in DAY_CHOICES.keys()]
		return user

class StaffUser(CustomUser):

	class Meta:
		proxy = True
		verbose_name = "Сотрудник"
		verbose_name_plural = "Персонал"

class UserProfile(models.Model):
	id = models.PositiveIntegerField(primary_key=True, editable=True, verbose_name='tg id')
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
	phone = models.CharField(max_length=15, blank=True, null=True, verbose_name='Мобильный')
	address = models.CharField(max_length=100, validators=[MinLengthValidator(10)], verbose_name='Адрес')

	class Meta:
		verbose_name = "Профиль"
		verbose_name_plural = "Профили"

	def __str__(self):
		return 'Profile of the ' + str(self.user)

# TODO оборудование
class StaffStorage(models.Model):
	id = models.PositiveIntegerField(primary_key=True, editable=True, verbose_name='tg id')
	staff = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='storage', verbose_name='Сотрудник')
# 	stuff = models.OneToOneField('Stuff', on_delete=models.SET_NULL, related_name='staffes', verbose_name='Товар')
# 	quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name='Количество')

	class Meta:
		verbose_name = "Оборудование сотрудника"
		verbose_name_plural = "Оборудование сотрудников"

	def __str__(self):
		return 'Storage of the ' + str(self.staff)

class WorkDay(models.Model):
	staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Сотрудник')
	day = models.CharField(max_length=3, choices=DAY_CHOICES, verbose_name='День недели')
	is_working = models.BooleanField(default=True, verbose_name='Рабочий день')

	class Meta:
		unique_together = ('staff', 'day')
		verbose_name = "Рабочий день"
		verbose_name_plural = "Рабочие дни"

	def clean(self):
		super().clean()
		# валидатор
		if not getattr(self, 'staff', None):
			raise ValidationError("Field staff must be set.")
		elif self.staff.is_superuser or not self.staff.is_staff:
			raise ValidationError({'staff': "User can be only the staff."})

	def __str__(self):
		return '{} is {} working'.format(self.day, '' if self.is_working else 'not')

# TODO оборудование
# class Stuff(models.Model):
# 	name = models.CharField(max_length=30, verbose_name='Оборудование')
# 	firm = models.CharField(max_length=35, verbose_name='Фирма оборудования')
# 	stuff_type = models.CharField(max_length=13, choices=STUFF_TYPES, verbose_name='Вид оборудования')
# 	cost = models.FloatField(validators=[MinValueValidator(0.01)], verbose_name='Цена')

# 	def __str__(self):
# 		return 'Stuff {}, firm {}, stuff_type {}, cost {}'.format(self.name, self.firm, self.stuff_type, self.cost)

class Order(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name='user_orders', verbose_name='Пользователь')
	order_time = models.DateField(auto_now_add=True, verbose_name='Дата оформления')
	cleaning_date = models.DateField(verbose_name='Дата')
	cleaning_start_time = models.TimeField(verbose_name='Время начала')
	cleaning_end_time = models.TimeField(verbose_name='Время окончания')
	info = models.CharField(max_length=70, verbose_name='Задачи')
	price = models.FloatField(validators=[MinValueValidator(1.0)], verbose_name='Цена')
	status = models.SmallIntegerField(choices=ORDER_STATUSES, default=1, verbose_name='Статус')
	staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='staff_orders', verbose_name='Сотрудник')
	# TODO оборудование
	# stuff = models.ForeignKey(Stuff, on_delete=models.SET_NULL, related_name='orders_stuff', verbose_name='Оборудование')

	class Meta:
		verbose_name = "Заказ"
		verbose_name_plural = "Заказы"

	def to_schedule(self) -> list:
		"""
		Преобразование данных заказа к необходимому виду графика работы
		"""
		to_send = []
		for column in SCHEDULE_DB_COLUMNS:
			column = column.split('__')
			if len(column) == 1:
				to_send.append(getattr(self, column[0]))
			else:
				related_obj = self
				for sub_field in column:
					related_obj = getattr(related_obj, sub_field)
				to_send.append(related_obj)
			
		return to_send

	def __str__(self):
		return 'From ' + str(self.user) + ' on {}, {}-{}'.format(self.cleaning_date, self.cleaning_start_time, self.cleaning_end_time)
