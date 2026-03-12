import os
from flask import Flask, request, jsonify, abort
from flask_login import LoginManager, UserMixin, login_user, current_user, login_required
from zrb.storage.sqlalchemy import SQLAlchemyStore
from zrb.engine.access import AccessEngine
from zrb.web.flask import ZRBFlask
from zrb.core.models import User as ZRBUser

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# Database
db_url = os.environ.get("DATABASE_URL", "sqlite:///ecommerce.db")
store = SQLAlchemyStore(db_url)
engine = AccessEngine(store)
zrb = ZRBFlask(app, engine)

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Simple user mapping (in production, use real user store)
users_db = {
    "u1": {"username": "alice", "zrb_id": "u1"},
    "u2": {"username": "bob", "zrb_id": "u2"},
    "u3": {"username": "carol", "zrb_id": "u3"},
    "u4": {"username": "dave", "zrb_id": "u4"},
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

# ---- Company level ----
@app.route('/company/report')
@login_required
@zrb.i_rzbac(operation='company:report')
def company_report():
    return jsonify({"report": "Company performance report"})

# ---- Sales ----
@app.route('/discount/approve', methods=['POST'])
@login_required
@zrb.n_rzbac(operation='discount:approve')   # direct mode to enforce SoD
def approve_discount():
    data = request.get_json()
    # In real app, check if the order belongs to the same user (SoD)
    # The constraint will handle it if we pass context
    return jsonify({"status": "discount approved"})

@app.route('/sales/report')
@login_required
@zrb.i_rzbac(operation='sales:report')
def sales_report():
    return jsonify({"report": "Sales report"})

@app.route('/order', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='order:create')
def create_order():
    return jsonify({"status": "order created"})

@app.route('/order/<order_id>', methods=['PUT'])
@login_required
@zrb.i_rzbac(operation='order:modify')
def modify_order(order_id):
    return jsonify({"status": f"order {order_id} modified"})

# ---- Inventory ----
@app.route('/stock/adjust', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='stock:adjust')
def adjust_stock():
    return jsonify({"status": "stock adjusted"})

@app.route('/reorder', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='reorder')
def reorder():
    # In real app, check stock level; attribute constraint will be evaluated
    return jsonify({"status": "reorder initiated"})

@app.route('/stock/update', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='stock:update')
def update_stock():
    return jsonify({"status": "stock updated"})

@app.route('/warehouse/A')
@login_required
@zrb.i_rzbac(operation='zone:A_access')
def warehouse_a():
    return "Warehouse A area"

@app.route('/warehouse/B')
@login_required
@zrb.i_rzbac(operation='zone:B_access')
def warehouse_b():
    return "Warehouse B area"

# ---- Shipping ----
@app.route('/ship/schedule', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='ship:schedule')
def schedule_shipment():
    return jsonify({"status": "shipment scheduled"})

@app.route('/ship/process', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='ship:process')
def process_shipment():
    return jsonify({"status": "shipment processed"})

# ---- Health check ----
@app.route('/health')
def health():
    return "OK"

if __name__ == '__main__':
    app.run(debug=True)