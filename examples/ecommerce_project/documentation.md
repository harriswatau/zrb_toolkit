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

## 3. E‑Commerce Platform

### 3.1 Zone Tree
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

### 3.2 Roles and Permissions
| Zone           | Role           | Base Permissions                              |
|----------------|----------------|-----------------------------------------------|
| Company        | CEO            | `company:report`, `all:access` (superuser)    |
| Sales          | Sales Manager  | `discount:approve`, `sales:report`            |
|                | Sales Rep      | `order:create`, `order:modify`                |
| Online Sales   | Online Rep     | inherits from Sales Rep                        |
| Retail Sales   | Retail Rep     | inherits from Sales Rep                        |
| Inventory      | Inventory Mgr  | `stock:adjust`, `reorder`                      |
|                | Clerk          | `stock:update`                                 |
| Warehouse A    | A Clerk        | inherits from Clerk, plus `zone:A_access`      |
| Shipping       | Shipping Mgr   | `ship:schedule`                                |
|                | Shipper        | `ship:process`                                 |

**Constraints**: Sales rep cannot approve their own discount (SoD). Reorder only if stock < threshold (attribute).

---