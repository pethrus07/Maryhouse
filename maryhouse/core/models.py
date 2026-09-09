"""Os cinco modelos do Mary House — a forma do negócio dentro do banco.

Três cadastros (Contratante, Prestadora, Servico), o evento que amarra os três
(Agendamento) e o histórico do que a equipe fez (LogAtividade).
A regra que sustenta o resto: agendamento aponta para os três com PROTECT, então
cadastro com histórico não pode ser apagado — some da tela pelo campo `ativo`.
"""
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Base(models.Model):
    """Campos comuns de auditoria.

    Abstrato: não vira tabela. Existe para que os quatro cadastros tenham "desde quando"
    e "mexido pela última vez" sem repetir os dois campos quatro vezes. A LogAtividade
    não herda daqui — ela já nasce com data_hora e nunca é editada.
    """

    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        abstract = True


class Contratante(Base):
    """Cliente que contrata o serviço."""

    nome = models.CharField("Nome", max_length=120)
    telefone = models.CharField("Telefone", max_length=20, blank=True)
    email = models.EmailField("E-mail", blank=True)
    endereco = models.CharField("Endereço", max_length=200, blank=True)
    observacoes = models.TextField("Observações", blank=True)
    ativo = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Contratante"
        verbose_name_plural = "Contratantes"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse("contratante_list")


class Prestadora(Base):
    """Prestadora de serviço doméstico (empregada)."""

    nome = models.CharField("Nome", max_length=120)
    telefone = models.CharField("Telefone", max_length=20, blank=True)
    email = models.EmailField("E-mail", blank=True)
    especialidades = models.CharField(
        "Especialidades", max_length=200, blank=True,
        help_text="Ex.: faxina, passadoria, cozinha…",
    )
    observacoes = models.TextField("Observações", blank=True)
    ativo = models.BooleanField("Ativa", default=True)

    class Meta:
        verbose_name = "Prestadora"
        verbose_name_plural = "Prestadoras"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse("prestadora_list")


class Servico(Base):
    """Tipo de serviço oferecido."""

    nome = models.CharField("Nome", max_length=120)
    descricao = models.TextField("Descrição", blank=True)
    preco = models.DecimalField("Preço (R$)", max_digits=10, decimal_places=2, default=0)
    duracao_minutos = models.PositiveIntegerField("Duração (minutos)", default=60)
    ativo = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse("servico_list")


class Agendamento(Base):
    """Agendamento de um serviço entre contratante e prestadora."""

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        CONFIRMADO = "confirmado", "Confirmado"
        CONCLUIDO = "concluido", "Concluído"
        CANCELADO = "cancelado", "Cancelado"

    # PROTECT nas três chaves, e não CASCADE: apagar um contratante não pode levar junto
    # o registro de tudo o que ele já contratou. O banco recusa a remoção; o caminho para
    # "sumir da tela" é desmarcar o campo `ativo` do cadastro.
    # Efeito colateral conhecido: a tela de remover devolve erro 500 nesse caso, porque a
    # view não trata ProtectedError (ver docs/ARQUITETURA.md, seção 13).
    contratante = models.ForeignKey(
        Contratante, on_delete=models.PROTECT,
        related_name="agendamentos", verbose_name="Contratante",
    )
    prestadora = models.ForeignKey(
        Prestadora, on_delete=models.PROTECT,
        related_name="agendamentos", verbose_name="Prestadora",
    )
    servico = models.ForeignKey(
        Servico, on_delete=models.PROTECT,
        related_name="agendamentos", verbose_name="Serviço",
    )
    data = models.DateField("Data")
    hora = models.TimeField("Hora")
    status = models.CharField(
        "Status", max_length=12,
        choices=Status.choices, default=Status.PENDENTE,
    )
    valor = models.DecimalField(
        "Valor (R$)", max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Em branco usa o preço do serviço.",
    )
    observacoes = models.TextField("Observações", blank=True)

    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ["-data", "-hora"]

    def __str__(self):
        return f"{self.servico} — {self.contratante} ({self.data:%d/%m/%Y})"

    def get_absolute_url(self):
        return reverse("agendamento_list")

    def save(self, *args, **kwargs):
        # O valor é do agendamento, não do serviço: uma vez gravado, ele congela, para que
        # mudar o preço da tabela não reescreva o histórico. Este copiar-na-gravação é só a
        # conveniência de deixar o campo em branco e herdar o preço de hoje.
        # Cuidado: editar um agendamento antigo apagando o campo traz o preço ATUAL.
        if self.valor in (None, "") and self.servico_id:
            self.valor = self.servico.preco
        super().save(*args, **kwargs)

    # Mora no modelo, e não no template, porque a linguagem de template não faz mapa:
    # sem isto, cada tela que mostra status precisaria de uma escada de {% if %}.
    @property
    def status_cor(self):
        return {
            self.Status.PENDENTE: "warning",
            self.Status.CONFIRMADO: "info",
            self.Status.CONCLUIDO: "success",
            self.Status.CANCELADO: "muted",
        }.get(self.status, "muted")


class LogAtividade(models.Model):
    """Registro de atividades (histórico/auditoria)."""

    class Acao(models.TextChoices):
        CRIOU = "criou", "Criou"
        EDITOU = "editou", "Editou"
        REMOVEU = "removeu", "Removeu"

    # SET_NULL: demitir alguém não pode apagar o rastro do que essa pessoa fez. A linha
    # fica no histórico e a tela mostra "Sistema" no lugar do nome.
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="Usuário",
    )
    acao = models.CharField("Ação", max_length=10, choices=Acao.choices)
    entidade = models.CharField("Entidade", max_length=50)
    descricao = models.CharField("Descrição", max_length=255)
    data_hora = models.DateTimeField("Data/hora", default=timezone.now)

    class Meta:
        verbose_name = "Log de atividade"
        verbose_name_plural = "Logs de atividade"
        ordering = ["-data_hora"]

    def __str__(self):
        return f"{self.get_acao_display()} {self.entidade} — {self.descricao}"
