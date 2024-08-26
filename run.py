import requests
import os
import sys
import subprocess
import time
from settings import BASE_DIR, DJANGO_MANAGE_FILE, BOT_MAIN_FILE


def wait_for_django(port=8000, timeout=30):
	start_time = time.time()
	while True:
		try:
			response = requests.get(f'http://localhost:{port}')
			if response.status_code == 200:
				break
		except requests.ConnectionError:
			pass

		if time.time() - start_time > timeout:
			raise Exception(f'Django server did not start within {timeout} seconds!')
		time.sleep(1)

if __name__ == '__main__':
	try:
		# запуск процессов с django и ботом
		djang_process = subprocess.Popen([sys.executable, DJANGO_MANAGE_FILE, 'runserver', '8000'], cwd=os.path.abspath(BASE_DIR))
		wait_for_django()
		bot_process = subprocess.Popen([sys.executable, '-m', 'Bot.main'])
		# ожидание окончания процессов
		djang_process.wait()
		bot_process.wait()
	except KeyboardInterrupt:
		# закрытие процессов
		djang_process.terminate()
		bot_process.terminate()
		# ождание закрытия процессов
		djang_process.wait()
		bot_process.wait()
		# завершение программы
		sys.exit(0)
