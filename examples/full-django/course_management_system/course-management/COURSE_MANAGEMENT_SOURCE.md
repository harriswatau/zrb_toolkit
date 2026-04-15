We will design five realistic enterprise information systems using the ZRB methodology and implement them as executable web applications with the Python `zrb-toolkit`. Each system includes:

- A **zone tree** mirroring the organization.
- **Roles**, **base permissions**, **intra‑zone hierarchies**, and **inter‑zone gamma mappings**.
- **Constraints** (separation of duty, temporal, attribute).
- A **Flask web application** with protected endpoints.
- A **database initialisation script** to load the ZRB configuration.
- **Deployment instructions** (Gunicorn + Nginx).

The full source code for all five systems is available at:  
[https://github.com/yourname/zrb-toolkit/tree/main/examples](https://github.com/yourname/zrb-toolkit/tree/main/examples)

---

## Prerequisites

1. Install Python 3.9+.
2. Install the `zrb-toolkit` (either from source or via `pip install zrb-toolkit` once published).
3. Install additional dependencies: `flask`, `flask-login`, `pyyaml`, `gunicorn`.

---

## System 1: University Course Management System

### Domain
A university with faculties, departments, students, professors, and teaching assistants.

### Zone Tree
```
University (root)
├── Faculty of Engineering
│   ├── Computer Science
│   └── Electrical Engineering
└── Faculty of Arts
    ├── History
    └── Philosophy
```

### Roles & Base Permissions
| Zone               | Role         | Base Permissions                         |
|--------------------|--------------|------------------------------------------|
| University         | Admin        | `user:manage`, `zone:manage`             |
| Faculty of Eng.    | Dean         | `course:create`, `faculty:report`        |
|                    | Professor    | `grade:submit`, `course:view`            |
|                    | Student      | `grade:view`, `course:enroll`            |
|                    | TA           | `grade:enter`                            |
| CS Dept            | DeptHead     | `schedule:manage`, `prof:assign`         |
|                    | Professor    | (inherits from Faculty Professor)        |
|                    | Student      | (inherits from Faculty Student)          |
|                    | TA           | (inherits from Faculty TA)               |
| (Other depts similar) | ...        | ...                                      |

### Intra‑Zone Hierarchy (within each zone)
`Admin` > `Dean` > `DeptHead` > `Professor` > `TA` > `Student`

### Gamma Mappings
- `(CS Dept, DeptHead)` → `(Faculty of Eng., Dean)`
- `(CS Dept, Professor)` → `(Faculty of Eng., Professor)`
- (Similar for other roles and departments)

### Constraints
- A student cannot be a TA in the same course (SoD).
- Grade submission only allowed during exam period (temporal).

### Implementation (Key Files)

**`config.yaml`** (partial – see full version in repository)
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
...

roles:
  - id: admin
    zone_id: root
    name: Admin
    base_permissions: ["user:manage", "zone:manage"]
  - id: dean_eng
    zone_id: eng
    name: Dean
    base_permissions: ["course:create", "faculty:report"]
  - id: prof_eng
    zone_id: eng
    name: Professor
    base_permissions: ["grade:submit", "course:view"]
  - id: student_eng
    zone_id: eng
    name: Student
    base_permissions: ["grade:view", "course:enroll"]
  - id: ta_eng
    zone_id: eng
    name: TA
    base_permissions: ["grade:enter"]
  - id: head_cs
    zone_id: cs
    name: DeptHead
    base_permissions: ["schedule:manage", "prof:assign"]
    parent_role_id: prof_cs
  - id: prof_cs
    zone_id: cs
    name: Professor
    base_permissions: []
  ...

gamma_mappings:
  - child_zone_id: cs
    child_role_id: head_cs
    parent_zone_id: eng
    parent_role_id: dean_eng
  ...

constraints:
  - id: sod_student_ta
    type: separation_of_duty
    target: { user_id: "*", operation_id: "grade:enter" }
    condition: { cannot_have_role: "student" }
    is_negative: true
  - id: temporal_grade_submit
    type: temporal
    target: { operation_id: "grade:submit" }
    condition: { time_range: ["2025-05-01T00:00", "2025-06-15T23:59"] }
    is_negative: false
```

**`init_db.py`**
```python
import yaml
from zrb.storage.sqlalchemy import SQLAlchemyStore

def init_db():
    store = SQLAlchemyStore("sqlite:///university.db")
    store.create_all()
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    # Bulk create methods (simplified)
    for z in config["zones"]:
        store.create_zone(z)
    for r in config["roles"]:
        store.create_role(r)
    for o in config["operations"]:
        store.create_operation(o)
    for g in config["gamma_mappings"]:
        store.create_gamma_mapping(g)
    for c in config["constraints"]:
        store.create_constraint(c)
    print("Database initialised.")

if __name__ == "__main__":
    init_db()
```

**`app.py`**
```python
from flask import Flask
from flask_login import LoginManager, UserMixin, login_user
from zrb.storage.sqlalchemy import SQLAlchemyStore
from zrb.engine.access import AccessEngine
from zrb.web.flask import ZRBFlask

app = Flask(__name__)
app.secret_key = "dev-key"

store = SQLAlchemyStore("sqlite:///university.db")
engine = AccessEngine(store)
zrb = ZRBFlask(app, engine)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    # In production, fetch from your user store
    return User(user_id, f"user{user_id}")

@app.route('/login/<user_id>')
def login(user_id):
    user = User(user_id, f"user{user_id}")
    login_user(user)
    return "Logged in"

@app.route('/grades')
@zrb.i_rzbac(operation='grade:view')
def view_grades():
    return "Your grades"

@app.route('/grades/submit', methods=['POST'])
@zrb.n_rzbac(operation='grade:submit')
def submit_grades():
    return "Grades submitted"

@app.route('/course/enroll', methods=['POST'])
@zrb.i_rzbac(operation='course:enroll')
def enroll():
    return "Enrolled"

if __name__ == '__main__':
    app.run()
```

**Run**:
```bash
pip install -r requirements.txt
python init_db.py
gunicorn -w 4 app:app
```
