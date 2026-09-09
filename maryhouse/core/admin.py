"""Os cinco modelos no Django admin — a porta dos bastidores.

Existe para o que as telas do sistema não fazem: criar usuário, corrigir dado à mão,
inspecionar o histórico. NÃO é a interface do dia a dia — essa é o site em core/views.py.
Cuidado: o que se edita aqui não gera LogAtividade, porque o log é escrito pelo
LogMixin das views do site.
"""
from django.contrib import admin

from .models import Agendamento, Contratante, LogAtividade, Prestadora, Servico


@admin.register(Contratante)
class ContratanteAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone", "email", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "email", "telefone")


@admin.register(Prestadora)
class PrestadoraAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone", "especialidades", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "email", "especialidades")


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "preco", "duracao_minutos", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome",)


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ("data", "hora", "contratante", "prestadora", "servico", "status", "valor")
    list_filter = ("status", "data", "prestadora")
    search_fields = ("contratante__nome", "prestadora__nome", "servico__nome")
    date_hierarchy = "data"
    autocomplete_fields = ()


@admin.register(LogAtividade)
class LogAtividadeAdmin(admin.ModelAdmin):
    list_display = ("data_hora", "usuario", "acao", "entidade", "descricao")
    list_filter = ("acao", "entidade")
    readonly_fields = ("data_hora",)
