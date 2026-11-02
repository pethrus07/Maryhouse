Português | [English](README.md)

# Sistema de agendamentos para uma agência de faxina

> **Arquivado (2026-11).** A conversa comercial terminou em setembro de 2026. Não há deploy configurado neste repositório.

Sistema interno de uma pequena agência de serviços domésticos em João Pessoa. Registra contratantes, prestadoras e o catálogo de serviços, e amarra os três num agendamento com data, hora, status e valor. Painel, relatórios, exportação CSV e histórico de atividade, tudo atrás de login.

## O que foi

A operação da agência se resume a quatro perguntas: quem pediu, quem vai, que dia, quanto custa. Quando isso vive em caderno e conversa de WhatsApp, a resposta muda conforme quem responde e o histórico não existe. O sistema responde as quatro num lugar só. Não é ERP: não emite nota, não controla caixa, não tem área do cliente nem API pública. Só a equipe interna usa.

Foi reescrito em Django em 2026. Uma proposta seguinte (site novo e o sistema migrado para Cloudflare Workers) não foi adiante.

## Stack

- Python 3.10+ e Django 5.1, um app só (`core`).
- PostgreSQL por `DATABASE_URL`; sem ela, um SQLite local.
- HTML renderizado no servidor e CSS próprio, sem framework de frontend. Chart.js dentro do repositório (sem CDN).

## Rodar localmente

De dentro de `maryhouse/`:

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # DEBUG=True para desenvolvimento
python manage.py migrate
python manage.py seed_demo        # usuário de demonstração admin / admin123 e dados fictícios
python manage.py runserver        # http://127.0.0.1:8000
```

Sem `.env`, o sistema assume produção: DEBUG desligado, só localhost, e não sobe sem `SECRET_KEY`. O `.env.example` liga o modo de desenvolvimento com SQLite. O `seed_demo` cria uma senha fraca de demonstração e nunca deve rodar em produção. As variáveis de ambiente estão em `maryhouse/.env.example`.

## Testes

```bash
cd maryhouse
python manage.py test
```

O `core/tests.py` é um teste de fumaça: a tela de login abre, toda tela e exportação manda para o login quando não há sessão, e com os dados de demonstração toda tela abre, as exportações saem em CSV e remover um contratante grava no histórico. Confere também que remover contratante com agendamento mostra mensagem em vez de erro 500, e sobe o `settings.py` num processo à parte para conferir os defaults seguros.

## Estrutura de pastas

```
maryhouse/README.md     guia de instalação e notas de produção
docs/ARQUITETURA.md     manual completo: fluxo, modelos, telas, receitas, armadilhas
docs/arquitetura/       diagramas (UML, BPMN, C4)
maryhouse/              o projeto Django
  config/               settings, urls raiz, wsgi
  core/                 models, forms, views, urls, admin, templatetags,
                        seed_demo, migrations, static/ (CSS + Chart.js), templates/, tests.py
```

## O que ficou de aprendizado

- **Um template de lista para três entidades.** Contratantes, prestadoras e serviços usam o mesmo template de lista e de formulário; a view declara as colunas e uma template tag formata. Agendamentos ganharam template próprio, porque forçar o genérico viraria um interpretador de expressões dentro de uma tag.
- **Uma fábrica de views em vez de doze classes.** `_make_views()` gera criar, editar e remover para cada entidade, e o `views.py` ficou em torno de 400 linhas.
- **Auditoria na view, não em signal.** O request é o único lugar que sabe quem fez pela tela. O preço: edição pelo `/admin/` não entra no histórico.
- **`PROTECT` nas chaves do agendamento.** Apagar um contratante não pode levar o histórico junto. O campo `ativo` esconde o registro sem perder o passado.
- **Default de desenvolvimento é risco.** O `settings.py` caía numa chave embutida, `DEBUG=True` e `ALLOWED_HOSTS=*` quando não havia `.env`. Desde 2026-11 os defaults são seguros e a chave embutida só vale com `DEBUG=True`.

## Licença

Todos os direitos reservados. Código feito para um cliente; publicado como portfólio.
