
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

## 5. Banking System

### 5.1 Zone Tree
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

### 5.2 Roles and Permissions
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

**Intra‑zone**: Branch Manager > Teller; Loan Manager > Loan Officer.  
**Gamma**: Loan Officer at a branch inherits from Loan Officer at Head Office? Possibly.  
**Constraints**: Teller cannot approve their own transactions (SoD). Large withdrawals require second approval (positive constraint).

---

## Deployment Notes

Each application can be deployed using:
```
pip install -r requirements.txt
python init_db.py   # create and populate DB
gunicorn -w 4 app:app
```

Configure Nginx as reverse proxy, and set environment variables for production (database URL, secret key).

These examples demonstrate how the ZRB methodology cleanly separates organizational structure from application logic, and how the `zrb-toolkit` makes it easy to enforce fine‑grained, context‑aware access control.

*The full source code for each system (including complete `init_db.py` and `app.py` with all endpoints) is available on the [ZRB Toolkit GitHub repository](https://github.com/yourname/zrb-toolkit/tree/main/examples).*