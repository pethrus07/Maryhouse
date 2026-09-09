"""Popula o banco com dados de demonstração e cria um usuário admin.

Existe para mostrar o sistema cheio: painel com gráfico, relatório com número, lista
com paginação. Sem dado, todas as telas ficam vazias e não dá para avaliar nada.

NUNCA rodar em produção: cria o superusuário admin com senha fraca escrita aqui
mesmo. É idempotente por segurança — se já existe agendamento, sai sem tocar em nada.

Uso:
    python manage.py seed_demo
"""
import random
from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Agendamento, Contratante, Prestadora, Servico


class Command(BaseCommand):
    help = "Cria usuário admin e dados de demonstração."

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                "admin", "admin@maryhouse.local", "admin123",
                first_name="Maria", last_name="Souza",
            )
            self.stdout.write(self.style.SUCCESS("Usuário 'admin' criado (senha: admin123)."))
        else:
            self.stdout.write("Usuário 'admin' já existe.")

        # A trava: um único agendamento já existente aborta tudo. É o que impede o comando
        # de duplicar a demonstração a cada execução — e de despejar dado falso por cima de
        # dado real, se alguém rodá-lo por engano num banco em uso.
        if Agendamento.objects.exists():
            self.stdout.write("Dados de demonstração já existem — nada a fazer.")
            return

        servicos_data = [
            ("Faxina completa", 180.00, 240),
            ("Faxina simples", 120.00, 120),
            ("Passadoria", 90.00, 120),
            ("Cozinha / preparo de refeições", 150.00, 180),
            ("Organização de ambientes", 200.00, 240),
            ("Limpeza pós-obra", 350.00, 360),
        ]
        servicos = [Servico.objects.create(nome=n, preco=p, duracao_minutos=d,
                                           descricao=f"Serviço de {n.lower()}.")
                    for n, p, d in servicos_data]

        contratantes_nomes = [
            "Ana Beatriz Lima", "Carlos Eduardo Ramos", "Fernanda Oliveira",
            "Gustavo Henrique Dias", "Juliana Castro", "Marcos Vinícius Alves",
            "Patrícia Gomes", "Roberto Carvalho", "Tânia Mendes", "Vítor Hugo Pires",
        ]
        contratantes = []
        for i, nome in enumerate(contratantes_nomes):
            contratantes.append(Contratante.objects.create(
                nome=nome,
                telefone=f"(83) 9{random.randint(8000,9999)}-{random.randint(1000,9999)}",
                email=f"{nome.split()[0].lower()}@email.com",
                endereco=f"Rua das Flores, {100 + i*7} — João Pessoa/PB",
            ))

        prestadoras_data = [
            ("Maria das Graças", "Faxina, passadoria"),
            ("Joana Silva", "Cozinha, organização"),
            ("Rita de Cássia", "Faxina pós-obra"),
            ("Sandra Pereira", "Faxina, cozinha"),
            ("Lúcia Fernandes", "Passadoria, organização"),
        ]
        prestadoras = [Prestadora.objects.create(
            nome=n, especialidades=e,
            telefone=f"(83) 9{random.randint(8000,9999)}-{random.randint(1000,9999)}",
            email=f"{n.split()[0].lower()}@email.com",
        ) for n, e in prestadoras_data]

        status_pesos = [
            (Agendamento.Status.CONCLUIDO, 5),
            (Agendamento.Status.CONFIRMADO, 3),
            (Agendamento.Status.PENDENTE, 3),
            (Agendamento.Status.CANCELADO, 1),
        ]
        status_pool = [s for s, w in status_pesos for _ in range(w)]
        horas = [time(8, 0), time(9, 30), time(11, 0), time(13, 30), time(15, 0), time(16, 30)]

        hoje = timezone.localdate()
        total = 0
        # O passado precisa ser irregular para o gráfico de 6 meses ter alguma forma: dia
        # sorteado fora (45%) e 1 ou 2 agendamentos nos que ficam. O total, portanto, muda
        # a cada execução — fica na casa dos 140.
        for delta in range(-150, 15):  # ~5 meses para trás + próximos dias
            if random.random() < 0.45:
                continue
            for _ in range(random.randint(1, 2)):
                serv = random.choice(servicos)
                Agendamento.objects.create(
                    contratante=random.choice(contratantes),
                    prestadora=random.choice(prestadoras),
                    servico=serv,
                    data=hoje + timedelta(days=delta),
                    hora=random.choice(horas),
                    status=(Agendamento.Status.PENDENTE if delta > 0
                            else random.choice(status_pool)),
                    valor=serv.preco,
                )
                total += 1

        self.stdout.write(self.style.SUCCESS(
            f"Demonstração criada: {len(servicos)} serviços, "
            f"{len(contratantes)} contratantes, {len(prestadoras)} prestadoras, "
            f"{total} agendamentos."
        ))
