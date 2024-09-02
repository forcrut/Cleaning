from yoomoney import Client
import requests
from urllib.parse import quote


def authorize(client_id: str, client_secret: str) -> str:
	"""
	Start process of the authorization to the yoomoney for getting access_key
	:param cliend_id: str-id from yoomoney,
	:param cliend_secret: str-secret from yoomoney
	"""
	from yoomoney import Authorize
	
	client = Authorize(
		client_id=secrets.client_id,
		client_secret=secrets.client_secret,
		redirect_uri='https://t.me/Trees_and_cats_bot',
		scope=[
			'account-info',
			'operation-history',
			'operation-details',
			'incoming-transfers',
			'payment-p2p',
			'payment-shop'
		]
	)

def account_info(access_token: str) -> None:
	"""
	Получение информации об аккаунте
	:param access_token: токен для доступа к API yoomoney
	"""
	from yoomoney.exceptions import InvalidToken

	client = Client(access_token)
	try:
		user = client.account_info()
	except InvalidToken:
		print('Неправильный токен или его права не включают просмотр информации аккаунта')
		return
	print("Account number:", user.account)
	print("Account balance:", user.balance)
	print("Account currency code in ISO 4217 format:", user.currency)
	print("Account status:", user.account_status)
	print("Account type:", user.account_type)
	print("Extended balance information:")
	for pair in vars(user.balance_details):
		print("\t-->", pair, ":", vars(user.balance_details).get(pair))
	print("Information about linked bank cards:")
	cards = user.cards_linked
	if len(cards) != 0:
		for card in cards:
			print(card.pan_fragment, " - ", card.type)
	else:
		print("No card is linked to the account")

class Payment:
	"""
	Управление оплатой
	"""
	
	def __init__(self, access_token: str=None):
		"""
		:param access_token: токен для доступа к API
		"""
		if access_token is None:
			from .secrets import access_token

		self.client = Client(access_token)
		self.access_token =  access_token
		self.account = self.client.account_info().account

	def create_payment(self, amount: int, order_message: str, order_id: int) -> tuple:
		"""
		Создание платежа с последующим возвращением url со сроком жизни
		:param amount: сумма платежа,
		:param order_message: перечень услуг и других данных, входящих в заказ,
		:param order_id: id заказа для отображения в истории
		"""
		from yoomoney import Quickpay

		quickpay = Quickpay(
			receiver=self.account,
			quickpay_form="shop",
			targets="Олата услуг Cleaning",
			paymentType="SB",
			sum=amount,
			comment=order_message,
			label='C{}'.format(order_id)
		)

		return quickpay.redirected_url

	def was_paid(self, order_id: int) -> bool:
		"""
		Проверка статуса платежа
		:param order_id: id заказа
		"""
		operation_label = 'C{}'.format(order_id)
		for operation in self.client.operation_history(label=operation_label).operations:
			return operation.status == 'success'
		return False


if __name__ == '__main__':
	import secrets

	payment = Payment(secrets.access_token)

	# print(authorize(secrets.client_id, secrets.client_secret))
	# account_info(secrets.access_token)
	# print(payment.create_payment(100, 'privet', -1))
	# print(payment.was_paid(-1))



# # заголовки
# headers = {
# 	"Authorization": f"Bearer {self.access_token}",
# 	"Content-Type": "application/x-www-form-urlencoded"
# }
# # параметры
# data = {
# 	'pattern_id': 'p2p',
# 	'to': self.account,
# 	'amount': f'{amount:.2f}',
# 	'comment': order_message,
# 	'message': 'Платеж за заказ #{}'.format(order_id),
# 	'label': 'CleaningPay'
# }
# # request-payment запрос
# response = requests.post('https://yoomoney.ru/api/request-payment', headers=headers, data=data)
# print(response.status_code)
# if response.status_code != 200:
# 	raise Exception("Payment-request's status is not success. Payment is not working currently")
# response = response.json()
# print(response)
# request_id = response['request_id']
# return request_id
