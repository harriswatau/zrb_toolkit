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

## 2. Hospital Patient Management System

### 2.1 Zone Tree
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

### 2.2 Roles and Permissions
| Zone           | Role        | Base Permissions                              |
|----------------|-------------|-----------------------------------------------|
| Hospital       | Admin       | `user:manage`, `dept:manage`                  |
| Cardiology     | Head        | `staff:assign`, `report:view`                 |
|                | Doctor      | `record:view`, `prescribe`, `diagnose`        |
|                | Nurse       | `vitals:update`, `medication:administer`      |
|                | Patient     | `record:view_own`                             |
| ICU            | ICU_Doctor  | inherits from Cardiology Doctor + `icu:access`|
|                | ICU_Nurse   | inherits from Nurse + `icu:access`            |
| General Ward   | Ward_Doctor | inherits from Doctor                           |
|                | Ward_Nurse  | inherits from Nurse                            |
| Radiology      | Head        | `report:approve`                               |
|                | Technician  | `scan:perform`, `image:view`                   |
| Administration | Clerk       | `admit:process`, `bill:create`                 |

**Intra‑zone hierarchies**: `Head` > `Doctor` > `Nurse`; `Head` > `Technician`.  
**Gamma mappings**: Unit roles inherit from parent department roles.  
**Constraints**: A doctor cannot prescribe for themselves (SoD); access to patient records only during shift (temporal).

Implementation similar to University system, adapted.
