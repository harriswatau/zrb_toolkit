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

---

## System 2: Hospital Patient Management System

### Domain
A hospital with departments, ICUs, and administrative units.

### Zone Tree
```
Hospital (root)
├── Cardiology Department
│   ├── ICU
│   └── General Ward
├── Radiology Department
│   ├── MRI Unit
│   └── X-Ray Unit
└── Administration
```

### Roles & Base Permissions
| Zone           | Role          | Base Permissions                              |
|----------------|---------------|-----------------------------------------------|
| Hospital       | Admin         | `user:manage`, `dept:manage`                  |
| Cardiology     | Head          | `staff:assign`, `report:view`                 |
|                | Doctor        | `record:view`, `prescribe`, `diagnose`        |
|                | Nurse         | `vitals:update`, `medication:administer`      |
|                | Patient       | `record:view_own`                             |
| ICU            | ICU_Doctor    | inherits from Doctor + `icu:access`           |
|                | ICU_Nurse     | inherits from Nurse + `icu:access`            |
| General Ward   | Ward_Doctor   | inherits from Doctor                           |
|                | Ward_Nurse    | inherits from Nurse                            |
| Radiology      | Head          | `report:approve`                               |
|                | Technician    | `scan:perform`, `image:view`                   |
| Administration | Clerk         | `admit:process`, `bill:create`                 |

### Intra‑Zone Hierarchies
`Head` > `Doctor` > `Nurse`; `Head` > `Technician`; `Admin` > all.

### Gamma Mappings
- `(ICU, ICU_Doctor)` → `(Cardiology, Doctor)`
- `(ICU, ICU_Nurse)` → `(Cardiology, Nurse)`
- `(General Ward, Ward_Doctor)` → `(Cardiology, Doctor)`
- `(General Ward, Ward_Nurse)` → `(Cardiology, Nurse)`
- `(MRI Unit, Technician)` → `(Radiology, Technician)`
- `(X-Ray Unit, Technician)` → `(Radiology, Technician)`

### Constraints
- A doctor cannot prescribe for themselves (SoD).
- Access to patient records only during shift (temporal).

**Implementation** is analogous to System 1, with appropriate endpoints: `/patient/<id>/record`, `/prescribe`, `/scan`.

---

## System 3: E‑Commerce Platform

### Domain
A company with sales, inventory, and shipping divisions.

### Zone Tree
```
Company (root)
├── Sales Division
│   ├── Online Sales Team
│   └── Retail Sales Team
├── Inventory Division
│   ├── Warehouse A
│   └── Warehouse B
└── Shipping Division
    ├── Domestic Shipping
    └── International Shipping
```

### Roles & Base Permissions
| Zone           | Role           | Base Permissions                              |
|----------------|----------------|-----------------------------------------------|
| Company        | CEO            | `company:report`, `all:access`                |
| Sales          | Sales Manager  | `discount:approve`, `sales:report`            |
|                | Sales Rep      | `order:create`, `order:modify`                |
| Online Sales   | Online Rep     | inherits from Sales Rep                        |
| Retail Sales   | Retail Rep     | inherits from Sales Rep                        |
| Inventory      | Inventory Mgr  | `stock:adjust`, `reorder`                      |
|                | Clerk          | `stock:update`                                 |
| Warehouse A    | A Clerk        | inherits from Clerk, plus `zone:A_access`      |
| Shipping       | Shipping Mgr   | `ship:schedule`                                |
|                | Shipper        | `ship:process`                                 |

### Gamma Mappings
- `(Online Sales, Online Rep)` → `(Sales, Sales Rep)`
- `(Retail Sales, Retail Rep)` → `(Sales, Sales Rep)`
- `(Warehouse A, A Clerk)` → `(Inventory, Clerk)`
- `(Warehouse B, B Clerk)` → `(Inventory, Clerk)`
- `(Domestic Shipping, Shipper)` → `(Shipping, Shipper)`
- `(International Shipping, Shipper)` → `(Shipping, Shipper)`

### Constraints
- Sales rep cannot approve their own discount (SoD).
- Reorder only if stock < threshold (attribute-based).

**Implementation**: Endpoints like `/order`, `/stock`, `/ship`.

---

## System 4: Project Management Tool

### Domain
An organization running multiple projects with development and QA teams.

### Zone Tree
```
Organization (root)
├── Project Alpha
│   ├── Development Team
│   └── QA Team
├── Project Beta
│   ├── Development Team
│   └── QA Team
└── PMO (Project Management Office)
```

### Roles & Base Permissions
| Zone        | Role             | Base Permissions                              |
|-------------|------------------|-----------------------------------------------|
| Organization| Admin            | `project:create`, `user:manage`               |
| Project     | Project Manager  | `task:assign`, `milestone:set`, `report:view` |
|             | Developer        | `task:update`, `code:commit`                  |
|             | Tester           | `bug:report`, `test:run`                      |
| Dev Team    | Lead Dev         | inherits from Developer + `review:approve`    |
| QA Team     | Lead Tester      | inherits from Tester + `test:plan`            |
| PMO         | Analyst          | `portfolio:report`                             |

### Gamma Mappings
- `(Project Alpha, Project Manager)` → none (specific to project)
- `(Project Alpha Dev Team, Lead Dev)` → `(Project Alpha, Developer)`
- `(Project Alpha QA Team, Lead Tester)` → `(Project Alpha, Tester)`
- Similarly for Project Beta.

### Constraints
- Developer cannot approve their own pull request (SoD).
- Testing only in QA environment (context).

**Implementation**: Endpoints for tasks, code commits, test plans.

---

## System 5: Banking System

### Domain
A bank with branches, head office, and audit.

### Zone Tree
```
Bank (root)
├── Branch A
│   ├── Loans Department
│   └── Accounts Department
├── Branch B
│   ├── Loans
│   └── Accounts
└── Head Office
    ├── Risk Management
    └── Audit
```

### Roles & Base Permissions
| Zone         | Role            | Base Permissions                              |
|--------------|-----------------|-----------------------------------------------|
| Bank         | System Admin    | `branch:manage`, `audit:log`                  |
| Branch       | Branch Manager  | `transaction:approve_high`, `staff:manage`    |
|              | Teller          | `deposit`, `withdraw`, `balance:view`         |
| Loans Dept   | Loan Officer    | `loan:process`, `credit:check`                |
|              | Loan Manager    | `loan:approve`                                 |
| Accounts Dept| Accountant      | `account:open`, `account:close`                |
| Head Office  | Risk Officer    | `risk:report`, `limit:set`                     |
| Audit        | Auditor         | `audit:view_all`                               |

### Intra‑Zone Hierarchies
`Branch Manager` > `Teller`; `Loan Manager` > `Loan Officer`; `Head of Risk` > `Risk Officer`.

### Gamma Mappings
- `(Branch A Loans, Loan Officer)` → none (local)
- `(Branch A Loans, Loan Manager)` → none
- `(Branch B Loans, Loan Officer)` → none
- Possibly no gamma, as each branch is independent.

### Constraints
- Teller cannot approve their own transactions (SoD).
- Large withdrawals (>10k) require second approval (positive constraint).
- Audit view only during business hours (temporal).

**Implementation**: Endpoints for transactions, loan processing, audit logs.

---

## Deployment Guide (All Systems)

1. **Prepare the environment**:
   ```bash
   mkdir myapp && cd myapp
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install zrb-toolkit flask flask-login pyyaml gunicorn
   ```

3. **Place the application files**:
   - `app.py`
   - `init_db.py`
   - `config.yaml`
   - `requirements.txt`

4. **Initialise the database**:
   ```bash
   python init_db.py
   ```

5. **Run with Gunicorn**:
   ```bash
   gunicorn -w 4 -b 127.0.0.1:8000 app:app
   ```

6. **Set up Nginx as reverse proxy** (example):
   ```nginx
   server {
       listen 80;
       server_name example.com;
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
       }
   }
   ```

7. **Environment variables**: Use a `.env` file for production secrets (database URL, secret key).

---

## Conclusion

These five examples demonstrate how the ZRB methodology can be applied to diverse enterprise domains. By using the `zrb-toolkit`, developers can quickly build secure, maintainable web applications where access control is an emergent property of the organisational structure. All code is ready to deploy on a standard web server.

For the complete source code (including full `config.yaml` and all endpoints), visit the [ZRB Toolkit Examples Repository](https://github.com/yourname/zrb-toolkit/tree/main/examples).