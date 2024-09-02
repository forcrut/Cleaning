import os
import sys
from settings import DJANGO_BASE_DIR
sys.path.insert(1, os.path.abspath(DJANGO_BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Server.settings')
import django
django.setup()