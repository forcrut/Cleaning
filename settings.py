from pathlib import Path


# schedule
SCHEDULE_URL = "https://docs.google.com/spreadsheets/d/1hy2TiNg4ck5esCNXF2w2dRcHfIzXiWn5fDWN9i_dX10"
SCHEDULE_COLUMNS = ['id', 'Логин сотрудника', 'Дата', 'Время начала', 'Время оконачния', 'Задачи', 'Телефон', 'Адрес', 'Стоимость', 'Статус']
SCHEDULE_DB_COLUMNS = ['pk', 'staff__username', 'cleaning_date', 'cleaning_start_time', 'cleaning_end_time', 'info', 'user__profile__phone', 'user__profile__address', 'price', 'status']
SCHEDULE_COLUMNS_MAPPING = {sheet_column: db_column for sheet_column, db_column in zip(SCHEDULE_COLUMNS, SCHEDULE_DB_COLUMNS)}

# stuff
STUFF_TYPES = {'одноразовый': 0, 'неодноразовый': 1}

# order
ORDER_STATUSES = {'неизвестно': 0, 'оформлен': 1, 'оплачен': 2, 'завершен': 3}
ORDER_SEQUENCE = {
	0: ['rooms', 'Комнат', 'int'],
	1: ['bathrooms', 'Санузел', 'int'],
	2: ['cleaning_date', 'Дата уборки', 'date'],
	3: ['cleaning_start_time', 'Время уборки', 'time'],
	4: ['kitchen', 'Кухня', 'bool'],
	5: ['hall', 'Коридор', 'bool'],
	6: ['street', 'Улица', 'char'],
	7: ['house', 'Дом', 'char'],
	8: ['section', 'Корпус', 'int'],
	9: ['apartment', 'Квартира', 'int'],
	10: ['last_name', 'Фамилия', 'char'],
	11: ['first_name', 'Имя', 'char'],
	12: ['surname', 'Отчество', 'char'],
	13: ['phone', 'Контактный телефон', 'char'],
	14: ['email', 'Почта', 'char']
}

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

# bot
BOT_TOKEN = '5303666004:AAHfkjYN_TBqGmL4FxgFXbHXGFz3_g75Caw'
default_info = dict.fromkeys([
	'message_id',
	'rooms', 'bathrooms',
	'cleaning_date', 'cleaning_start_time', 
	'kitchen', 'hall',
	'street', 'house', 'section', 'apartment',
	'last_name', 'first_name', 'surname',
	'phone', 'email'
])
# message_id для того, чтобы потом можно было удалить это сообщение по истечению какого-то времени и удалить из order_states
