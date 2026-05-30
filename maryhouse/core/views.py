"""Views do Mary House."""
import csv
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, ListView, TemplateView, UpdateView,
)

from .forms import (
    AgendamentoForm, ContratanteForm, PrestadoraForm, ServicoForm,
)
from .models import (
    Agendamento, Contratante, LogAtividade, Prestadora, Servico,
)


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------
class LogMixin:
    """Registra a ação no histórico de atividades."""

    log_entidade = ""

    def _log(self, acao, obj):
        LogAtividade.objects.create(
            usuario=self.request.user if self.request.user.is_authenticated else None,
            acao=acao,
            entidade=self.log_entidade,
            descricao=str(obj)[:255],
        )


class CrudContextMixin:
    """Injeta rótulos usados pelos templates genéricos."""

    titulo = ""
    singular = ""
    list_url = ""
    colunas = []          # [(label, atributo_ou_callable)]
    cadastrar_url = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            titulo=self.titulo,
            singular=self.singular,
            list_url=self.list_url,
            cadastrar_url=self.cadastrar_url,
            secao=self.secao,
        )
        return ctx


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"
    secao = "dashboard"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hoje = timezone.localdate()

        ctx["total_agendamentos"] = Agendamento.objects.count()
        ctx["total_contratantes"] = Contratante.objects.filter(ativo=True).count()
        ctx["total_prestadoras"] = Prestadora.objects.filter(ativo=True).count()
        ctx["total_servicos"] = Servico.objects.filter(ativo=True).count()

        ctx["agendamentos_hoje"] = (
            Agendamento.objects.filter(data=hoje)
            .select_related("contratante", "prestadora", "servico")
            .order_by("hora")
        )

        ctx["proximos"] = (
            Agendamento.objects.filter(
                data__gte=hoje,
                status__in=[Agendamento.Status.PENDENTE, Agendamento.Status.CONFIRMADO],
            )
            .select_related("contratante", "prestadora", "servico")
            .order_by("data", "hora")[:6]
        )

        # Distribuição por status (para o gráfico de rosca)
        por_status = {s: 0 for s, _ in Agendamento.Status.choices}
        for row in Agendamento.objects.values("status").annotate(n=Count("id")):
            por_status[row["status"]] = row["n"]
        ctx["status_labels"] = [label for _, label in Agendamento.Status.choices]
        ctx["status_data"] = [por_status[s] for s, _ in Agendamento.Status.choices]

        # Agendamentos nos últimos 6 meses (gráfico de barras)
        meses, labels, valores = [], [], []
        ref = hoje.replace(day=1)
        for i in range(5, -1, -1):
            ano = ref.year
            mes = ref.month - i
            while mes <= 0:
                mes += 12
                ano -= 1
            meses.append((ano, mes))
        nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                 "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        for ano, mes in meses:
            labels.append(f"{nomes[mes - 1]}/{str(ano)[2:]}")
            valores.append(
                Agendamento.objects.filter(data__year=ano, data__month=mes).count()
            )
        ctx["meses_labels"] = labels
        ctx["meses_data"] = valores

        # Faturamento estimado dos concluídos no mês corrente
        ctx["faturamento_mes"] = (
            Agendamento.objects.filter(
                status=Agendamento.Status.CONCLUIDO,
                data__year=hoje.year, data__month=hoje.month,
            ).aggregate(total=Sum("valor"))["total"] or 0
        )
        return ctx


# ---------------------------------------------------------------------------
# Listas (com busca e filtros)
# ---------------------------------------------------------------------------
class ContratanteList(LoginRequiredMixin, CrudContextMixin, ListView):
    model = Contratante
    paginate_by = 12
    template_name = "crud/list.html"
    titulo = "Contratantes"
    singular = "Contratante"
    secao = "contratantes"
    list_url = "contratante_list"
    cadastrar_url = "contratante_create"
    colunas = [("Nome", "nome"), ("Telefone", "telefone"),
               ("E-mail", "email"), ("Situação", "_situacao")]

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(nome__icontains=q) | Q(email__icontains=q)
                           | Q(telefone__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["colunas"] = self.colunas
        ctx["q"] = self.request.GET.get("q", "")
        ctx["edit_url"] = "contratante_update"
        ctx["delete_url"] = "contratante_delete"
        return ctx


class PrestadoraList(LoginRequiredMixin, CrudContextMixin, ListView):
    model = Prestadora
    paginate_by = 12
    template_name = "crud/list.html"
    titulo = "Prestadoras"
    singular = "Prestadora"
    secao = "prestadoras"
    list_url = "prestadora_list"
    cadastrar_url = "prestadora_create"
    colunas = [("Nome", "nome"), ("Telefone", "telefone"),
               ("Especialidades", "especialidades"), ("Situação", "_situacao")]

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(nome__icontains=q) | Q(especialidades__icontains=q)
                           | Q(telefone__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["colunas"] = self.colunas
        ctx["q"] = self.request.GET.get("q", "")
        ctx["edit_url"] = "prestadora_update"
        ctx["delete_url"] = "prestadora_delete"
        return ctx


class ServicoList(LoginRequiredMixin, CrudContextMixin, ListView):
    model = Servico
    paginate_by = 12
    template_name = "crud/list.html"
    titulo = "Serviços"
    singular = "Serviço"
    secao = "servicos"
    list_url = "servico_list"
    cadastrar_url = "servico_create"
    colunas = [("Nome", "nome"), ("Preço", "_preco"),
               ("Duração", "_duracao"), ("Situação", "_situacao")]

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(nome__icontains=q) | Q(descricao__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["colunas"] = self.colunas
        ctx["q"] = self.request.GET.get("q", "")
        ctx["edit_url"] = "servico_update"
        ctx["delete_url"] = "servico_delete"
        return ctx


class AgendamentoList(LoginRequiredMixin, CrudContextMixin, ListView):
    model = Agendamento
    paginate_by = 12
    template_name = "crud/list_agendamentos.html"
    titulo = "Agendamentos"
    singular = "Agendamento"
    secao = "agendamentos"
    list_url = "agendamento_list"
    cadastrar_url = "agendamento_create"

    def get_queryset(self):
        qs = (super().get_queryset()
              .select_related("contratante", "prestadora", "servico"))
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        if q:
            qs = qs.filter(Q(contratante__nome__icontains=q)
                           | Q(prestadora__nome__icontains=q)
                           | Q(servico__nome__icontains=q))
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["status_atual"] = self.request.GET.get("status", "")
        ctx["status_choices"] = Agendamento.Status.choices
        ctx["edit_url"] = "agendamento_update"
        ctx["delete_url"] = "agendamento_delete"
        return ctx


# ---------------------------------------------------------------------------
# Create / Update / Delete (fábrica para reduzir repetição)
# ---------------------------------------------------------------------------
def _make_views(model, form, label, secao, list_url, create_url, update_url):
    """Cria as classes Create/Update/Delete para uma entidade."""

    class _Create(LoginRequiredMixin, LogMixin, CreateView):
        template_name = "crud/form.html"
        log_entidade = label

        def get_form_class(self):
            return form

        def form_valid(self, response):
            resp = super().form_valid(response)
            self._log(LogAtividade.Acao.CRIOU, self.object)
            messages.success(self.request, f"{label} cadastrado(a) com sucesso.")
            return resp

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            ctx.update(titulo=f"Novo(a) {label}", secao=secao,
                       list_url=list_url, modo="criar")
            return ctx

    _Create.model = model

    class _Update(LoginRequiredMixin, LogMixin, UpdateView):
        template_name = "crud/form.html"
        log_entidade = label

        def get_form_class(self):
            return form

        def form_valid(self, response):
            resp = super().form_valid(response)
            self._log(LogAtividade.Acao.EDITOU, self.object)
            messages.success(self.request, f"{label} atualizado(a) com sucesso.")
            return resp

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            ctx.update(titulo=f"Editar {label}", secao=secao,
                       list_url=list_url, modo="editar")
            return ctx

    _Update.model = model

    class _Delete(LoginRequiredMixin, LogMixin, DeleteView):
        template_name = "crud/confirm_delete.html"
        log_entidade = label
        success_url = reverse_lazy(list_url)

        def form_valid(self, response):
            self._log(LogAtividade.Acao.REMOVEU, self.get_object())
            messages.success(self.request, f"{label} removido(a).")
            return super().form_valid(response)

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            ctx.update(titulo=f"Remover {label}", secao=secao, list_url=list_url)
            return ctx

    _Delete.model = model
    return _Create, _Update, _Delete


ContratanteCreate, ContratanteUpdate, ContratanteDelete = _make_views(
    Contratante, ContratanteForm, "Contratante", "contratantes",
    "contratante_list", "contratante_create", "contratante_update")

PrestadoraCreate, PrestadoraUpdate, PrestadoraDelete = _make_views(
    Prestadora, PrestadoraForm, "Prestadora", "prestadoras",
    "prestadora_list", "prestadora_create", "prestadora_update")

ServicoCreate, ServicoUpdate, ServicoDelete = _make_views(
    Servico, ServicoForm, "Serviço", "servicos",
    "servico_list", "servico_create", "servico_update")

AgendamentoCreate, AgendamentoUpdate, AgendamentoDelete = _make_views(
    Agendamento, AgendamentoForm, "Agendamento", "agendamentos",
    "agendamento_list", "agendamento_create", "agendamento_update")


# ---------------------------------------------------------------------------
# Relatórios / Exportação CSV
# ---------------------------------------------------------------------------
class RelatoriosView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/relatorios.html"
    secao = "relatorios"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["por_status"] = (
            Agendamento.objects.values("status")
            .annotate(n=Count("id")).order_by("-n")
        )
        ctx["status_dict"] = dict(Agendamento.Status.choices)
        ctx["por_prestadora"] = (
            Agendamento.objects.values("prestadora__nome")
            .annotate(n=Count("id"), total=Sum("valor")).order_by("-n")[:10]
        )
        ctx["por_servico"] = (
            Agendamento.objects.values("servico__nome")
            .annotate(n=Count("id"), total=Sum("valor")).order_by("-n")[:10]
        )
        ctx["logs"] = LogAtividade.objects.select_related("usuario")[:15]
        return ctx


def _csv_response(filename):
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    resp.write("\ufeff")  # BOM para acentuação correta no Excel
    return resp


class ExportAgendamentosCSV(LoginRequiredMixin, ListView):
    model = Agendamento

    def get(self, request, *args, **kwargs):
        resp = _csv_response("agendamentos.csv")
        writer = csv.writer(resp, delimiter=";")
        writer.writerow(["Data", "Hora", "Contratante", "Prestadora",
                         "Serviço", "Status", "Valor (R$)"])
        qs = Agendamento.objects.select_related(
            "contratante", "prestadora", "servico").order_by("-data", "-hora")
        for a in qs:
            writer.writerow([
                a.data.strftime("%d/%m/%Y"), a.hora.strftime("%H:%M"),
                a.contratante.nome, a.prestadora.nome, a.servico.nome,
                a.get_status_display(),
                f"{a.valor:.2f}".replace(".", ",") if a.valor is not None else "",
            ])
        return resp


class ExportContratantesCSV(LoginRequiredMixin, ListView):
    model = Contratante

    def get(self, request, *args, **kwargs):
        resp = _csv_response("contratantes.csv")
        writer = csv.writer(resp, delimiter=";")
        writer.writerow(["Nome", "Telefone", "E-mail", "Endereço", "Ativo"])
        for c in Contratante.objects.all():
            writer.writerow([c.nome, c.telefone, c.email, c.endereco,
                             "Sim" if c.ativo else "Não"])
        return resp


class ExportPrestadorasCSV(LoginRequiredMixin, ListView):
    model = Prestadora

    def get(self, request, *args, **kwargs):
        resp = _csv_response("prestadoras.csv")
        writer = csv.writer(resp, delimiter=";")
        writer.writerow(["Nome", "Telefone", "E-mail", "Especialidades", "Ativa"])
        for p in Prestadora.objects.all():
            writer.writerow([p.nome, p.telefone, p.email, p.especialidades,
                             "Sim" if p.ativo else "Não"])
        return resp
