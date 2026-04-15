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
db_url = os.environ.get("DATABASE_URL", "sqlite:///hospital.db")
store = SQLAlchemyStore(db_url)
engine = AccessEngine(store)
zrb = ZRBFlask(app, engine)

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Simple in-memory user store for demonstration
# In production, use a real user database and synchronise with ZRB users.
class FlaskUser(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# Mapping from Flask user id to ZRB user id (same in our case)
users_db = {
    "u1": {"username": "alice", "zrb_id": "u1"},
    "u2": {"username": "bob", "zrb_id": "u2"},
    "u3": {"username": "charlie", "zrb_id": "u3"},
}

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

# Helper to get current ZRB user
def current_zrb_user():
    if not current_user.is_authenticated:
        return None
    return store.get_user(current_user.id)

# ---- Patient Records ----
@app.route('/patient/<patient_id>/record')
@login_required
@zrb.i_rzbac(operation='record:view')   # doctors and heads can view any record
def view_patient_record(patient_id):
    # In real app, fetch record from DB
    return jsonify({"patient_id": patient_id, "record": "Sample record"})

@app.route('/patient/<patient_id>/record/own')
@login_required
@zrb.i_rzbac(operation='record:view_own')   # patients can view their own
def view_own_record(patient_id):
    # Ensure the patient_id matches current user? For demo we skip.
    return jsonify({"patient_id": patient_id, "record": "Your record"})

# ---- Treatment ----
@app.route('/prescribe', methods=['POST'])
@login_required
@zrb.n_rzbac(operation='prescribe')   # direct mode to enforce SoD
def prescribe():
    data = request.get_json()
    # In real app, create prescription
    return jsonify({"status": "prescribed"})

@app.route('/diagnose', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='diagnose')
def diagnose():
    return jsonify({"status": "diagnosed"})

# ---- Nursing ----
@app.route('/vitals', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='vitals:update')
def update_vitals():
    return jsonify({"status": "vitals updated"})

@app.route('/medication', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='medication:administer')
def administer_medication():
    return jsonify({"status": "medication administered"})

# ---- ICU specific ----
@app.route('/icu/access')
@login_required
@zrb.i_rzbac(operation='icu:access')
def icu_access():
    return "ICU area"

# ---- Radiology ----
@app.route('/scan', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='scan:perform')
def perform_scan():
    return jsonify({"status": "scan performed"})

@app.route('/image/<image_id>')
@login_required
@zrb.i_rzbac(operation='image:view')
def view_image(image_id):
    return jsonify({"image_id": image_id, "url": f"/images/{image_id}"})

@app.route('/report/approve', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='report:approve')
def approve_report():
    return jsonify({"status": "report approved"})

# ---- Administration ----
@app.route('/admit', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='admit:process')
def admit_patient():
    return jsonify({"status": "patient admitted"})

@app.route('/bill', methods=['GET'])
@login_required
@zrb.i_rzbac(operation='bill:create')
def create_bill():
    return jsonify({"bill": "sample bill"})

# ---- Management ----
@app.route('/staff/assign', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='staff:assign')
def assign_staff():
    return jsonify({"status": "staff assigned"})

@app.route('/report/view')
@login_required
@zrb.i_rzbac(operation='report:view')
def view_report():
    return jsonify({"report": "departmental report"})

# ---- Admin ----
@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
@zrb.i_rzbac(operation='user:manage')
def manage_users():
    if request.method == 'POST':
        # create user
        return jsonify({"status": "user created"})
    return jsonify({"users": list(users_db.values())})

@app.route('/admin/departments', methods=['GET', 'POST'])
@login_required
@zrb.i_rzbac(operation='dept:manage')
def manage_departments():
    return jsonify({"departments": ["Cardiology", "Radiology", "Admin"]})

# ---- Health check ----
@app.route('/health')
def health():
    return "OK"

if __name__ == '__main__':
    app.run(debug=True)