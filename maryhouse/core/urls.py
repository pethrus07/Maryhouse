"""As rotas do sistema — o índice de tudo o que existe.

Vinte e três rotas em seis blocos: o painel na raiz, a autenticação, um bloco por
entidade (lista, novo, editar, remover e, onde faz sentido, exportar) e os relatórios.
Todos os caminhos são fixos ou com <int:pk>; não há curinga, então a ordem das linhas
não muda o resultado.
Os nomes (contratante_list, agendamento_update...) são contrato com os templates:
crud/list.html recebe o nome da rota como string e resolve com a tag url.
"""
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),

    # Autenticação
    path("login/", auth_views.LoginView.as_view(
        template_name="registration/login.html", redirect_authenticated_user=True,
    ), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Contratantes
    path("contratantes/", views.ContratanteList.as_view(), name="contratante_list"),
    path("contratantes/novo/", views.ContratanteCreate.as_view(), name="contratante_create"),
    path("contratantes/<int:pk>/editar/", views.ContratanteUpdate.as_view(), name="contratante_update"),
    path("contratantes/<int:pk>/remover/", views.ContratanteDelete.as_view(), name="contratante_delete"),
    path("contratantes/exportar/", views.ExportContratantesCSV.as_view(), name="contratante_export"),

    # Prestadoras
    path("prestadoras/", views.PrestadoraList.as_view(), name="prestadora_list"),
    path("prestadoras/nova/", views.PrestadoraCreate.as_view(), name="prestadora_create"),
    path("prestadoras/<int:pk>/editar/", views.PrestadoraUpdate.as_view(), name="prestadora_update"),
    path("prestadoras/<int:pk>/remover/", views.PrestadoraDelete.as_view(), name="prestadora_delete"),
    path("prestadoras/exportar/", views.ExportPrestadorasCSV.as_view(), name="prestadora_export"),

    # Serviços
    path("servicos/", views.ServicoList.as_view(), name="servico_list"),
    path("servicos/novo/", views.ServicoCreate.as_view(), name="servico_create"),
    path("servicos/<int:pk>/editar/", views.ServicoUpdate.as_view(), name="servico_update"),
    path("servicos/<int:pk>/remover/", views.ServicoDelete.as_view(), name="servico_delete"),

    # Agendamentos
    path("agendamentos/", views.AgendamentoList.as_view(), name="agendamento_list"),
    path("agendamentos/novo/", views.AgendamentoCreate.as_view(), name="agendamento_create"),
    path("agendamentos/<int:pk>/editar/", views.AgendamentoUpdate.as_view(), name="agendamento_update"),
    path("agendamentos/<int:pk>/remover/", views.AgendamentoDelete.as_view(), name="agendamento_delete"),
    path("agendamentos/exportar/", views.ExportAgendamentosCSV.as_view(), name="agendamento_export"),

    # Relatórios
    path("relatorios/", views.RelatoriosView.as_view(), name="relatorios"),
]
