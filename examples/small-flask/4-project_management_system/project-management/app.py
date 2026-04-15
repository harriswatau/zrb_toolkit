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
db_url = os.environ.get("DATABASE_URL", "sqlite:///project_management.db")
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
    # In a real app, you'd map subdomains to zone IDs
    # For demo, we'll use a query parameter or default to org
    zone_id = request.args.get('zone', 'org')
    return store.get_zone(zone_id)

# ---- Organization level ----
@app.route('/project', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='project:create')
def create_project():
    return jsonify({"status": "project created"})

@app.route('/users', methods=['GET', 'POST'])
@login_required
@zrb.i_rzbac(operation='user:manage')
def manage_users():
    if request.method == 'POST':
        return jsonify({"status": "user created"})
    return jsonify({"users": list(users_db.values())})

# ---- Project management (tasks, milestones, reports) ----
@app.route('/task/assign', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='task:assign')
def assign_task():
    return jsonify({"status": "task assigned"})

@app.route('/milestone', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='milestone:set')
def set_milestone():
    return jsonify({"status": "milestone set"})

@app.route('/report')
@login_required
@zrb.i_rzbac(operation='report:view')
def view_report():
    return jsonify({"report": "Project progress report"})

# ---- Development ----
@app.route('/task/update', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='task:update')
def update_task():
    return jsonify({"status": "task updated"})

@app.route('/code/commit', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='code:commit')
def commit_code():
    data = request.get_json()
    # In real app, you'd store commit info
    return jsonify({"status": "code committed", "commit_id": "abc123"})

@app.route('/review/approve', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='review:approve')
def approve_review():
    data = request.get_json()
    # SoD constraint will be evaluated; we need to pass context with author_id
    # For demonstration, we'll assume context is passed via request JSON
    context = {'author_id': data.get('author_id')}
    # The decorator doesn't currently accept context; we would need to extend it.
    # For now, we'll just return success; the engine would check if we passed context.
    return jsonify({"status": "review approved"})

# ---- QA ----
@app.route('/bug/report', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='bug:report')
def report_bug():
    return jsonify({"status": "bug reported"})

@app.route('/test/run', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='test:run')
def run_tests():
    # Context constraint expects environment=qa
    # We can pass context via request JSON
    data = request.get_json()
    context = {'environment': data.get('environment', 'dev')}
    # Again, decorator would need to accept context.
    return jsonify({"status": "tests run"})

@app.route('/test/plan', methods=['POST'])
@login_required
@zrb.i_rzbac(operation='test:plan')
def plan_tests():
    return jsonify({"status": "test plan created"})

# ---- PMO ----
@app.route('/portfolio/report')
@login_required
@zrb.i_rzbac(operation='portfolio:report')
def portfolio_report():
    return jsonify({"report": "Portfolio overview"})

@app.route('/review/approve', methods=['POST'])
@login_required
def approve_review():
    data = request.get_json()
    context = {'author_id': data.get('author_id')}
    user = current_zrb_user()
    op = store.get_operation('review:approve')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential', context=context):
        abort(403)
    return jsonify({"status": "review approved"})

@app.route('/test/run', methods=['POST'])
@login_required
def run_tests():
    data = request.get_json()
    context = {'environment': data.get('environment', 'dev')}
    user = current_zrb_user()
    op = store.get_operation('test:run')
    zone = get_current_zone()
    if not engine.decide(user, op, zone, mode='inferential', context=context):
        abort(403)
    return jsonify({"status": "tests run"})

# ---- Health check ----
@app.route('/health')
def health():
    return "OK"

if __name__ == '__main__':
    app.run(debug=True)