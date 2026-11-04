"""
Configurações do projeto Mary House — o único lugar onde o ambiente entra no sistema.

Tudo o que muda entre a máquina do dev e o servidor (banco, chave, DEBUG, hosts) vem de
variável de ambiente pela função env() abaixo; o código do app nunca lê os.environ.

Banco de dados: usa PostgreSQL quando DATABASE_URL está definida; sem ela, cai para um
SQLite local (db.sqlite3). O fallback existe para que clonar o repositório e rodar não
exija subir servidor de banco nenhum — em produção, DATABASE_URL é obrigatória na prática.

Defaults seguros: sem .env o sistema sobe com DEBUG desligado, só para localhost, e
RECUSA subir sem SECRET_KEY. Para desenvolver, ponha DEBUG=True no .env (ver .env.example):
só aí a chave de desenvolvimento embutida passa a valer.
"""
from pathlib import Path
import os

from django.core.exceptions import ImproperlyConfigured

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega variáveis do arquivo .env (se existir e se python-dotenv estiver instalado).
# O import fica num try porque o sistema tem de subir mesmo sem o pacote — nesse caso as
# variáveis têm de vir do ambiente do processo. O silêncio é a armadilha: sem o dotenv,
# o .env é ignorado sem aviso nenhum.
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


def env(key, default=None):
    return os.environ.get(key, default)


# --- Segurança -------------------------------------------------------------
DEBUG = env("DEBUG", "False").lower() in ("1", "true", "yes", "on")

SECRET_KEY = env("SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "SECRET_KEY não definida. Em produção ela é obrigatória; para desenvolver, "
            "use DEBUG=True no .env."
        )
    SECRET_KEY = "dev-inseguro-so-com-debug-0123456789abcdefghijklmnopqrstuv"

ALLOWED_HOSTS = [
    h.strip() for h in (env("ALLOWED_HOSTS") or "localhost,127.0.0.1").split(",") if h.strip()
]
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in env("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

# Fora do desenvolvimento, cookie de sessão e de CSRF só por HTTPS. HSTS e redirecionamento
# para HTTPS ficam para o servidor web, que é quem sabe se há TLS na frente.
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# --- Aplicações ------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Banco de dados --------------------------------------------------------
DATABASE_URL = env("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    # Fallback de desenvolvimento: SQLite, zero configuração.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# --- Validação de senha ----------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internacionalização ---------------------------------------------------
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# --- Arquivos estáticos ----------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Autenticação ----------------------------------------------------------
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"

# Mensagens -> classes CSS
# O template imprime {{ m.tags }} direto como classe do <div class="flash ...">; este mapa é
# o que faz "error" virar .error no styles.css em vez do "danger" que o Django usa por padrão.
from django.contrib.messages import constants as messages  # noqa: E402

MESSAGE_TAGS = {
    messages.DEBUG: "info",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "error",
}
