from pathlib import Path


# schedule
SCHEDULE_URL = "https://docs.google.com/spreadsheets/d/1hy2TiNg4ck5esCNXF2w2dRcHfIzXiWn5fDWN9i_dX10"
SCHEDULE_COLUMNS = ['id', 'Логин сотрудника', 'Дата', 'Время начала', 'Время оконачния', 'Задачи', 'Телефон', 'Адрес', 'Стоимость', 'Статус']
SCHEDULE_DB_COLUMNS = ['pk', 'staff__username', 'cleaning_date', 'cleaning_start_time', 'cleaning_end_time', 'info', 'user__profile__phone', 'user__profile__address', 'price', 'status']
SCHEDULE_COLUMNS_MAPPING = {sheet_column: db_column for sheet_column, db_column in zip(SCHEDULE_COLUMNS, SCHEDULE_DB_COLUMNS)}

# stuff
STUFF_TYPES = {'одноразовый': 0, 'неодноразовый': 1}

# formats
DATE_FORMAT = '%d-%m-%Y'
TIME_FORMAT = '%H:%M'

# order
ORDER_STATUSES = {'неизвестно': 0, 'оформлен': 1, 'оплачен': 2, 'завершен': 3}

# order's prices
BASE_PRICE = 31
ROOM_PRICE = 14
BATHROOM_PRICE = 20
KITCHEN_PRICE = 50
HALL_PRICE = 10

# order's time
BASE_TIME = 30
ROOM_TIME = 40
BATHROOM_TIME = 30
KITCHEN_TIME = 60
HALL_TIME = 20

# quantity limits
ROOM_LIMIT = 10
BATHROOM_LIMIT = 10

# days
DAY_CHOICES = {
	'Mon': 'Monday',
	'Tue': 'Tuesday',
	'Wed': 'Wednesday',
	'Thu': 'Thursday',
	'Fri': 'Friday',
	'Sat': 'Saturday',
	'Sun': 'Sunday'
}

# paths
BASE_DIR = Path(__file__).resolve().parent
DJANGO_BASE_DIR = BASE_DIR / 'Server'
DJANGO_MANAGE_FILE = DJANGO_BASE_DIR / 'manage.py'
BOT_MAIN_FILE = BASE_DIR / 'Bot' / 'main.py'

# bot's token
BOT_TOKEN = '5303666004:AAHfkjYN_TBqGmL4FxgFXbHXGFz3_g75Caw'

# group's id
GROUP_ID = -1002177036365

# order's data
data_fields = [
	'rooms', 'bathrooms',
	'cleaning_date', 'cleaning_start_time',
	'kitchen', 'hall',
	'street', 'house', 'section', 'apartment',
	'last_name', 'first_name', 'surname',
	'phone', 'email'
]
data_field_type = {k: v for k, v in zip(data_fields, [
	'int', 'int',
	'date', 'time',
	'bool', 'bool',
	'str', 'str', 'int', 'int',
	'str', 'str', 'str',
	'str', 'str'
])}
data_next_field = {k: v for k, v in zip(data_fields[:-1], data_fields[1:])}
data_prev_field = {k: v for k, v in zip(data_fields[1:], data_fields[:-1])}
data_default = dict.fromkeys(data_fields)
data_humanize = {k: v for k, v in zip(data_fields, [
	'Комнат', 'Санузлов',
	'Дата уборки', 'Время уборки',
	'Кухня', 'Коридор',
	'Улица', 'Дом', 'Корпус', 'Квартира',
	'Фамилия', 'Имя', 'Отчество',
	'Мобильный', 'Почта'
])}

# информация об услугах
services = """
	<b>Наши услуги:</b>
	<code>
		<b>Уборка комнаты:</b>
		1.
		2.
	</code>
	<code>
		<b>Уборка санузла:</b>
		1.
		2.
		Примечание:.
	</code>
	<code>
		<b>Уборка кухни:</b>
		1.
		2.
	</code>
	<code>
		<b>Уборка коридора:</b>
		1.
		2.
	</code>
"""

# информация о нас
about = """
	<b>Наша организация:</b>
	<code>
		<b>Название:</b> Cleaning.
	</code>
	<b>Контактные данные:</b>
	<code>
		<b>Телефон:</b> +375*********.
		<b>Email:</b> *******@gmail.com.
	</code>
"""
