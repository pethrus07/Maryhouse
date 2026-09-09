# Mary House — Arquitetura e funcionamento

> Escrito em 09/09/2026 para uma pessoa entender o sistema **sozinha**, sem quem o construiu por
> perto. Cobre da estrutura de pastas ao que acontece em cada requisição e em cada comando. Onde o
> código tem uma decisão que não é óbvia, o motivo está no cabeçalho do próprio arquivo; aqui fica
> o mapa que liga tudo.
>
> O que este documento **não** é: o passo a passo de instalação (isso é
> [../maryhouse/README.md](../maryhouse/README.md)) nem a lista de desejos do cliente.
> Tudo o que está aqui foi medido no código de hoje. O que não existe está dito que não existe.

---

## 0 · Como ler

Se você tem dez minutos, leia as seções 1, 2 e 12. Se vai mexer numa tela, leia 3 a 6. Se vai
mexer no banco, 5. Se vai colocar no ar, 8 e a receita certa em 10. A seção 11 é o vocabulário; a
13 é o que quebra se você esquecer.

---

## 1 · O sistema em um parágrafo

Um **projeto Django único**, sem API, sem JavaScript de aplicação e sem framework de frontend: o
servidor renderiza HTML e o navegador só recebe página pronta. Ele existe para a Mary House, uma
agência de serviços domésticos em João Pessoa, saber **quem contratou, quem vai executar, qual
serviço, em que dia e por quanto**. São cinco tabelas (`Contratante`, `Prestadora`, `Servico`,
`Agendamento` e `LogAtividade`), um CRUD por tabela, um painel com quatro números e dois gráficos,
uma página de relatórios e três exportações CSV. **Não há cadastro público nem área do cliente**:
tudo atrás de login, para a equipe interna. O banco é PostgreSQL quando existe `DATABASE_URL`, e
SQLite quando não existe — o mesmo código roda nos dois sem mudar uma linha.

```mermaid
flowchart LR
  U[Equipe interna] -->|login| L[LoginView do Django]
  L --> D[DashboardView]
  subgraph app["core · o único app"]
    D --> M[(Modelos)]
    C[ListView / Create / Update / Delete] --> M
    C --> LOG[LogAtividade]
    R[RelatoriosView] --> M
    X[Export*CSV] --> M
  end
  M --> DB[(PostgreSQL ou SQLite)]
  LOG --> DB
  A[/admin/ Django] --> DB
```

O único caminho que **não** passa pelas views do `core` é o `/admin/`: o Django admin escreve
direto nos modelos e, por isso, **não gera `LogAtividade`** (seção 13).

---

## 2 · Mapa do repositório

```
Maryhouse/                       raiz do repositório (público no GitHub)
├── README.md                    a vitrine
├── docs/ARQUITETURA.md          este arquivo
├── .gitignore                   mantém maryhouse-proposta/ fora do repo público
├── maryhouse-proposta/          FORA DO GIT — material comercial do cliente
└── maryhouse/                   o projeto Django (é daqui que se roda tudo)
    ├── manage.py                utilitário padrão do Django
    ├── requirements.txt         4 dependências: Django, dj-database-url, psycopg2, python-dotenv
    ├── .env.example             o modelo do .env (o .env real é ignorado pelo git)
    ├── .gitignore               __pycache__, .env, db.sqlite3, staticfiles/, venvs, *.log
    ├── config/                  o projeto: settings, urls raiz, wsgi
    └── core/                    O APP — todo o sistema mora aqui
        ├── models.py            as 5 tabelas
        ├── forms.py             4 ModelForms (um por entidade editável)
        ├── views.py             painel, CRUD, relatórios, exportação
        ├── urls.py              as 23 rotas do sistema
        ├── admin.py             os 5 modelos no /admin/
        ├── apps.py              a AppConfig
        ├── templatetags/core_extras.py   as 3 tags que os templates genéricos usam
        ├── management/commands/seed_demo.py   dados de demonstração + usuário admin
        ├── migrations/0001_initial.py   a única migração; cria as 5 tabelas
        ├── static/core/css/styles.css   o tema inteiro (branco + rosa), num arquivo só
        ├── static/core/js/chart.umd.min.js   Chart.js embutido (não é código nosso)
        └── templates/
            ├── base.html                 o esqueleto: barra lateral, topo, mensagens
            ├── registration/login.html   a única tela sem login (não estende base.html)
            ├── crud/list.html            a lista genérica (contratantes, prestadoras, serviços)
            ├── crud/list_agendamentos.html   a lista de agendamentos (tem filtro e badge)
            ├── crud/form.html            o formulário genérico (criar e editar)
            ├── crud/confirm_delete.html  a confirmação de remoção
            ├── dashboard/dashboard.html  o painel + os dois gráficos
            └── dashboard/relatorios.html as agregações e o histórico
```

Duas pastas ficam fora do git e você não vai encontrá-las numa cópia limpa: `maryhouse-proposta/`
(material comercial) e `staticfiles/` (saída do `collectstatic`).

---

## 3 · O ciclo de vida de uma requisição

1. **`config/urls.py` decide quem responde.** Só duas entradas: `/admin/` vai para o Django admin,
   e **todo o resto** vai para `core/urls.py`.
2. **`core/urls.py` casa a rota.** São caminhos fixos (`/contratantes/`, `/agendamentos/novo/`,
   `/relatorios/`…) e caminhos com `<int:pk>`; não há curinga, então a ordem não importa aqui.
3. **`LoginRequiredMixin` barra quem não entrou.** Toda view do sistema o usa. Sem sessão, o
   Django manda para `LOGIN_URL = "login"` com `?next=` — é o que faz o sistema ser só da equipe
   interna. A exceção é a própria tela de login.
4. **A view monta o contexto.** As listas aplicam busca (`?q=`) e, em agendamentos, o filtro de
   status (`?status=`); pagina de 12 em 12. As de escrita validam o `ModelForm`, salvam, gravam
   uma linha em `LogAtividade` e põem uma mensagem de sucesso.
5. **O template renderiza.** Toda tela de dentro estende `base.html`, que desenha a barra lateral,
   o topo com título e ação, e as mensagens. A variável `secao` (`"agendamentos"`,
   `"contratantes"`…) é o que acende o item certo do menu — quem esquece de defini-la fica com o
   menu apagado (seção 13).
6. **A resposta sai como HTML.** Não há cache configurado, não há sessão em Redis, não há fila.
   O CSS é servido pelo `staticfiles` do Django em desenvolvimento e pelo servidor web em
   produção; o Chart.js vem do próprio projeto, não de CDN. **As fontes (Fraunces e Plus Jakarta
   Sans), essas sim, vêm do Google Fonts** — sem internet o navegador cai nas fontes de sistema.

O **CSV** é a única resposta que não é HTML: `_csv_response()` abre um `HttpResponse` de
`text/csv`, escreve um BOM UTF-8 (`\ufeff`) e usa `;` como separador. Os dois detalhes existem pelo
mesmo motivo — é o que faz o Excel em português abrir o arquivo com acento certo e coluna
separada.

---

## 4 · Os módulos

| Arquivo | Responsabilidade | O que não faz |
|---|---|---|
| `config/settings.py` | Toda a configuração: banco (`DATABASE_URL` ou SQLite), segurança, apps, fuso `America/Sao_Paulo`, rotas de login/logout, mapa de mensagens → classe CSS | Não valida se o `.env` faz sentido: um `DEBUG` esquecido em `True` sobe assim mesmo |
| `config/urls.py` | Só divide o mundo em `/admin/` e o resto | Não tem rota própria |
| `config/wsgi.py` | O ponto de entrada para Gunicorn/uWSGI | — |
| `core/models.py` | As cinco tabelas, o `Base` abstrato com `criado_em`/`atualizado_em`, o `save()` que herda o preço do serviço e a propriedade `status_cor` | Não valida agenda: nada impede duas prestadoras no mesmo horário, nem data no passado |
| `core/forms.py` | Quatro `ModelForm` que só existem para (a) escolher os campos e (b) pendurar `class="field"` e `type="date"`/`type="time"` nos widgets. O `AgendamentoForm` filtra os selects para **só cadastros ativos** | Não valida regra de negócio; a validação é a do modelo |
| `core/views.py` | Painel, as quatro listas, a fábrica `_make_views()` que gera Create/Update/Delete, relatórios e os três CSV | Não tem controle por papel: quem entra pode tudo (seção 7) |
| `core/urls.py` | As 23 rotas, incluindo login e logout do Django | — |
| `core/admin.py` | Os cinco modelos no `/admin/`, com filtro, busca e `date_hierarchy` em agendamentos | Não bloqueia edição: o admin escreve sem passar pelo `LogAtividade` |
| `core/templatetags/core_extras.py` | `coluna_valor` e `coluna_classe` (o que a lista genérica imprime em cada célula) e `querystring` (paginar sem perder busca e filtro) | — |
| `core/management/commands/seed_demo.py` | Cria o usuário `admin` e um conjunto aleatório de dados de demonstração | Não apaga nada: se já houver agendamento, sai sem fazer nada |
| `core/static/core/css/styles.css` | O tema inteiro em tokens `--rose`, `--ink`, `--surface`…, o shell de duas colunas e o responsivo | — |

### A fábrica de views (`_make_views`)

O trecho menos óbvio do `views.py`. Em vez de escrever doze classes quase iguais (criar, editar e
remover × quatro entidades), a função devolve as três classes já com o modelo, o formulário, o
rótulo, a seção do menu e a URL de volta amarrados. É por isso que `views.py` cabe numa leitura só, em vez de
passar de mil linhas, e é por isso que uma entidade nova custa uma linha:

```python
XCreate, XUpdate, XDelete = _make_views(
    Modelo, ModeloForm, "Rótulo", "secao", "x_list", "x_create", "x_update")
```

Os dois últimos argumentos (`create_url` e `update_url`) **não são usados por nada** dentro da
fábrica — sobraram de uma versão anterior. Não removi porque a instrução era não mudar
comportamento; remover é seguro e cabe numa faxina futura.

---

## 5 · Os dados

Cinco tabelas, uma migração (`0001_initial`). Quem escreve em cada uma:

| Modelo | O que guarda | Quem escreve | Quem lê |
|---|---|---|---|
| `Contratante` | Quem contrata: nome, telefone, e-mail, endereço, observações, `ativo` | CRUD `/contratantes/`, `/admin/`, `seed_demo` | listas, select do agendamento (só ativos), painel, CSV |
| `Prestadora` | Quem executa: nome, telefone, e-mail, `especialidades` (texto livre), observações, `ativo` | CRUD `/prestadoras/`, `/admin/`, `seed_demo` | idem |
| `Servico` | O catálogo: nome, descrição, `preco`, `duracao_minutos`, `ativo` | CRUD `/servicos/`, `/admin/`, `seed_demo` | idem; o preço é a origem do valor do agendamento |
| `Agendamento` | O evento: FKs para os três acima, `data`, `hora`, `status`, `valor`, observações | CRUD `/agendamentos/`, `/admin/`, `seed_demo` | painel, relatórios, CSV |
| `LogAtividade` | O histórico: usuário, ação (`criou`/`editou`/`removeu`), entidade, descrição, data/hora | **só o `LogMixin` das views do site** | a seção "Atividade recente" dos relatórios |

Detalhes que valem saber:

- **`Base` é abstrato.** `criado_em` e `atualizado_em` existem nas quatro tabelas de cadastro; a
  `LogAtividade` não herda (ela já tem `data_hora`).
- **As três FKs do agendamento são `PROTECT`.** Isso é proposital: apagar um contratante não pode
  levar junto o histórico do que ele contratou. A consequência está na seção 13.
- **`valor` é anulável e se auto-preenche.** `Agendamento.save()` copia `servico.preco` quando o
  campo vem vazio. Por isso o formulário diz "Em branco usa o preço do serviço".
- **`status_cor` é apresentação, não dado.** Traduz o status para o sufixo do badge
  (`warning`, `info`, `success`, `muted`); mora no modelo porque o template não sabe fazer isso.
- **`LogAtividade.usuario` é `SET_NULL`.** Apagar um usuário não apaga o histórico dele — a linha
  fica e a tela mostra "Sistema".
- **Não há índice além das chaves.** O painel filtra por `data__year`/`data__month` e conta por
  status a cada carregamento. No volume de uma agência isso é irrelevante; num volume grande é o
  primeiro lugar a olhar.

---

## 6 · As telas e as rotas

| Rota | View | Template | O que é |
|---|---|---|---|
| `/` | `DashboardView` | `dashboard/dashboard.html` | Quatro números, gráfico de 6 meses, rosca por status, agenda de hoje, próximos 6 |
| `/login/` · `/logout/` | Django (`auth_views`) | `registration/login.html` | A única tela pública. O logout é **POST** (form escondido na barra lateral) |
| `/contratantes/` · `/prestadoras/` · `/servicos/` | `*List` | `crud/list.html` | Mesma tela para os três: busca, tabela montada a partir de `colunas`, paginação de 12 |
| `/agendamentos/` | `AgendamentoList` | `crud/list_agendamentos.html` | Tela própria: colunas vêm de tabelas ligadas, tem filtro de status e badge colorido |
| `/<entidade>/novo/` · `/<entidade>/<pk>/editar/` | fábrica | `crud/form.html` | Mesmo formulário para criar e editar; o rótulo do botão muda com `modo` |
| `/<entidade>/<pk>/remover/` | fábrica | `crud/confirm_delete.html` | Confirmação; o POST é que remove |
| `/relatorios/` | `RelatoriosView` | `dashboard/relatorios.html` | Top 10 por prestadora e por serviço (quantidade e soma), últimas 15 linhas do histórico |
| `/contratantes/exportar/` · `/prestadoras/exportar/` · `/agendamentos/exportar/` | `Export*CSV` | — | CSV com `;` e BOM. **Serviços não tem exportação** |
| `/admin/` | Django admin | — | Bastidores: usuários, e os cinco modelos |

**Por que duas listas e não uma.** A lista genérica imprime células com a tag `coluna_valor`, que
só sabe ler atributos do próprio objeto e três casos especiais (`_situacao`, `_preco`,
`_duracao`). O agendamento precisa de `contratante.nome`, de badge por status e de um `<select>`
de filtro — não cabia sem transformar a tag genérica num interpretador. Foi mais barato duplicar
o template.

**Os gráficos.** As listas Python (`meses_labels`, `status_data`…) são despejadas no JavaScript
com `|safe`, o que funciona porque a representação de uma lista de strings em Python é JSON
válido em JavaScript. Hoje é seguro — todos os rótulos são fixos no código. Deixa de ser no
minuto em que um rótulo vier do banco (seção 13).

---

## 7 · Autenticação e permissões

- **Um só nível de acesso.** `LoginRequiredMixin` em todas as views: quem tem sessão vê e altera
  tudo — contratantes, prestadoras, serviços, agendamentos e relatórios. **Não existem perfis,
  grupos ou permissões por objeto** no código do site.
- **`is_staff`/`is_superuser` só governam o `/admin/`**, que é o Django padrão.
- Usuários são criados por `python manage.py createsuperuser` ou pelo `/admin/`. Não há tela de
  cadastro, nem de "esqueci a senha", nem envio de e-mail (não há `EMAIL_BACKEND` configurado).
- Os validadores de senha são os quatro padrão do Django. Sessão é a de banco, padrão.
- CSRF está ativo (o middleware está na lista e todo formulário tem `{% csrf_token %}`).
  `CSRF_TRUSTED_ORIGINS` vem do `.env` e é o que você vai precisar preencher ao pôr atrás de um
  domínio com HTTPS.

---

## 8 · Configuração, ambientes e deploy

Todas as variáveis são lidas em `config/settings.py` pela função `env()`, do ambiente do processo;
o `python-dotenv` carrega o `maryhouse/.env` antes, **se estiver instalado** (o `import` está num
`try`, então a falta dele não quebra nada — só faz o `.env` ser ignorado em silêncio).

| Variável | Para que serve | Se faltar |
|---|---|---|
| `DATABASE_URL` | O Postgres, no formato `postgres://…` | Cai para SQLite em `maryhouse/db.sqlite3` |
| `SECRET_KEY` | A chave de assinatura de sessão e CSRF | **Usa um valor embutido no código** — ver seção 13 |
| `DEBUG` | Modo de desenvolvimento | Assume `True` |
| `ALLOWED_HOSTS` | Hosts aceitos, separados por vírgula | Assume `*` |
| `CSRF_TRUSTED_ORIGINS` | Origens confiáveis para POST com HTTPS | Fica vazio |

O modelo está em `maryhouse/.env.example`; o `.env` real é ignorado pelo git e **não existe neste
repositório** — nem ele, nem `db.sqlite3`, nem qualquer dado de cliente.

**Deploy: não existe no repositório.** Não há Dockerfile, Procfile, arquivo de CI, receita de
servidor nem servidor de aplicação nas dependências — `requirements.txt` tem quatro pacotes e
Gunicorn/uWSGI e WhiteNoise **não** estão entre eles. As notas de produção do
[README do projeto](../maryhouse/README.md) descrevem o caminho pretendido (DEBUG desligado,
`collectstatic`, WSGI atrás de Nginx, Postgres), não uma configuração pronta. Colocar no ar hoje é
trabalho manual, e o primeiro passo é acrescentar o servidor WSGI ao `requirements.txt`.

---

## 9 · Como conferir

**Não há testes.** O app nem tem o `tests.py` que o `startapp` cria; `python manage.py test` roda
zero casos. Também não há linter, formatter nem CI configurados. O que dá para rodar hoje, com o
ambiente montado (seção 10):

```bash
python manage.py check              # erros de configuração e de modelo
python manage.py makemigrations --check --dry-run   # modelo e migração ainda batem?
python manage.py migrate            # aplica a 0001 num banco limpo
```

Conferência manual antes de entregar qualquer mudança: entrar, criar um agendamento **sem
preencher o valor** (tem de herdar o preço do serviço), editar, filtrar por status, buscar,
exportar os três CSVs e abrir um deles no Excel, e olhar a "Atividade recente" nos relatórios —
as três ações que você acabou de fazer têm de estar lá.

---

## 10 · Receitas

**Montar o ambiente do zero** (de dentro de `maryhouse/`):

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; no Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**Ver o sistema cheio de dados, para demonstração:** `python manage.py seed_demo`. Ele cria o
usuário `admin` (senha fraca, escrita no próprio comando), 6 serviços, 10 contratantes, 5
prestadoras e um número **aleatório** de agendamentos espalhados por ~5 meses para trás e 2
semanas para a frente — roda duas vezes e o total muda. Só roda uma vez de verdade: se já existe
agendamento, ele sai sem tocar em nada. **Nunca em produção.**

**Trocar de SQLite para PostgreSQL:** preencher `DATABASE_URL` no `.env`, rodar `migrate` no banco
novo. Não há script de migração de dados entre os dois; SQLite é para desenvolvimento.

**Acrescentar um campo a uma entidade:** editar `core/models.py` → `python manage.py
makemigrations core` → `migrate` → acrescentar o campo na lista `fields` do form em
`core/forms.py` (senão ele não aparece na tela) → se a coluna deve aparecer na lista, acrescentar
o par `("Rótulo", "atributo")` em `colunas`, na view da entidade.

**Criar uma entidade nova (tabela + CRUD completo):** modelo em `models.py`, `ModelForm` em
`forms.py`, uma `ListView` copiada de `ContratanteList`, uma linha chamando `_make_views(...)`,
cinco rotas em `core/urls.py`, o item no menu em `base.html` e o registro em `admin.py`. O
template não precisa: `crud/list.html` e `crud/form.html` servem.

**Mudar a cor ou o espaçamento do tema:** só em `:root` no topo de `styles.css`. Os tokens estão
todos lá; o resto do arquivo os consome. As cores dos gráficos são a exceção — estão cravadas no
`<script>` do `dashboard.html` e precisam ser trocadas junto, à mão.

**Colocar no ar:** `.env` com `DEBUG=False`, `SECRET_KEY` novo, `ALLOWED_HOSTS` com o domínio e
`CSRF_TRUSTED_ORIGINS` com `https://o-dominio`; `pip install gunicorn` (ainda não está no
`requirements.txt`); `python manage.py collectstatic`; servir `staticfiles/` pelo Nginx e o
`config.wsgi:application` pelo Gunicorn; `createsuperuser` para a conta real.

---

## 11 · Vocabulário interno

| Termo | Significa |
|---|---|
| **Contratante** | O cliente da agência: quem pede o serviço e paga |
| **Prestadora** | Quem executa o serviço (o código usa o feminino em toda parte) |
| **Serviço** | Um item do catálogo, com preço e duração. É de onde o valor do agendamento vem |
| **Agendamento** | O encontro marcado: contratante + prestadora + serviço + data e hora |
| **Status** | Uma de quatro fases fechadas do agendamento: pendente, confirmado, concluído, cancelado |
| **Faturamento do mês** | No painel, a **soma dos valores dos agendamentos concluídos** do mês corrente. Não é caixa: nada no sistema registra pagamento |
| **Seção (`secao`)** | A string que diz à `base.html` qual item do menu acender |
| **Fábrica (`_make_views`)** | A função que gera as classes de criar/editar/remover de uma entidade |
| **Log de atividade** | O histórico de quem criou, editou ou removeu o quê pelo site |
| **Situação** | A coluna "Ativo/Inativo" das listas; vem do booleano `ativo` |

---

## 12 · Status em 09/09/2026

| Área | Estado | Onde conferir |
|---|---|---|
| Modelos e migração | **Pronto.** 5 modelos, 1 migração; modelo e migração batem | `core/models.py`, `core/migrations/0001_initial.py` |
| CRUD das 4 entidades | **Pronto**, com busca, paginação e histórico | `core/views.py`, `core/urls.py` |
| Painel e relatórios | **Pronto.** 4 indicadores, 2 gráficos, 2 agregações, 15 últimas atividades | `dashboard/*.html` |
| Exportação CSV | Pronta para agendamentos, contratantes e prestadoras. **Serviços não tem** | `core/urls.py` |
| Tema e responsivo | Pronto, um CSS único com tokens em `:root`; há breakpoint e menu de gaveta | `styles.css` §Responsivo |
| Autenticação | Login/logout prontos. **Perfis de acesso não existem** | seção 7 |
| Testes | **Não existem.** Nenhum arquivo de teste no repositório | seção 9 |
| Deploy | **Não existe.** Sem Docker, sem CI, sem servidor WSGI nas dependências | seção 8 |
| Notificação (e-mail/WhatsApp), API REST | **Não existem.** Estão listados como evolução futura no README do projeto | `maryhouse/README.md` |
| Documentação | Este arquivo e `maryhouse/README.md` valem. O README da raiz é a vitrine | `docs/` |
| Comentários no código | Todo `.py` escrito à mão abre com um cabeçalho dizendo o que é e por quê; todo template abre com um `{# #}` dizendo que tela é | — |

---

## 13 · Armadilhas conhecidas

- **Remover cadastro com histórico devolve erro 500.** As FKs do agendamento são `PROTECT` e nem a
  view nem o template tratam o `ProtectedError`: clicar em "Sim, remover" num contratante,
  prestadora ou serviço que já tem agendamento derruba a página com erro de servidor, em vez de
  uma mensagem. **É o defeito mais provável de aparecer para o cliente.** O contorno de hoje é
  desmarcar "Ativo" — o cadastro some dos selects e continua no histórico, que é o que o campo
  `ativo` existe para fazer. A correção seria capturar `ProtectedError` no `form_valid` do
  `_Delete` e devolver uma mensagem.
- **`SECRET_KEY` tem um valor embutido no `settings.py`.** Não é uma chave real em uso, é um
  placeholder — mas ele está num repositório **público**, e subir em produção sem definir
  `SECRET_KEY` no ambiente significa assinar sessão e CSRF com uma chave que qualquer um pode ler.
  Mesma família: `DEBUG` assume `True` e `ALLOWED_HOSTS` assume `*` quando não definidos. Os três
  defaults são de conveniência de desenvolvimento e viram risco em produção.
- **`seed_demo` cria `admin` com senha fraca.** Rodado por engano num banco de produção, é uma
  porta aberta com superusuário. O comando não pergunta nada e não tem trava de ambiente.
- **`/admin/` não gera histórico.** O `LogAtividade` é escrito pelo `LogMixin` das views do site;
  quem edita pelo `/admin/` não aparece na "Atividade recente". Se o histórico for tratado como
  auditoria, essa é a fresta.
- **`secao` esquecida numa view nova quebra a página.** `CrudContextMixin.get_context_data` lê
  `self.secao`, mas o mixin não declara esse atributo — só as subclasses o definem. Uma view nova
  que herde o mixin e esqueça o `secao = "..."` levanta `AttributeError` em tempo de requisição,
  não na importação.
- **`|safe` nos dados dos gráficos.** `{{ meses_labels|safe }}` e companhia despejam a
  representação de uma lista Python dentro de um `<script>`. Funciona porque hoje só há strings
  fixas ali. No dia em que um rótulo vier do banco — nome de prestadora, por exemplo — vira
  injeção de script. O certo é `json_script`.
- **Editar um agendamento antigo apagando o campo Valor traz o preço de hoje.** O `save()` só
  olha se o campo está vazio; ele não sabe que o serviço mudou de preço desde então. Para
  registrar "de graça" use `0`, não vazio.
- **As fontes vêm do Google.** `base.html` e `login.html` carregam Fraunces e Plus Jakarta Sans
  de `fonts.googleapis.com`. Numa rede sem saída, o layout continua funcionando, mas com fontes
  de sistema — e o navegador espera o tempo do timeout antes de desistir.
- **Não há validação de conflito de agenda.** Nada impede a mesma prestadora em dois lugares no
  mesmo horário, nem agendamento com data no passado. Se isso passar a incomodar, o lugar é um
  `clean()` no `AgendamentoForm`.
- **`login.html` e `base.html` duplicam o `<head>`.** A tela de login não estende `base.html` (não
  tem barra lateral); trocar a fonte ou o favicon é trocar nos dois.
- **Rodar os comandos de dentro de `maryhouse/`.** O `manage.py` não está na raiz do repositório;
  rodar de fora dá "No such file or directory".
