import os
from flask import Flask, request, jsonify, abort
from flask_login import LoginManager, UserMixin, login_user, current_user, login_required
from zrb.storage.sqlalchemy import SQLAlchemyStore
from zrb.engine.access import AccessEngine
from zrb.web.flask import ZRBFlask
from zrb.core.models import User as ZRBUser
import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# Database
db_url = os.environ.get("DATABASE_URL", "sqlite:///banking.db")
store = SQLAlchemyStore(db_url)
engine = AccessEngine(store)
zrb = ZRBFlask(app, engine)  # for zone resolution, etc.

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Simple user mapping (in production, use real user store)
users_db = {
    "u1": {"username": "alice", "zrb_id": "u1"},
    "u2": {"username": "bob", "zrb_id": "u2"},
    "u3": {"username": "carol", "zrb_id": "u3"},
    "u4": {"username": "dave", "zrb_id": "u4"},
    "u5": {"username": "eve", "zrb_id": "u5"},
}

class FlaskUser(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    if user_id in users_db:
        return FlaskUser(user_id, users_db[user_id]["username"])
    return None

@app.route('/login/<user_id>')
def login(user_id):
    if user_id not in users_db:
        abort(404)
    user = FlaskUser(user_id, users_db[user_id]["username"])
    login_user(user)
    return f"Logged in as {user.username}"

def current_zrb_user():
    if not current_user.is_authenticated:
        return None
    return store.get_user(current_user.id)

# Helper to get zone from request (subdomain or header)
def get_current_zone():
    # In a real app, you'd map subdomains (branch_a.bank.com) to zone IDs
    # For demo, we'll use a query parameter or default to bank
    zone_id = request.args.get('zone', 'bank')
    return store.get_zone(zone_id)

# ---- Bank-level admin ----
@app.route('/admin/branch', methods=['POST'])
@login_required
def manage_branch():
    # Use direct engine call to pass context if needed
    user = current_zrb_user()
    op = store.get_operation('branch:manage')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential'):
        abort(403)
    return jsonify({"status": "branch managed"})

@app.route('/admin/audit/log')
@login_required
def view_audit_log():
    user = current_zrb_user()
    op = store.get_operation('audit:log')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential'):
        abort(403)
    return jsonify({"log": "sample audit log"})

# ---- Branch operations ----
@app.route('/transaction/approve-high', methods=['POST'])
@login_required
def approve_high_transaction():
    data = request.get_json()
    context = {'creator_id': data.get('creator_id')}  # for SoD constraint
    user = current_zrb_user()
    op = store.get_operation('transaction:approve_high')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential', context=context):
        abort(403)
    return jsonify({"status": "high-value transaction approved"})

@app.route('/staff/manage', methods=['POST'])
@login_required
def manage_staff():
    user = current_zrb_user()
    op = store.get_operation('staff:manage')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential'):
        abort(403)
    return jsonify({"status": "staff managed"})

# ---- Teller operations ----
@app.route('/deposit', methods=['POST'])
@login_required
def deposit():
    data = request.get_json()
    # We could include amount in context if needed for constraints
    context = {'amount': data.get('amount', 0)}
    user = current_zrb_user()
    op = store.get_operation('deposit')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential', context=context):
        abort(403)
    return jsonify({"status": "deposit successful"})

@app.route('/withdraw', methods=['POST'])
@login_required
def withdraw():
    data = request.get_json()
    context = {'amount': data.get('amount', 0), 'creator_id': current_user.id}
    user = current_zrb_user()
    op = store.get_operation('withdraw')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential', context=context):
        abort(403)
    # If amount > 10000, we might require second approval (handled in application logic)
    amount = data.get('amount', 0)
    if amount > 10000:
        # In a real system, you'd create a pending transaction and require manager approval
        return jsonify({"status": "withdrawal requires manager approval"})
    return jsonify({"status": "withdrawal successful"})

@app.route('/balance/<account_id>')
@login_required
def view_balance(account_id):
    user = current_zrb_user()
    op = store.get_operation('balance:view')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential'):
        abort(403)
    return jsonify({"account": account_id, "balance": 1234.56})

# ---- Loans ----
@app.route('/loan/process', methods=['POST'])
@login_required
def process_loan():
    user = current_zrb_user()
    op = store.get_operation('loan:process')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential'):
        abort(403)
    return jsonify({"status": "loan processed"})

@app.route('/loan/credit-check/<customer_id>')
@login_required
def credit_check(customer_id):
    user = current_zrb_user()
    op = store.get_operation('credit:check')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential'):
        abort(403)
    return jsonify({"customer": customer_id, "credit_score": 720})

@app.route('/loan/approve', methods=['POST'])
@login_required
def approve_loan():
    user = current_zrb_user()
    op = store.get_operation('loan:approve')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential'):
        abort(403)
    return jsonify({"status": "loan approved"})

# ---- Accounts ----
@app.route('/account/open', methods=['POST'])
@login_required
def open_account():
    user = current_zrb_user()
    op = store.get_operation('account:open')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential'):
        abort(403)
    return jsonify({"status": "account opened"})

@app.route('/account/close', methods=['POST'])
@login_required
def close_account():
    user = current_zrb_user()
    op = store.get_operation('account:close')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential'):
        abort(403)
    return jsonify({"status": "account closed"})

# ---- Risk ----
@app.route('/risk/report')
@login_required
def risk_report():
    user = current_zrb_user()
    op = store.get_operation('risk:report')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential'):
        abort(403)
    return jsonify({"report": "risk report"})

@app.route('/risk/limit', methods=['POST'])
@login_required
def set_limit():
    user = current_zrb_user()
    op = store.get_operation('limit:set')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential'):
        abort(403)
    return jsonify({"status": "limit set"})

# ---- Audit ----
@app.route('/audit/all')
@login_required
def view_all_audit():
    # Temporal constraint will be checked with current time
    context = {'current_time': datetime.datetime.now().time().isoformat()}
    user = current_zrb_user()
    op = store.get_operation('audit:view_all')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential', context=context):
        abort(403)
    return jsonify({"audit": "all audit records"})

# ---- Health check ----
@app.route('/health')
def health():
    return "OK"

if __name__ == '__main__':
    app.run(debug=True)