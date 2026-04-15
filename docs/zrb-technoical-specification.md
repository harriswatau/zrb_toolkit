# ZRB Python Toolkit: Technical Specifications

## 1. Introduction

The ZRB (Zoned Role-Based) Python toolkit is a complete implementation of the Zoned Role-Based framework for building secure, maintainable enterprise systems. It provides a formal model for defining organizational structure (zones), roles, permissions, and constraints, and enforces access control with high performance and scalability.

This document describes the architecture, modules, classes, and methods of the toolkit, serving as a comprehensive reference for developers, integrators, and contributors.

## 2. Architecture Overview

The toolkit is organized into several logical layers:

- **Core**: Data models and type definitions.
- **Storage**: Pluggable persistence layer (SQLAlchemy provided).
- **Engine**: Permission computation, caching, and access decisions.
- **Constraints**: Extensible constraint evaluation.
- **Web**: Integration with Django and Flask (decorators, middleware).
- **CLI**: Command-line interface for configuration management.
- **Validation**: Consistency and conflict checking.
- **Utils**: Tree and graph algorithms for zone/role hierarchies.

All components are designed to be modular and extensible.

## 3. Core Module (`zrb.core`)

### 3.1 Types (`zrb.core.types`)

**Enumerations**

```python
from enum import Enum

class ConstraintType(str, Enum):
    SOD = "separation_of_duty"
    TEMPORAL = "temporal"
    ATTRIBUTE = "attribute"
    CONTEXT = "context"

class AccessMode(str, Enum):
    DIRECT = "direct"          # n_rzbac
    INFERENTIAL = "inferential" # i_rzbac
```

### 3.2 Models (`zrb.core.models`)

All models are Pydantic `BaseModel` classes for validation and serialization.

#### `User`

```python
class User(BaseModel):
    id: str
    username: str
    email: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
```

Represents a system user. The `id` should match the identifier used in the authentication system. `attributes` hold key‑value pairs for attribute‑based constraints.

#### `Operation`

```python
class Operation(BaseModel):
    id: str
    app_name: str
    name: str
    description: str = ""
```

A minimal executable unit. `id` is globally unique; `app_name` groups operations by application.

#### `Zone`

```python
class Zone(BaseModel):
    id: str
    name: str
    parent_id: Optional[str] = None
    description: str = ""
```

A node in the zone tree. `parent_id` references another zone; `None` indicates the root.

#### `Role`

```python
class Role(BaseModel):
    id: str
    zone_id: str
    name: str
    parent_role_id: Optional[str] = None
    description: str = ""
    base_permissions: Set[str] = Field(default_factory=set)  # operation ids
```

A role belongs to exactly one zone. `parent_role_id` defines the intra‑zone hierarchy (senior role inherits from junior). `base_permissions` are the explicitly granted operations.

#### `UserZoneRole`

```python
class UserZoneRole(BaseModel):
    user_id: str
    zone_id: str
    role_id: str
    assigned_at: datetime = Field(default_factory=datetime.now)
```

Assigns a user to a role within a specific zone.

#### `GammaMapping`

```python
class GammaMapping(BaseModel):
    child_zone_id: str
    child_role_id: str
    parent_zone_id: str
    parent_role_id: str
    weight: float = 1.0
    priority: int = 0
```

Defines inter‑zone inheritance: a role in a child zone inherits from a role in a parent zone. `weight` (0‑1) allows partial inheritance; `priority` resolves conflicts (lower number = higher priority).

#### `Constraint`

```python
class Constraint(BaseModel):
    id: str
    type: ConstraintType
    target: Dict[str, Any]      # e.g., {"user_id": "u1", "operation_id": "op1"}
    condition: Dict[str, Any]    # e.g., {"time_range": ["09:00","17:00"]}
    is_negative: bool = True
    priority: int = 0
```

A restriction on access. `is_negative=True` means a deny rule; `False` means a required positive condition. `priority` handles override order.

---

## 4. Storage Layer (`zrb.storage`)

The storage layer abstracts persistence of ZRB configuration. The base interface `Storage` defines all required methods; the SQLAlchemy implementation `SQLAlchemyStore` provides a concrete backend.

### 4.1 Base Interface (`zrb.storage.base.Storage`)

```python
from abc import ABC, abstractmethod
from typing import Optional, List, Set, Dict

class Storage(ABC):
    # Read methods
    @abstractmethod
    def get_user(self, user_id: str) -> Optional[User]:
        """Retrieve a user by ID."""
        pass

    @abstractmethod
    def get_zone(self, zone_id: str) -> Optional[Zone]:
        """Retrieve a zone by ID."""
        pass

    @abstractmethod
    def get_role(self, role_id: str) -> Optional[Role]:
        """Retrieve a role by ID."""
        pass

    @abstractmethod
    def get_operation(self, op_id: str) -> Optional[Operation]:
        """Retrieve an operation by ID."""
        pass

    @abstractmethod
    def get_user_roles(self, user_id: str, zone_id: str) -> List[Role]:
        """Return all roles of user in given zone."""
        pass

    @abstractmethod
    def get_zone_roles(self, zone_id: str) -> List[Role]:
        """Return all roles defined in a zone."""
        pass

    @abstractmethod
    def get_zone_children(self, zone_id: str) -> List[Zone]:
        """Return immediate child zones of the given zone."""
        pass

    @abstractmethod
    def get_child_roles(self, role_id: str) -> List[Role]:
        """Return roles that have the given role as parent (intra‑zone hierarchy)."""
        pass

    @abstractmethod
    def get_gamma_mappings(self, child_zone_id: str, child_role_id: str) -> List[GammaMapping]:
        """Return gamma mappings for a specific (zone, role) pair."""
        pass

    @abstractmethod
    def get_constraints(self, **filters) -> List[Constraint]:
        """Return constraints matching the given filters (e.g., target__contains)."""
        pass

    # Write methods (to be implemented by concrete stores)
    @abstractmethod
    def create_user(self, user: User) -> None:
        pass

    @abstractmethod
    def update_user(self, user: User) -> None:
        pass

    @abstractmethod
    def delete_user(self, user_id: str) -> None:
        pass

    # Similar CRUD for Zone, Role, Operation, GammaMapping, Constraint, UserZoneRole
    # ... (omitted for brevity but follow same pattern)
```

### 4.2 SQLAlchemy Implementation (`zrb.storage.sqlalchemy.SQLAlchemyStore`)

Uses SQLAlchemy ORM to persist ZRB entities. Constructor:

```python
def __init__(self, database_url: str, echo: bool = False):
    """
    Args:
        database_url: SQLAlchemy database URL (e.g., 'sqlite:///zrb.db')
        echo: If True, log SQL statements.
    """
    self.engine = create_engine(database_url, echo=echo)
    self.Session = sessionmaker(bind=self.engine)
```

**Methods**:

- `create_all()`: Creates all tables.
- `drop_all()`: Drops all tables.
- All read methods from `Storage` are implemented using SQLAlchemy queries.
- All write methods perform appropriate `session.add/delete/commit`.

**Helper conversion methods** (private) convert between ORM models and core models.

---

## 5. Access Control Engine (`zrb.engine`)

### 5.1 Inheritance Resolver (`zrb.engine.inheritance.InheritanceResolver`)

Computes effective permissions by traversing intra‑zone hierarchies and gamma mappings.

```python
class InheritanceResolver:
    def __init__(self, storage: Storage):
        self.storage = storage
        self._role_hierarchy_cache: Dict[str, List[str]] = {}  # role_id -> junior role ids

    def get_junior_roles(self, role_id: str, zone_id: str) -> List[Role]:
        """
        Return all roles in the same zone that are junior to the given role (including itself).
        Uses transitive closure of parent_role_id.
        """
        pass

    def compute_effective_permissions(self, role_id: str, zone_id: str) -> Set[str]:
        """
        Compute effective permissions for a role in a zone by:
        1. Union of base permissions of all junior roles (intra‑zone hierarchy).
        2. Recursively adding permissions from gamma‑mapped parent roles (inter‑zone).
        """
        pass

    def _gamma_inherit(self, role_id: str, zone_id: str) -> Set[str]:
        """Helper that traverses gamma mappings up the zone ancestry."""
        pass
```

### 5.2 Cache (`zrb.engine.cache.PermissionCache`)

Caches effective permission sets to reduce database and computation overhead.

```python
class PermissionCache:
    def __init__(self, maxsize=10000, ttl=300):
        """
        Args:
            maxsize: Maximum number of entries.
            ttl: Time-to-live in seconds.
        """
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def get_effective_permissions(self, role_id: str, zone_id: str) -> Optional[Set[str]]:
        """Return cached permission set or None."""
        pass

    def set_effective_permissions(self, role_id: str, zone_id: str, perms: Set[str]) -> None:
        """Store permission set in cache."""
        pass

    def invalidate_role(self, role_id: str, zone_id: Optional[str] = None) -> None:
        """Invalidate all entries for the given role (optionally restricted to one zone)."""
        pass
```

### 5.3 Access Engine (`zrb.engine.access.AccessEngine`)

The main entry point for access decisions.

```python
class AccessEngine:
    def __init__(self, storage: Storage, cache_ttl: int = 300):
        self.storage = storage
        self.resolver = InheritanceResolver(storage)
        self.cache = PermissionCache(ttl=cache_ttl)
        self.constraint_registry = ConstraintRegistry()

    def _get_effective_permissions(self, role_id: str, zone_id: str, mode: AccessMode) -> Set[str]:
        """Internal: get effective permissions with caching."""
        pass

    def decide(
        self,
        user: User,
        operation: Operation,
        zone: Zone,
        mode: AccessMode = AccessMode.INFERENTIAL,
        context: Optional[dict] = None,
    ) -> bool:
        """
        Return True if access is allowed.

        Steps:
        1. If user is not active → False.
        2. Retrieve user’s roles in the zone.
        3. Check if operation is in any effective permission set.
        4. Apply all constraints (negative deny, positive require).
        5. Return True if all checks pass.
        """
        pass
```

---

## 6. Constraints (`zrb.constraints`)

### 6.1 Base Evaluator (`zrb.constraints.base.ConstraintEvaluator`)

```python
class ConstraintEvaluator(ABC):
    @abstractmethod
    def evaluate(
        self,
        constraint: Constraint,
        user: User,
        role: Role,
        zone: Zone,
        operation: Operation,
        context: Optional[Dict] = None
    ) -> bool:
        """
        For negative constraints: return True if the condition is violated (i.e., should deny).
        For positive constraints: return True if the condition is satisfied (i.e., should allow).
        """
        pass
```

### 6.2 Registry (`zrb.constraints.registry.ConstraintRegistry`)

Maps `ConstraintType` to evaluator instances.

```python
class ConstraintRegistry:
    def __init__(self):
        self._evaluators: Dict[ConstraintType, ConstraintEvaluator] = {
            ConstraintType.SOD: SoDEvaluator(),
            ConstraintType.TEMPORAL: TemporalEvaluator(),
            ConstraintType.ATTRIBUTE: AttributeEvaluator(),
            ConstraintType.CONTEXT: ContextEvaluator(),
        }

    def evaluate(self, constraint: Constraint, *args, **kwargs) -> bool:
        """Delegate to the appropriate evaluator."""
        evaluator = self._evaluators.get(constraint.type)
        if evaluator:
            return evaluator.evaluate(constraint, *args, **kwargs)
        return False  # unknown type – ignore (or raise)
```

### 6.3 Provided Evaluators (`zrb.constraints.evaluators`)

- **`SoDEvaluator`**: Checks if the user holds a prohibited role or is the same as the resource creator (self).
- **`TemporalEvaluator`**: Compares current time (from context or system time) with allowed windows.
- **`AttributeEvaluator`**: Compares user attributes (or context attributes) against thresholds using operators (`>`, `<`, `==`, etc.).
- **`ContextEvaluator`**: Matches context keys against expected values.

Each evaluator implements the `evaluate` method with logic appropriate to its type.

---

## 7. Web Integrations

### 7.1 Django Integration (`zrb.web.django`)

Provides middleware and decorators for Django.

#### Middleware: `ZRBDjango`

```python
class ZRBDjango:
    def __init__(self, get_response, engine: AccessEngine = None):
        self.get_response = get_response
        self.engine = engine  # should be configured globally

    def __call__(self, request):
        # Attach zone to request (implement _zone_from_host)
        request.zone = self._zone_from_request(request)
        response = self.get_response(request)
        return response

    def _zone_from_request(self, request):
        """Extract zone from subdomain or header. Must be overridden or configured."""
        host = request.get_host().split(':')[0]
        # custom logic...
        return self.engine.storage.get_zone(zone_id)
```

#### Decorators

```python
def n_rzbac(roles=None, operation=None):
    """Decorator for direct mode (n_rzbac)."""

def i_rzbac(roles=None, operation=None):
    """Decorator for inferential mode (i_rzbac)."""
```

Both decorators:
- Expect `request.user` (Django User) and `request.zone` to be set.
- Convert Django user to ZRB user (using `user.id` as the key).
- Resolve operation if not given (e.g., from `request.resolver_match.url_name`).
- Call `engine.decide()` and return 403 if denied.

### 7.2 Flask Integration (`zrb.web.flask`)

Provides a Flask extension and decorators.

#### Extension: `ZRBFlask`

```python
class ZRBFlask:
    def __init__(self, app=None, engine=None):
        self.engine = engine
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.extensions['zrb'] = self
        # Register before_request to set request.zone
        @app.before_request
        def set_zone():
            request.zone = self._zone_from_request()
```

#### Decorators

Same interface as Django: `@zrb.n_rzbac(...)` and `@zrb.i_rzbac(...)`. They rely on `request.zone` and `flask_login.current_user`.

---

## 8. Command‑Line Interface (`zrb.cli`)

Built with `click`. Provides commands to manage ZRB configuration.

```python
@click.group()
def cli():
    """ZRB Toolkit Command Line Interface"""
    pass

@cli.command()
@click.option('--db', default='sqlite:///zrb.db', help='Database URL')
def init(db):
    """Initialize the database (create tables)."""
    store = SQLAlchemyStore(db)
    store.create_all()

@cli.command()
@click.argument('file')
@click.option('--db', default='sqlite:///zrb.db')
def import_config(file, db):
    """Import configuration from YAML."""
    store = SQLAlchemyStore(db)
    with open(file) as f:
        config = yaml.safe_load(f)
    # ... import logic

@cli.command()
@click.option('--db', default='sqlite:///zrb.db')
def validate(db):
    """Validate the current configuration."""
    store = SQLAlchemyStore(db)
    errors = validate_config(store)
    # output errors

# Additional CRUD commands: zone create, role list, etc.
```

---

## 9. Validation Utilities (`zrb.validation`)

### `zrb.validation.checker.validate_config(store: Storage) -> List[str]`

Performs consistency checks:
- No cycles in zone tree (must be a DAG; but zones form a tree by definition).
- No cycles in intra‑zone role hierarchies.
- All `parent_role_id`, `parent_zone_id`, etc., reference existing entities.
- No conflicting gamma mappings (multiple with same child but different parents).
- Constraint target fields exist and refer to valid objects.
- Returns list of error messages (empty if valid).

---

## 10. Utility Modules

### `zrb.utils.tree`

Functions for tree traversal:

- `get_ancestors(zone_id, storage)`
- `get_descendants(zone_id, storage)`
- `is_descendant(child_id, ancestor_id, storage)`

### `zrb.utils.graph`

Functions for role hierarchy DAG:

- `transitive_closure(role_id, storage)` – returns all junior roles.
- `has_cycle(role_id, storage)` – detects cycles.

---

## 11. Configuration and Deployment

The toolkit expects a ZRB store (database) to be populated with zones, roles, etc. The store can be shared across multiple application instances (if using PostgreSQL, etc.). In Django/Flask, the store is typically a singleton initialized once and reused.

Environment variables:
- `ZRB_DATABASE_URL`: connection string for the ZRB store.

In Django, set `ZRB_DATABASE_URL` in `settings.py` and create the store there. The middleware and decorators use that store.

---

## 12. Extending the Toolkit

### 12.1 Custom Constraint Types

1. Subclass `ConstraintEvaluator`.
2. Implement `evaluate()` with your logic.
3. Register it with the global `ConstraintRegistry` (or a custom registry instance).

### 12.2 Custom Storage Backend

Implement the `Storage` interface using another database (e.g., MongoDB, Redis). The engine only depends on the abstract interface.

### 12.3 Custom Cache Backend

Create a class with the same methods as `PermissionCache` and pass it to `AccessEngine`.

### 12.4 Custom Web Framework Integration

Study the Django/Flask implementations; they follow a common pattern: resolve zone, get user, call `engine.decide()`, and handle denial (HTTP 403).

---

## 13. API Reference (Detailed)

This section provides complete signatures and descriptions for all public classes and methods.

*(Due to length, we include only a representative subset; the full reference would be generated from docstrings.)*

### `zrb.core.models.User`

- `id: str` – Unique identifier (matches auth system).
- `username: str` – Login name.
- `email: str` – Email address.
- `attributes: Dict[str, Any]` – Custom attributes for constraints.
- `is_active: bool` – If False, user is blocked.

### `zrb.engine.access.AccessEngine.decide`

```python
def decide(
    self,
    user: User,
    operation: Operation,
    zone: Zone,
    mode: AccessMode = AccessMode.INFERENTIAL,
    context: Optional[dict] = None
) -> bool
```

**Parameters**:
- `user`: The user requesting access.
- `operation`: The operation being requested.
- `zone`: The zone in which the request occurs.
- `mode`: `INFERENTIAL` (default) applies inheritance; `DIRECT` only checks base permissions.
- `context`: A dictionary with additional information for constraint evaluation (e.g., `{"amount": 15000, "current_time": "14:30"}`).

**Returns**:
- `True` if access is allowed, `False` otherwise.

**Raises**:
- No exceptions; all failures return `False`.

### `zrb.storage.sqlalchemy.SQLAlchemyStore.create_zone`

```python
def create_zone(self, zone: Zone) -> None
```

Inserts a new zone into the database. If a zone with the same ID exists, raises `IntegrityError`.

### `zrb.web.django.i_rzbac`

```python
def i_rzbac(roles: Optional[List[str]] = None, operation: Optional[str] = None) -> Callable
```

Decorator factory. The actual decorator expects a view function. It uses `request.user` and `request.zone`. If `roles` is given, it also checks that the user has one of those roles (in addition to the operation permission). The `operation` can be a string; if omitted, it is inferred from the view name (e.g., `'view_grades'`). The view must be mapped in `urls.py` with a `name=`.

---

## 14. Examples

Each example system (university, hospital, e‑commerce, project management, banking) is provided as a separate Django/Flask application in the `examples/` directory. They demonstrate:

- Defining ZRB config in YAML.
- Loading it via management command.
- Using decorators to protect views.
- Passing context for constraint evaluation.
- Mapping subdomains to zones.

Refer to the example READMEs for step‑by‑step instructions.

---

## 15. Conclusion

The ZRB Python toolkit is a comprehensive, production‑ready implementation of the Zoned Role‑Based framework. Its modular design allows easy extension and integration with existing web frameworks. This specification serves as the definitive guide for developers using or extending the toolkit.