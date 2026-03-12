

# ZRB Toolkit — Zoned Role‑Based Access Control Framework

The **ZRB Toolkit** is a Python framework that implements the **Zoned Role‑Based (ZRB)** methodology for the **analysis, design, implementation, maintenance, and enforcement of access control** in enterprise information systems.

It models **zones**, **roles**, **operations**, and **users**, supports **intra‑zone role hierarchies** and **inter‑zone (gamma) inheritance**, and evaluates permissions in **direct (n\_rzbac)** and **inferential (i\_rzbac)** modes with a pluggable **constraints** engine (SoD, temporal, attribute, context, positive “allow‑only‑if”).

***

## Table of Contents

*   features
*   architecture
*   installation
*   quick-start
*   configuration-yaml
*   web-integration
    *   flask
    *   django
*   constraints
*   storage-backends
*   cli
*   admin-api--minimal-ui
*   testing
*   documentation
*   roadmap
*   contributing
*   license

***

## Features

*   **Zoned model**: hierarchical zones; hierarchical roles per zone; gamma mappings for inter‑zone inheritance.
*   **Access engine**: direct (n\_rzbac) vs inferential (i\_rzbac) modes, with caching.
*   **Constraints framework**:
    *   Separation‑of‑Duty (SoD): static (role conflicts) & dynamic (operation conflicts).
    *   Temporal: time windows, days.
    *   Attribute‑based: user attributes (e.g., clearance levels).
    *   Context‑based: IP, device, location, request metadata.
    *   Positive constraints: “allow only if condition is satisfied”.
*   **Storage**: SQLAlchemy ORM backend + in‑memory store for tests/demos.
*   **Web integration**: decorators/middleware for Flask & Django.
*   **CLI**: DB init, YAML import, validation, inspection.
*   **Admin API**: Flask‑RESTX endpoints; optional minimal Jinja2 UI.
*   **Examples**: runnable app under `examples/`.
*   **Tests**: pytest suite with memory store.

***

## Architecture

    zrb/
    ├─ core/         # Pydantic models & enums (User, Zone, Role, Operation, Constraint, etc.)
    ├─ engine/       # AccessEngine, gamma and role-hierarchy resolution, caching
    ├─ storage/      # Storage interface, SQLAlchemy and in-memory implementations
    ├─ constraints/  # Evaluators (SoD, temporal, attribute, context, positive) + registry
    ├─ web/          # Flask and Django integration
    ├─ cli/          # 'zrb' command entrypoint (Click)
    ├─ admin/        # Admin API (Flask-RESTX) and optional UI
    └─ validation/   # Structural configuration validation hooks

**Key ideas**

*   **Direct mode** uses a role’s base permissions only.
*   **Inferential mode** computes effective permissions via **role hierarchy** (intra‑zone) and **gamma mappings** (inter‑zone), then applies **constraints**.

***

## Installation

```bash
# Recommended: Python 3.11+
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install toolkit (editable for development)
pip install -e .

# Optional extras for examples and docs
pip install flask flask-login
# For docs (MkDocs + Material and mkdocstrings):
# pip install mkdocs mkdocs-material mkdocstrings[python]
```

***

## Quick Start

### 1) Minimal programmatic usage

```python
from zrb.engine import AccessEngine
from zrb.storage.memory import MemoryStore
from zrb.core.models import User, Zone, Role, Operation
from zrb.core.types import AccessMode

# Storage & seed
store = MemoryStore()
store.add_zone(Zone(id="root", name="Root"))
store.add_operation(Operation(id="grade:view", app_name="university", name="view"))
store.add_role(Role(id="faculty_reader", zone_id="root", name="FacultyReader",
                    base_permissions={"grade:view"}))

# User & assignment
u = User(id="u1", username="alice", email="a@u.edu")
store.add_user(u)
store.assign_user_to_role(u.id, "root", "faculty_reader")

# Decide
engine = AccessEngine(store)
zone = store.get_zone("root")
op = store.get_operation("grade:view")
allowed = engine.decide(u, op, zone, mode=AccessMode.INFERENTIAL)
print("Allowed?", allowed)  # True
```

### 2) Example application

A runnable Flask demo is included:

```bash
export FLASK_APP=examples/university/app.py
pip install flask-login
python examples/university/app.py
# Visit:
#   http://127.0.0.1:5000/login/1  (log in demo user)
#   http://127.0.0.1:5000/grade    (protected route)
```

***

## Configuration (YAML)

You can define zones, roles, and operations in YAML and import them via CLI:

```yaml
# examples/university/config.yaml
zones:
  - { id: root, name: Root }

operations:
  - { id: grade:view, app_name: university, name: view_grade }

roles:
  - id: faculty_reader
    zone_id: root
    name: FacultyReader
    base_permissions: [grade:view]
```

***

## Web Integration

### Flask

```python
from flask import Flask
from flask_login import LoginManager, UserMixin, login_user
from zrb.engine import AccessEngine
from zrb.storage.memory import MemoryStore
from zrb.web.flask import ZRBFlask

app = Flask(__name__)
app.secret_key = "secret"

store = MemoryStore()
# ...seed zones/roles/ops/users...
engine = AccessEngine(store)
zrb = ZRBFlask(app, engine)

@app.route("/grade")
@zrb.i_rzbac(operation="grade:view")
def view_grades():
    return "Grades page"
```

### Django

```python
# middleware/decorators exist under zrb.web.django
# Example usage (pseudo):
from zrb.web.django import ZRBDjango

zrb_django = ZRBDjango(engine=my_engine)

@zrb_django.i_rzbac(operation="grade:view")
def view_grades(request):
    ...
```

***

## Constraints

The constraint engine evaluates **negative** (deny‑on‑match) and **positive** (allow‑only‑if satisfied) rules. Examples:

*   **SoD (roles)**: deny if a user simultaneously holds conflicting roles in a zone.
*   **SoD (operations)**: deny if user executes conflicting operations in a session/time window.
*   **Temporal**: allow only within business hours or specific days.
*   **Attribute**: allow only if `user.attributes["clearance"] >= 5`.
*   **Context**: allow only if `context["ip"]` is whitelisted.
*   **Positive**: explicitly require a condition to be satisfied (e.g., MFA passed).

You can register custom evaluators via the `ConstraintRegistry`.

***

## Storage Backends

*   **SQLAlchemyStore** — production‑ready relational store (SQLite, Postgres, MySQL, etc.).
*   **MemoryStore** — in‑memory store for tests, demos, and prototyping.

Both implement a common `Storage` interface and support role hierarchy traversal and gamma mapping lookups.

***

## CLI

The `zrb` CLI helps bootstrap databases, import/export configuration, and validate models.

```bash
# Initialize database (SQLite)
zrb init --db sqlite:///zrb.db

# Import YAML config
zrb import-config examples/university/config.yaml --db sqlite:///zrb.db

# Validate configuration
zrb validate --db sqlite:///zrb.db

# Inspect a zone
zrb zone-show root --db sqlite:///zrb.db
```

***

## Admin API & Minimal UI

A Flask‑RESTX admin API provides endpoints for managing zones/roles/assignments. Optionally enable a minimal Jinja2 web UI for quick administration. (Extend `zrb/admin/api.py` and add templates under `zrb/admin/templates/` as needed.)

***

## Testing

```bash
pip install -r requirements-dev.txt
pytest -q
```

Tests favor the `MemoryStore` for speed and isolation. Add database‑backed tests by pointing to a test database and seeding fixtures.

***

## Documentation

We recommend **MkDocs + Material** with `mkdocstrings` for API pages.

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
mkdocs serve   # local docs server on http://127.0.0.1:8000
```

Add a `mkdocs.yml` and `docs/` folder with conceptual and API pages. For Read the Docs, include `.readthedocs.yaml`.

***

## Roadmap

*   Rich SoD policy language + audit trail
*   Policy versioning & change impact analysis
*   Fine‑grained operation metadata (resources, scopes, conditions)
*   Import/export for multiple formats (YAML/JSON/CSV)
*   Admin SPA (React/Vue) backed by the Admin API
*   First‑class multi‑tenant helpers
*   Performance benchmarks & tuning guide

***

## Contributing

Contributions welcome! Please:

1.  Fork the repo; create a feature branch.
2.  Run `black`, `flake8`, and tests (`pytest -q`) before opening a PR.
3.  Include docs and examples for new features.

Consider adding a `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` for your community standards.

***

## License

**MIT License** — see `LICENSE` for details.

***

### Badges (optional)

Add badges once CI and publishing are configured:


![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg) ![License MIT](https://img.shields.io/badge/license-MIT-green.svg) ![Build passing](https://img.shields.io/badge/build-passing-brightgreen.svg) ![Status alpha](https://img.shields.io/badge/status-alpha-orange.svg)

