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

## 4. Project Management Tool

### 4.1 Zone Tree
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

### 4.2 Roles and Permissions
| Zone        | Role             | Base Permissions                              |
|-------------|------------------|-----------------------------------------------|
| Organization| Admin            | `project:create`, `user:manage`               |
| Project     | Project Manager  | `task:assign`, `milestone:set`, `report:view` |
|             | Developer        | `task:update`, `code:commit`                  |
|             | Tester           | `bug:report`, `test:run`                      |
| Dev Team    | Lead Dev         | inherits from Developer + `review:approve`    |
| QA Team     | Lead Tester      | inherits from Tester + `test:plan`            |
| PMO         | Analyst          | `portfolio:report`                             |

**Gamma**: Project Manager in each project inherits from PMO Analyst? Not needed.  
**Constraints**: Developer cannot approve their own pull request (SoD). Testing only in QA environment (context).
