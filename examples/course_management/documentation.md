
Like all EIS modelled in ZRB, this system includes:

- A **zone tree** mirroring the organizational structure.
- **Roles** with base permissions.
- **Intra‑zone role hierarchies** (where applicable).
- **Inter‑zone gamma mappings** (where cross‑zone inheritance is needed).
- **Constraints** to enforce separation of duty or temporal rules.
- A **Flask web application** using the `zrb-toolkit` to enforce access control.
- A **database initialisation script** to load the ZRB configuration.

This application is ready to run locally or deploy on a web server (e.g., with Gunicorn + Nginx). The code assumes the `zrb-toolkit` is installed; you can install it via `pip install zrb-toolkit` after we release it, or use the provided source.

---

This application includes the following files:

**config.yaml** (ZRB configuration dump):


**init_db.py**:


**app.py** – main Flask application:


**requirements.txt**:
```
Flask>=2.0
Flask-Login>=0.5
zrb-toolkit>=0.1.0
PyYAML>=6.0
```

---

## 1. University Course Management System

### 1.1 Zone Tree
```
University (root)
├── Faculty of Engineering
│   ├── Department of Computer Science
│   └── Department of Electrical Engineering
└── Faculty of Arts
    ├── Department of History
    └── Department of Philosophy
```

### 1.2 Roles and Base Permissions
| Zone               | Role                | Base Permissions (operations)                               |
|--------------------|---------------------|-------------------------------------------------------------|
| University         | Admin               | `user:manage`, `zone:manage`                                |
| Faculty of Eng.    | Dean                | `course:create`, `faculty:report`                           |
|                    | Professor           | `grade:submit`, `course:view`                               |
|                    | Student             | `grade:view`, `course:enroll`                               |
|                    | TA                  | `grade:enter` (assist)                                      |
| CS Dept            | DeptHead            | `schedule:manage`, `prof:assign`                            |
|                    | Professor           | (inherits from faculty professor)                           |
|                    | Student             | (inherits from faculty student)                             |
|                    | TA                  | (inherits from faculty TA)                                  |
| … other depts similar                                                 |

**Intra‑zone hierarchy** (within each zone):  
`Admin` > `Dean` > `DeptHead` > `Professor` > `TA` > `Student` (senior roles inherit permissions of juniors).

**Gamma mappings**:
- `(CS Dept, DeptHead)` inherits from `(Faculty of Eng., Dean)` – department head gets dean’s permissions.
- `(CS Dept, Professor)` inherits from `(Faculty of Eng., Professor)`.

**Constraints**:
- A student cannot be a TA in the same course (SoD).
- Grade submission only allowed during exam period (temporal).

### 1.3 Implementation (Flask)

**Directory structure:**
```
university/
├── app.py
├── init_db.py
├── requirements.txt
└── config.yaml
```