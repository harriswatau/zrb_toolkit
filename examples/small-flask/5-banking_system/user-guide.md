
## Deployment Instructions

### Local Development
```bash
# Clone the repository (or create files)
cd banking-system
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python init_db.py
python app.py
# Visit http://127.0.0.1:5000/login/u1 (for Alice)
# Then access endpoints with ?zone=branch_a (or appropriate zone)
```

### Production Deployment with Gunicorn and Nginx

1. Set environment variables:
   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost/banking"
   export SECRET_KEY="your-secret-key"
   ```

2. Run with Gunicorn:
   ```bash
   gunicorn -w 4 -b 127.0.0.1:8000 app:app
   ```

3. Configure Nginx as reverse proxy:
   ```nginx
   server {
       listen 80;
       server_name banking.example.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

4. (Optional) Use systemd to manage Gunicorn.

---

### 6. Testing the System

- **Alice** (Branch Manager of Branch A) can:
  - Approve high-value transactions (`/transaction/approve-high`)
  - Manage staff (`/staff/manage`)
  - Also has teller permissions via hierarchy (deposit, withdraw, view balance)

- **Bob** (Teller and Loan Officer in Branch A) can:
  - Deposit, withdraw, view balance
  - Process loans, check credit
  - Cannot approve high-value transactions (needs manager role)
  - Cannot approve loans (needs loan manager)

- **Carol** (Teller in Branch B) can:
  - Perform teller operations in Branch B only (if zone is set correctly)

- **Dave** (Risk Officer) can:
  - View risk report, set limits

- **Eve** (Auditor) can:
  - View all audit records only during business hours (9am–5pm); outside those hours, access is denied.

---

### 7. Customising Constraints

The constraints are evaluated by passing a `context` dictionary to `engine.decide()`. For example:

- **SoD for teller approving own transaction**: The context includes `creator_id` (the user who created the transaction). The constraint evaluator checks if the current user ID equals `creator_id` and denies if true.
- **Temporal for audit**: The context includes `current_time` (ISO time string). The evaluator checks if it falls within the configured range.
- **Attribute for large withdrawal**: In the `withdraw` endpoint, we check the amount and return a different response if it exceeds 10k. The attribute constraint is not enforced automatically; we use it as an example. A more sophisticated implementation could have a separate operation `withdraw_large` that requires manager approval, and the attribute constraint could be used to decide which operation to invoke.

---

### Conclusion

You now have a fully functional Banking System built with the ZRB methodology. The system enforces fine‑grained access control based on organisational structure, role hierarchies, and constraints. All components are ready for deployment.

The complete source code for this system (and the other examples) is available at the [ZRB Toolkit Examples Repository](https://github.com/yourname/zrb-toolkit/tree/main/examples/banking).