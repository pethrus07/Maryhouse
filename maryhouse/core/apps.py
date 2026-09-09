"""Configuração do app core — o único app do projeto.

O verbose_name "Mary House" é o que aparece como título da seção no /admin/;
sem ele o Django mostraria "Core", que não diz nada para quem usa.
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Mary House"
