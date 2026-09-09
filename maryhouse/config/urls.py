"""URLs raiz do projeto Mary House.

Divide o mundo em duas metades e nada mais: /admin/ e todo o resto.
O sistema inteiro (painel, cadastros, agendamentos, relatórios) mora em core.urls,
montado na raiz — não há prefixo /app/ nem versão de API para carregar.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
]
