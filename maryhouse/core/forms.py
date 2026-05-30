"""Formulários do Mary House."""
from django import forms

from .models import Agendamento, Contratante, Prestadora, Servico

_TEXT = {"class": "field"}


class ContratanteForm(forms.ModelForm):
    class Meta:
        model = Contratante
        fields = ["nome", "telefone", "email", "endereco", "observacoes", "ativo"]
        widgets = {
            "nome": forms.TextInput(attrs=_TEXT),
            "telefone": forms.TextInput(attrs=_TEXT),
            "email": forms.EmailInput(attrs=_TEXT),
            "endereco": forms.TextInput(attrs=_TEXT),
            "observacoes": forms.Textarea(attrs={**_TEXT, "rows": 3}),
        }


class PrestadoraForm(forms.ModelForm):
    class Meta:
        model = Prestadora
        fields = ["nome", "telefone", "email", "especialidades", "observacoes", "ativo"]
        widgets = {
            "nome": forms.TextInput(attrs=_TEXT),
            "telefone": forms.TextInput(attrs=_TEXT),
            "email": forms.EmailInput(attrs=_TEXT),
            "especialidades": forms.TextInput(attrs=_TEXT),
            "observacoes": forms.Textarea(attrs={**_TEXT, "rows": 3}),
        }


class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = ["nome", "descricao", "preco", "duracao_minutos", "ativo"]
        widgets = {
            "nome": forms.TextInput(attrs=_TEXT),
            "descricao": forms.Textarea(attrs={**_TEXT, "rows": 3}),
            "preco": forms.NumberInput(attrs={**_TEXT, "step": "0.01", "min": "0"}),
            "duracao_minutos": forms.NumberInput(attrs={**_TEXT, "min": "0"}),
        }


class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = [
            "contratante", "prestadora", "servico",
            "data", "hora", "status", "valor", "observacoes",
        ]
        widgets = {
            "contratante": forms.Select(attrs=_TEXT),
            "prestadora": forms.Select(attrs=_TEXT),
            "servico": forms.Select(attrs=_TEXT),
            "data": forms.DateInput(attrs={**_TEXT, "type": "date"}),
            "hora": forms.TimeInput(attrs={**_TEXT, "type": "time"}),
            "status": forms.Select(attrs=_TEXT),
            "valor": forms.NumberInput(attrs={**_TEXT, "step": "0.01", "min": "0"}),
            "observacoes": forms.Textarea(attrs={**_TEXT, "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Só mostra cadastros ativos nos selects.
        self.fields["contratante"].queryset = Contratante.objects.filter(ativo=True)
        self.fields["prestadora"].queryset = Prestadora.objects.filter(ativo=True)
        self.fields["servico"].queryset = Servico.objects.filter(ativo=True)
