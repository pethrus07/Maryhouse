[Português](README.pt-BR.md) | English

# Scheduling system for a cleaning agency

> **Archived (2026-11).** Commercial follow-up ended in September 2026. No deploy is configured in this repository.

Internal system for a small domestic cleaning agency in João Pessoa, Brazil. It records clients, service providers and the service catalog, and ties the three together in a booking with date, time, status and price. Dashboard, reports, CSV export and an activity log, all behind a login.

## What it was

The agency's operation comes down to four questions: who asked, who goes, which day, how much. When that lives in a notebook and WhatsApp chats, the answer depends on who you ask and there is no history. This system answers the four questions in one place. It is not an ERP: no invoices, no cash control, no customer area, no public API. Only the internal team uses it.

It was rewritten in Django in 2026. A later proposal (new website plus moving the system to Cloudflare Workers) did not go ahead.

## Stack

- Python 3.10+ and Django 5.1, one app (`core`).
- PostgreSQL through `DATABASE_URL`; without it, a local SQLite file.
- Server-rendered HTML and own CSS, no front-end framework. Chart.js vendored in the repo (no CDN).

## Run locally

From inside `maryhouse/`:

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo        # demo user admin / admin123 and fictitious data
python manage.py runserver        # http://127.0.0.1:8000
```

Without a `.env` the system starts in development mode on SQLite. `seed_demo` creates a weak demo password and must never run in production. Environment variables are listed in `maryhouse/.env.example`.

## Tests

```bash
cd maryhouse
python manage.py test
```

`core/tests.py` is a smoke test: the login page opens, every screen and export redirects to login when anonymous, and with the demo data every screen opens, exports come out as CSV and deleting a client writes to the activity log.

## Folder structure

```
maryhouse/README.md     install guide and production notes (Portuguese)
docs/ARQUITETURA.md     full manual: flow, models, screens, recipes, traps (Portuguese)
docs/arquitetura/       diagrams (UML, BPMN, C4)
maryhouse/              the Django project
  config/               settings, root urls, wsgi
  core/                 models, forms, views, urls, admin, templatetags,
                        seed_demo, migrations, static/ (CSS + Chart.js), templates/, tests.py
```

## What I learned

- **One list template for three entities.** Clients, providers and services share the same list and form templates; the view declares the columns and a template tag formats them. Bookings got their own template because forcing the generic one would have turned a tag into an expression interpreter.
- **A view factory instead of twelve classes.** `_make_views()` builds Create, Update and Delete for each entity, which kept `views.py` around 400 lines.
- **Audit in the view, not in a signal.** The request is the only place that knows who did it from the screen. The trade-off is that edits through `/admin/` are not logged.
- **`PROTECT` on booking foreign keys.** Deleting a client cannot take its history with it. The `ativo` flag hides records without losing the past.
- **Development defaults are a risk.** `settings.py` falls back to an embedded secret key, `DEBUG=True` and `ALLOWED_HOSTS=*` when no `.env` exists. A safer version (secure defaults, key required outside development) is in branch `revisao-2026-11`.

## License

All rights reserved. Published as portfolio; not licensed for reuse. See [LICENSE](LICENSE).
