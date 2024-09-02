import gspread
from gspread.utils import rowcol_to_a1
from settings import SCHEDULE_URL, ORDER_STATUSES, SCHEDULE_COLUMNS_MAPPING, SCHEDULE_DB_COLUMNS
import warnings


# TODO Возможно, следует добавить ограничения на использование
class ScheduleController:
	"""
	Контроллер взаимодействия с графиком работы
	"""

	def __init__(self):
		self.client = gspread.service_account(filename='gs_account.json')
		self.spreadsheet = self.client.open_by_url(SCHEDULE_URL).worksheet('schedule')

	def add_order(self, order: 'Order') -> 'Order':
		"""
		Добавить новый заказ в график работы
		:param order: экземпляр класса Order, содержащий информацию о заказе
		"""
		# TODO не выгружать все сразу
		# получение и преобразование всех записей
		all_records = {SCHEDULE_COLUMNS_MAPPING.get(k, k): v for k, v in record.items() for record in self.spreadsheet.get_all_records()}
		# поиск нужной строки
		row = 2
		for record in all_records:
			if not record.get('cleaning_date') or not record.get('cleaning_start_time'):
				warnings.warn(f"Schedule: Bad record {record}")
				continue
			if record['cleaning_date'] > order.cleaning_date and record['cleaning_start_time'] > order.cleaning_start_time:
				row += 1
				continue
			else:
				break
		all_records = None
		# вставка новой строки
		self.spreadsheet.insert_row(order.to_schedule(), index=row)
		# валидатор статуса
		validation_rule = {
			"source": ORDER_STATUSES.values(),
			"strict": True,
			"showCustomUi": True
		}
		worksheet.set_data_validation(rowcol_to_a1(row, SCHEDULE_DB_COLUMNS.index('status') + 1), validation_rule)
		# возвращает объект заказа
		return order

	def give_access(self, email: str, role: str):
		"""
		Выдать определенный права и доступ к графику работы
		:param email: почта того, кому выдаются права
		:param role: вид прав, которые получит этот пользователь ('reader', 'commenter', 'writer')
		Примечание:
			role 'owner' недоступна
		"""
		self.spreadsheet.share(email, perm_type='user', role=role)
