# Mary House — Sistema de Gerenciamento

Reescrita em **Python / Django** do sistema Mary House: gestão de cadastros e
agendamentos de contratantes e prestadoras de serviço doméstico.

Interface limpa (branco + rosa), painel com indicadores, CRUD completo,
busca, filtros, relatórios e exportação CSV. Acesso restrito à equipe interna.

---

## Stack

- **Python 3.10+** e **Django 5.1**
- **PostgreSQL** (com fallback automático para SQLite em desenvolvimento)
- HTML + CSS próprios (sem framework de frontend); gráficos com Chart.js (embutido, sem CDN)

---

## Como rodar

### 1. Criar ambiente virtual e instalar dependências

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env`. Para usar **PostgreSQL**, preencha `DATABASE_URL`:

```
DATABASE_URL=postgres://usuario:senha@localhost:5432/maryhouse
```

> Se deixar `DATABASE_URL` em branco, o sistema usa **SQLite** automaticamente
> (arquivo `db.sqlite3`), sem precisar configurar nada — ótimo para testar na hora.

As variáveis do `.env` precisam estar disponíveis no ambiente. Você pode exportá-las
manualmente, usar um `.env` com `python-dotenv`, ou definir no seu provedor de deploy.
Para um teste rápido em SQLite, basta não definir `DATABASE_URL`.

### 3. Banco de dados e usuário

```bash
python manage.py migrate
python manage.py seed_demo        # cria admin + dados de exemplo
```

O comando `seed_demo` cria:
- usuário **admin** / senha **admin123**
- serviços, contratantes, prestadoras e ~140 agendamentos de exemplo

> Em produção, **não** rode `seed_demo`. Crie o usuário real com:
> ```bash
> python manage.py createsuperuser
> ```

### 4. Subir o servidor

```bash
python manage.py runserver
```

Acesse **http://127.0.0.1:8000/** e entre com `admin` / `admin123`.

---

## Funcionalidades

- **Dashboard** — total de agendamentos, contratantes/prestadoras ativas,
  faturamento do mês, gráfico de agendamentos por mês e por status, agenda do
  dia e próximos agendamentos.
- **Agendamentos** — CRUD, filtro por status, busca, exportação CSV. O valor é
  herdado automaticamente do serviço quando deixado em branco.
- **Serviços** — CRUD (nome, preço, duração, situação).
- **Contratantes** e **Prestadoras** — CRUD com busca e exportação CSV.
- **Relatórios** — agregações por prestadora e por serviço + histórico de atividade.
- **Histórico/logs** — toda criação, edição e remoção fica registrada com o usuário.
- **Autenticação** — acesso somente para a equipe interna (login obrigatório).
- **Django Admin** — disponível em `/admin/` para gestão de usuários e dados.

---

## Estrutura do projeto

```
maryhouse/
├── manage.py
├── requirements.txt
├── .env.example
├── config/                 # configurações do projeto
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── core/                   # aplicação principal
    ├── models.py           # Contratante, Prestadora, Servico, Agendamento, LogAtividade
    ├── forms.py
    ├── views.py            # dashboard, CRUD, relatórios, exportação CSV
    ├── urls.py
    ├── admin.py
    ├── templatetags/
    ├── management/commands/seed_demo.py
    ├── static/core/        # CSS e Chart.js
    └── templates/          # base, login, dashboard, crud, relatórios
```

---

## Notas para produção

- Defina `DEBUG=False`, um `SECRET_KEY` novo e `ALLOWED_HOSTS` no `.env`.
- Rode `python manage.py collectstatic` e sirva os estáticos pelo servidor web.
- Use um servidor WSGI (Gunicorn/uWSGI) atrás de Nginx, e o PostgreSQL via `DATABASE_URL`.

## Possíveis evoluções (deixadas fora do escopo atual)

- API REST (Django REST Framework) para um app mobile.
- Notificações automáticas (e-mail / WhatsApp).
- Perfis de acesso por função.
