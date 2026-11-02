"""Teste de fumaça: o sistema sobe, protege as telas e mostra os dados de demonstração.

Rodar de dentro de maryhouse/:
    python manage.py test
"""
import io

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Agendamento, Contratante, LogAtividade

TELAS = [
    "dashboard", "contratante_list", "prestadora_list", "servico_list",
    "agendamento_list", "relatorios",
    "contratante_create", "prestadora_create", "servico_create", "agendamento_create",
]

EXPORTACOES = ["contratante_export", "prestadora_export", "agendamento_export"]


class SemLoginTest(TestCase):
    def test_login_abre(self):
        r = self.client.get(reverse("login"))
        self.assertEqual(r.status_code, 200)

    def test_toda_tela_exige_login(self):
        for nome in TELAS + EXPORTACOES:
            with self.subTest(tela=nome):
                r = self.client.get(reverse(nome))
                self.assertEqual(r.status_code, 302)
                self.assertTrue(r["Location"].startswith(reverse("login")))


class ComDemonstracaoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=io.StringIO())

    def setUp(self):
        self.assertTrue(self.client.login(username="admin", password="admin123"))

    def test_demonstracao_tem_dados(self):
        self.assertGreater(Agendamento.objects.count(), 0)
        self.assertGreater(Contratante.objects.count(), 0)

    def test_toda_tela_abre(self):
        for nome in TELAS:
            with self.subTest(tela=nome):
                self.assertEqual(self.client.get(reverse(nome)).status_code, 200)

    def test_exportacoes_saem_em_csv(self):
        for nome in EXPORTACOES:
            with self.subTest(exportacao=nome):
                r = self.client.get(reverse(nome))
                self.assertEqual(r.status_code, 200)
                self.assertIn("text/csv", r["Content-Type"])

    def test_remover_contratante_deixa_rastro(self):
        c = Contratante.objects.create(nome="Contratante de teste", telefone="0000")
        antes = LogAtividade.objects.count()
        r = self.client.post(reverse("contratante_delete", args=[c.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Contratante.objects.filter(pk=c.pk).exists())
        self.assertEqual(LogAtividade.objects.count(), antes + 1)
