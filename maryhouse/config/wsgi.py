"""Ponto de entrada WSGI do Mary House.

É o objeto que Gunicorn/uWSGI carregam em produção (config.wsgi:application).
Em desenvolvimento o runserver usa este mesmo caminho, então ele nunca fica sem teste.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
