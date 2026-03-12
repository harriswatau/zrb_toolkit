# ZRB User Guide

## Modelling and Implementing Organizational Information Systems with ZRB

**Version:** 0.1.0  
**Date:** March 2026  
**Author:** Harris Wang  
**License:** MIT  
**Repository:** [https://github.com/harriswatau/zrb_toolkit](https://github.com/harriswatau/zrb_toolkit)

# ZRB Methodology and Toolkit: A Developer’s Guide

Welcome! You are about to embark on a journey to build enterprise systems that are **secure by design**, **maintainable**, and **perfectly aligned with your organisation’s structure**. The **Zoned Role-Based (ZRB) framework** provides a mathematically formal yet practical approach to access control and system architecture. Instead of bolting on security as an afterthought, ZRB makes it an emergent property of how you model your organisation.

This guide is your companion for designing and implementing real‑world systems using the **ZRB Python toolkit**. Whether you are a software architect, a developer, or a security engineer, you will learn how to:

- Model your enterprise as a hierarchy of zones.
- Define roles, permissions, and inheritance rules.
- Enforce fine‑grained constraints (separation of duty, temporal, attribute‑based).
- Integrate seamlessly with Django or Flask.
- Test, simulate, and deploy with confidence.

Throughout the guide we use concrete examples – a university, a hospital, an e‑commerce platform, a project management tool, and a banking system – to illustrate every concept. By the end, you will be equipped to apply ZRB to your own projects and build systems that are not only robust but also a joy to maintain.

Let’s get started.

## Table of Contents
1. [Introduction to ZRB](#introduction)
2. [Core Concepts](#core-concepts)
3. [Designing a System with ZRB](#designing)
4. [Getting Started with the ZRB Toolkit](#getting-started)
5. [Defining the ZRB Configuration](#defining-config)
6. [Integrating with Web Frameworks](#web-integration)
   - [Django Integration](#django)
   - [Flask Integration](#flask)
7. [Implementing Constraints](#constraints)
8. [Testing and Simulation](#testing)
9. [Advanced Topics](#advanced)
   - [Custom Constraint Evaluators](#custom-constraints)
   - [Extending the Storage Backend](#custom-storage)
   - [Performance Tuning](#performance)
10. [Best Practices](#best-practices)
11. [Conclusion](#conclusion)

---

## 1. Introduction to ZRB <a name="introduction"></a>

The **Zoned Role-Based (ZRB) framework** is a comprehensive methodology for building secure, maintainable enterprise systems. It extends traditional RBAC by introducing **zones** – hierarchical organizational units that mirror the real‑world structure of an enterprise. Within each zone, roles are defined, and permissions are assigned to operations. Zones can contain sub‑zones, forming a **zone tree**. Roles can inherit permissions from other roles within the same zone (**intra‑zone hierarchy**) and from roles in parent zones (**inter‑zone inheritance** via **gamma mappings**). Additionally, **constraints** (separation of duty, temporal, attribute, context) provide fine‑grained control over access.

The **ZRB Python toolkit** implements this methodology, providing:

- A **core model** for zones, roles, operations, users, and constraints.
- A **storage abstraction** (with a SQLAlchemy backend) for persistence.
- An **access control engine** that computes effective permissions and evaluates constraints efficiently, with caching.
- **Web framework integrations** (Django, Flask) with decorators to protect views.
- A **command‑line interface** for configuration management.
- **Validation** utilities to detect conflicts.

This guide walks you through designing an enterprise system with ZRB and implementing it using the toolkit.

---

## 2. Core Concepts <a name="core-concepts"></a>

### Zones
A zone represents an organizational unit (e.g., department, division, project). Zones form a tree; the root is the entire enterprise. Each zone has:
- `id`: unique identifier
- `name`: human‑readable name
- `parent_id`: reference to the parent zone (None for root)

### Roles
A role is a job function within a specific zone. Roles have:
- `id`: unique identifier
- `zone_id`: the zone where the role exists
- `name`
- `parent_role_id`: (optional) points to a junior role in the same zone (senior roles inherit permissions from junior roles)
- `base_permissions`: a set of operation IDs explicitly granted to the role

### Operations
An operation is a minimal executable action (e.g., `grade:submit`, `order:create`). Operations are identified by a unique string and belong to an application.

### Users
Users are individuals who can be assigned to roles within zones. Each user has:
- `id`: must match the identifier used by the authentication system
- `username`, `email`, `attributes` (for attribute‑based constraints)

### Gamma Mappings
Inter‑zone inheritance: a role in a child zone can inherit permissions from a role in a parent zone. A gamma mapping consists of:
- `child_zone_id`, `child_role_id`
- `parent_zone_id`, `parent_role_id`
- `weight` (0‑1) for partial inheritance
- `priority` for conflict resolution

### Constraints
Constraints are rules that can block or require certain conditions. Types:
- **Separation of Duty (SoD)**: prohibits a user from performing an action if they hold another role or are the resource owner.
- **Temporal**: allows access only during specific time windows.
- **Attribute**: checks user or resource attributes against thresholds.
- **Context**: requires certain key‑value pairs in the request context.

### Access Modes
- **Direct (`n_rzbac`)**: only base permissions of the assigned roles are considered.
- **Inferential (`i_rzbac`)**: full effective permissions, including intra‑zone and inter‑zone inheritance.

---

## 3. Designing a System with ZRB <a name="designing"></a>

Follow these steps to design your enterprise system:

### Step 1: Model the Organizational Structure
Identify all organizational units (departments, teams, projects). Draw a tree. Example: a university has Faculties, each with Departments.

### Step 2: Define Operations
List every action that requires protection. Group them by application. Example:
- `grade:view` – view grades
- `grade:submit` – submit final grades
- `course:enroll` – enroll in a course

### Step 3: Define Roles per Zone
For each zone, list the job functions. Decide which operations each role should have **directly**. Then define intra‑zone hierarchies: senior roles (e.g., Department Head) inherit from junior roles (Professor, TA, Student). Use `parent_role_id` to link a role to its junior.

### Step 4: Plan Inter‑Zone Inheritance
Decide which roles in child zones should inherit from roles in parent zones. For each such relationship, create a gamma mapping. Example: a CS Department Professor inherits from the Faculty of Engineering Professor.

### Step 5: Identify Constraints
Add separation of duty (e.g., a student cannot be a TA in the same course), temporal (grade submission only during exam period), or attribute‑based rules (reorder only when stock < 10).

### Step 6: Assign Users to Roles
Map actual users to roles in specific zones.

The output of the design phase is a **ZRB configuration** – a YAML/JSON file containing all entities. This configuration is then loaded into the toolkit’s storage.

---

## 4. Getting Started with the ZRB Toolkit <a name="getting-started"></a>

### Installation
```bash
pip install zrb-toolkit
```

This installs the core library, SQLAlchemy storage, and the CLI.

### Basic Components
- **Storage**: `SQLAlchemyStore` – connects to a database (SQLite, PostgreSQL, etc.).
- **Engine**: `AccessEngine` – the main decision‑maker.
- **Web Integrations**: `zrb.web.django` and `zrb.web.flask` provide middleware and decorators.

### Initialising the Database
```python
from zrb.storage.sqlalchemy import SQLAlchemyStore
store = SQLAlchemyStore('sqlite:///zrb.db')
store.create_all()  # creates tables
```

---

## 5. Defining the ZRB Configuration <a name="defining-config"></a>

The toolkit can load configuration from YAML. Below is a simplified excerpt from the University system.

```yaml
zones:
  - id: root
    name: University
  - id: eng
    name: Faculty of Engineering
    parent_id: root
  - id: cs
    name: Computer Science
    parent_id: eng

operations:
  - id: grade:view
    app_name: grading
    name: View grades
  - id: grade:submit
    app_name: grading
    name: Submit grades

roles:
  - id: prof_eng
    zone_id: eng
    name: Professor
    base_permissions: ["grade:submit", "course:view"]
  - id: prof_cs
    zone_id: cs
    name: Professor
    base_permissions: []   # inherits via gamma

gamma_mappings:
  - child_zone_id: cs
    child_role_id: prof_cs
    parent_zone_id: eng
    parent_role_id: prof_eng
    priority: 1

constraints:
  - id: temporal_grade_submit
    type: temporal
    target: { operation_id: "grade:submit" }
    condition: { time_range: ["2025-05-01T00:00", "2025-06-15T23:59"] }
    is_negative: false
    priority: 10

users:
  - id: u1
    username: alice
    email: alice@uni.edu
    attributes: {}

assignments:
  - user_id: u1
    zone_id: cs
    role_id: prof_cs
```

### Loading the Configuration
Use the provided CLI command (or write a custom script):
```bash
zrb import --db sqlite:///zrb.db config.yaml
```
Or in Python:
```python
import yaml
from zrb.storage.sqlalchemy import SQLAlchemyStore
store = SQLAlchemyStore('sqlite:///zrb.db')
with open('config.yaml') as f:
    config = yaml.safe_load(f)
# ... loop and create objects (as shown in management commands)
```

---

## 6. Integrating with Web Frameworks <a name="web-integration"></a>

### 6.1 Django Integration <a name="django"></a>

#### Middleware
Add `'zrb.web.django.ZRBDjango'` to `MIDDLEWARE`. You need to configure it to resolve the current zone. A typical implementation:

```python
# middleware.py
from django.conf import settings
from zrb.storage.sqlalchemy import SQLAlchemyStore
from zrb.web.django import ZRBDjango

zrb_store = SQLAlchemyStore(settings.ZRB_DATABASE_URL)

class ZoneMiddleware(ZRBDjango):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.store = zrb_store

    def _zone_from_request(self, request):
        host = request.get_host().split(':')[0]
        subdomain = host.split('.')[0] if '.' in host else None
        mapping = {
            'cs': 'cs',
            'eng': 'eng',
            None: 'root',
        }
        zone_id = mapping.get(subdomain, 'root')
        return self.store.get_zone(zone_id)
```

Then in `settings.py`:
```python
MIDDLEWARE = [
    # ...
    'yourapp.middleware.ZoneMiddleware',
]
```

#### Decorators
Use `@i_rzbac` and `@n_rzbac` to protect views:

```python
from zrb.web.django import i_rzbac, n_rzbac

@login_required
@i_rzbac(operation='grade:view')
def view_grades(request):
    # ...
```

The decorator automatically:
- Retrieves the current user (`request.user`).
- Retrieves the current zone (`request.zone` – set by middleware).
- Resolves the operation (if `operation` is not given, it uses the URL name).
- Calls `engine.decide()`.
- Returns `HttpResponseForbidden` if denied.

You must set up the engine and store globally (e.g., in `settings.py` or `apps.py`). Example:

```python
# settings.py
ZRB_DATABASE_URL = 'sqlite:///zrb.db'
ZRB_ENGINE = None  # will be lazily created

# In middleware or app ready, create engine
from zrb.engine.access import AccessEngine
from zrb.storage.sqlalchemy import SQLAlchemyStore
store = SQLAlchemyStore(settings.ZRB_DATABASE_URL)
engine = AccessEngine(store)
# Then make it available to the decorators (the decorators import from a global; you need to set it)
import zrb.web.django
zrb.web.django.engine = engine
```

### 6.2 Flask Integration <a name="flask"></a>

#### Extension
```python
from flask import Flask
from zrb.web.flask import ZRBFlask
from zrb.storage.sqlalchemy import SQLAlchemyStore
from zrb.engine.access import AccessEngine

app = Flask(__name__)
store = SQLAlchemyStore('sqlite:///zrb.db')
engine = AccessEngine(store)
zrb = ZRBFlask(app, engine)  # registers before_request to set request.zone
```

You need to implement a method to resolve the zone from the request. Subclass `ZRBFlask` or set a custom `zone_resolver` function:

```python
def zone_from_request():
    host = request.host
    # ... mapping logic ...
    return store.get_zone(zone_id)

zrb.zone_resolver = zone_from_request
```

#### Decorators
```python
@app.route('/grades')
@login_required
@zrb.i_rzbac(operation='grade:view')
def view_grades():
    return jsonify(grades=...)
```

---

## 7. Implementing Constraints <a name="constraints"></a>

Constraints are evaluated by the engine during `decide()`. They rely on the **context** dictionary passed to the decision function.

### Built‑in Constraint Evaluators

- **SoD**: Expects a context key (e.g., `creator_id`) and compares with `user.id`. The condition `{"prohibited_relation": "self"}` triggers denial if they match.
- **Temporal**: Expects `current_time` (ISO time string) in context, or uses system time. Condition `{"time_range": ["09:00","17:00"]}` checks if current time falls within.
- **Attribute**: Expects an attribute (from user or context) and compares using operator. Example: `{"attribute": "stock_level", "operator": "<", "value": 10}`.
- **Context**: Expects context keys to match given values. Example: `{"environment": "qa"}`.

### Providing Context in Django Views

The decorators do not automatically pass context. You have two options:

1. **Call the engine directly** in the view:
   ```python
   from django.conf import settings
   from zrb.storage.sqlalchemy import SQLAlchemyStore
   from zrb.engine.access import AccessEngine

   store = SQLAlchemyStore(settings.ZRB_DATABASE_URL)
   engine = AccessEngine(store)

   def my_view(request):
       context = {'amount': request.POST.get('amount')}
       user = store.get_user(str(request.user.id))
       op = store.get_operation('withdraw')
       zone = request.zone
       if not engine.decide(user, op, zone, mode='inferential', context=context):
           return HttpResponseForbidden()
       # ... proceed
   ```

2. **Extend the decorators** to accept a `context_func` that extracts context from the request.

### Example: Temporal Constraint in Django

In the view, you would pass the current time:
```python
from datetime import datetime

def submit_grade(request):
    context = {'current_time': datetime.now().isoformat()}
    # ... use engine.decide with context
```

---

## 8. Testing and Simulation <a name="testing"></a>

The toolkit includes a `decide()` method that can be used for unit testing. Example:

```python
def test_professor_can_submit_grades():
    store = SQLAlchemyStore('sqlite:///test.db')
    # ... load test config ...
    engine = AccessEngine(store)
    user = store.get_user('u1')
    zone = store.get_zone('cs')
    op = store.get_operation('grade:submit')
    assert engine.decide(user, op, zone) is True
```

You can also write simulation scripts that iterate over many requests and measure performance.

---

## 9. Advanced Topics <a name="advanced"></a>

### 9.1 Custom Constraint Evaluators <a name="custom-constraints"></a>

To add a new constraint type:

1. Subclass `ConstraintEvaluator` and implement `evaluate()`.
2. Register it with the `ConstraintRegistry`.

Example:
```python
from zrb.constraints.base import ConstraintEvaluator
from zrb.constraints.registry import ConstraintRegistry

class WeekendEvaluator(ConstraintEvaluator):
    def evaluate(self, constraint, user, role, zone, operation, context=None):
        # condition: {"days": ["Sat","Sun"]}
        from datetime import datetime
        weekday = datetime.now().strftime('%a')
        return weekday in constraint.condition.get('days', [])

registry = ConstraintRegistry()
registry._evaluators['weekend'] = WeekendEvaluator()
```

Then use `type: weekend` in your constraint definitions.

### 9.2 Custom Storage Backend <a name="custom-storage"></a>

Implement the `Storage` interface (see `zrb.storage.base.Storage`) and pass it to the engine. This allows using NoSQL databases, REST APIs, etc.

### 9.3 Performance Tuning <a name="performance"></a>

- The engine caches effective permissions with a TTL. Adjust cache size and TTL in `AccessEngine` constructor.
- For high‑traffic systems, use Redis or Memcached as a backend for the cache (custom `PermissionCache` implementation).
- Ensure database indexes on foreign keys (`zone_id`, `role_id`, etc.).

---

## 10. Best Practices <a name="best-practices"></a>

1. **Start with a clear zone tree**: Involve business stakeholders to validate the organizational structure.
2. **Keep role hierarchies shallow**: Deep hierarchies can become hard to debug.
3. **Use gamma mappings sparingly**: Prefer intra‑zone inheritance unless cross‑zone sharing is truly needed.
4. **Name operations consistently**: Use `app:action` format (e.g., `inventory:reorder`).
5. **Version your ZRB configuration**: Store it in version control alongside your code.
6. **Test constraints thoroughly**: Write unit tests for each constraint scenario.
7. **Monitor performance**: Use logging to track cache hit rates and decision latency.
8. **Document roles and permissions**: Maintain a human‑readable matrix for auditors.

---

## 11. Conclusion <a name="conclusion"></a>

The ZRB methodology and toolkit provide a powerful, formal approach to building secure enterprise systems. By aligning access control with organizational structure, you reduce complexity, improve maintainability, and ensure that security is an emergent property of the design, not an afterthought.

This guide has covered the essentials – from design principles to practical implementation with Django and Flask. For more detailed API documentation, refer to the [ZRB Toolkit Reference](https://github.com/yourname/zrb-toolkit/docs). The example systems (University, Hospital, E‑Commerce, Project Management, Banking) provide complete, runnable code that you can adapt to your own needs.

Now go build systems that are secure by design!