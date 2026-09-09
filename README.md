# Mary House — Sistema de Gerenciamento

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.1-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-com%20fallback%20SQLite-4169E1?logo=postgresql&logoColor=white)
![Sem dependência de frontend](https://img.shields.io/badge/frontend-HTML%20%2B%20CSS%20pr%C3%B3prios-e25a7d)
![Status](https://img.shields.io/badge/status-em%20uso-2e9e6b)

> Sistema interno de uma agência de serviços domésticos em João Pessoa. Registra contratantes,
> prestadoras e o catálogo de serviços, e amarra os três num agendamento com data, hora, status e
> valor. Painel, relatórios, exportação CSV e histórico de quem mexeu no quê — tudo atrás de login.

> **Para entender o código sozinho, comece por [docs/ARQUITETURA.md](docs/ARQUITETURA.md).**

---

## 1. Visão Geral e a Dor

A operação de uma agência de faxina se resolve, na prática, em quatro perguntas: *quem pediu*,
*quem vai*, *que dia* e *quanto custa*. Quando isso vive em caderno e conversa de WhatsApp, a
resposta muda conforme quem responde — e o histórico não existe.

O sistema é a resposta única para essas quatro perguntas. Ele não tenta ser um ERP: não emite
nota, não controla caixa, não fala com o cliente final. Faz o cadastro, a agenda e a memória do
que aconteceu, e mostra num painel o que a dona precisa olhar antes de abrir o dia.

Quem usa é só a equipe interna. **Não há área do cliente, cadastro público nem API** — toda tela
exige login.

---

## 2. Arquitetura e Decisões Técnicas

| Camada | Escolha | Por quê | Alternativa | Impacto |
|---|---|---|---|---|
| Aplicação | Django 5.1, um único app (`core`) | O sistema é CRUD com relatório: as classes genéricas do Django cobrem 90% dele sem código | Flask/FastAPI + SQLAlchemy | O admin, a autenticação, as migrações e a paginação vêm de graça |
| Banco | `DATABASE_URL` → PostgreSQL; sem ela, SQLite | Testar não pode exigir subir servidor de banco | Só Postgres, sempre | `git clone` + `migrate` + `runserver` roda em qualquer máquina |
| Frontend | HTML renderizado no servidor, CSS próprio em tokens | Sem build, sem `node_modules`, sem versão de framework para envelhecer | React/Vue + API | Manutenção é editar um `.html` e um `.css`; nada compila |
| Gráficos | Chart.js **dentro do repositório** | Painel que depende de CDN quebra quando a CDN quebra | `<script src="cdn...">` | Um arquivo de vendor no git em troca de uma dependência a menos no ar |
| CRUD | Fábrica `_make_views()` gera Create/Update/Delete | Doze classes quase idênticas viram uma função e quatro chamadas | Escrever as doze | `views.py` cabe numa tela de rolagem; entidade nova custa uma linha |
| Auditoria | Tabela `LogAtividade` escrita por um mixin nas views | "Quem apagou isso?" precisava ter resposta | Django `LogEntry` (só cobre o `/admin/`) | Histórico do que a equipe faz **pelo site**, visível na tela de relatórios |
| Integridade | FKs de agendamento com `on_delete=PROTECT` | Apagar um contratante não pode levar junto o histórico dele | `CASCADE` | O banco recusa a remoção; o campo `ativo` é o caminho para "sumir da tela sem perder o passado" |

---

## 3. Destaque de Engenharia — a tela que serve três entidades

Contratantes, prestadoras e serviços usam **o mesmo template de lista e o mesmo de formulário**. A
view diz o que a tabela mostra, não como:

```python
colunas = [("Nome", "nome"), ("Preço", "_preco"),
           ("Duração", "_duracao"), ("Situação", "_situacao")]
```

O template percorre `colunas` e pede a cada célula à tag `coluna_valor`, que resolve o atributo
comum e trata os três casos que precisam de formatação (`_preco`, `_duracao`, `_situacao`).
`coluna_classe` faz o mesmo para a classe CSS, e é assim que "Ativo" vira um badge verde sem uma
linha de `if` no HTML.

O limite dessa abordagem também é explícito: agendamentos **têm** template próprio, porque
precisam de colunas vindas de tabelas ligadas, badge por status e um filtro. Foi mais barato
duplicar o template do que transformar a tag genérica num interpretador de expressões. O motivo
está registrado em [docs/ARQUITETURA.md](docs/ARQUITETURA.md), seção 6.

---

## 4. Como rodar

De dentro de `maryhouse/`:

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Sem `.env`, o sistema sobe em SQLite e em modo de desenvolvimento. Para PostgreSQL, copie
`.env.example` para `.env` e preencha `DATABASE_URL`. Os detalhes de variáveis, do comando de
demonstração e das notas de produção estão em [maryhouse/README.md](maryhouse/README.md).

> **Deploy não está configurado neste repositório**: não há Docker, CI nem servidor WSGI nas
> dependências. O caminho pretendido está descrito em
> [docs/ARQUITETURA.md](docs/ARQUITETURA.md), seção 8.

---

## Estrutura do Projeto

```
Maryhouse/
├── docs/ARQUITETURA.md      o manual: fluxo, modelos, telas, receitas, armadilhas
└── maryhouse/               o projeto Django
    ├── config/              settings, urls raiz, wsgi
    └── core/                o app: models, forms, views, urls, admin,
                             templatetags, seed_demo, migrations,
                             static/ (CSS + Chart.js) e templates/
```

---

## Licença

Software feito sob encomenda para a Mary House. **Não há arquivo de licença neste repositório** —
o código está público como portfólio; o uso é do cliente.
