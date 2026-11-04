"""Teste de fumaça: o sistema sobe, protege as telas e mostra os dados de demonstração.

Rodar de dentro de maryhouse/:
    cp .env.example .env   (uma vez; liga DEBUG para desenvolvimento)
    python manage.py test
"""
import io
import os
import subprocess
import sys
from pathlib import Path

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .models import Agendamento, Contratante, LogAtividade

RAIZ = Path(__file__).resolve().parent.parent

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


class RemoverComAgendamentoTest(TestCase):
    """PROTECT nas chaves do agendamento: remover quem tem agendamento não pode dar 500."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=io.StringIO())

    def test_recusa_com_mensagem_e_sem_log(self):
        self.assertTrue(self.client.login(username="admin", password="admin123"))
        c = Contratante.objects.filter(agendamentos__isnull=False).first()
        antes = LogAtividade.objects.count()
        r = self.client.post(reverse("contratante_delete", args=[c.pk]), follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(Contratante.objects.filter(pk=c.pk).exists())
        self.assertEqual(LogAtividade.objects.count(), antes)
        self.assertContains(r, "não pode ser removido")


class DefaultsSegurosTest(SimpleTestCase):
    """Sobe o settings num processo à parte, com o ambiente controlado."""

    def _subir(self, **amb):
        env = {k: v for k, v in os.environ.items()
               if k not in ("DEBUG", "SECRET_KEY", "ALLOWED_HOSTS")}
        env.update({"DEBUG": "", "SECRET_KEY": "", "ALLOWED_HOSTS": ""}, **amb)
        env["DJANGO_SETTINGS_MODULE"] = "config.settings"
        codigo = ("import django; django.setup(); from django.conf import settings as s; "
                  "print(s.DEBUG, s.ALLOWED_HOSTS, s.SESSION_COOKIE_SECURE)")
        return subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, env=env,
                              capture_output=True, text=True)

    def test_sem_chave_e_sem_debug_nao_sobe(self):
        r = self._subir()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("SECRET_KEY", r.stderr)

    def test_com_chave_sobe_seguro(self):
        r = self._subir(SECRET_KEY="x" * 50)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "False ['localhost', '127.0.0.1'] True")

    def test_debug_aceita_chave_de_desenvolvimento(self):
        r = self._subir(DEBUG="True")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith("True"))
