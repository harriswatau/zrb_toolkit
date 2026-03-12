from flask import Flask
from flask_login import LoginManager, UserMixin, login_user
from zrb.storage.memory import MemoryStore
from zrb.core.models import User as ZUser, Zone, Operation, Role
from zrb.engine.access import AccessEngine
from zrb.web.flask import ZRBFlask

# Setup store and seed minimal data
store = MemoryStore()
store.add_zone(Zone(id="root", name="Root"))
store.add_operation(Operation(id="grade:view", app_name="university", name="view"))
store.add_role(Role(id="faculty_reader", zone_id="root", name="FacultyReader", base_permissions={"grade:view"}))

# Flask app
app = Flask(__name__)
app.secret_key = 'secret'

# Engine + extension
engine = AccessEngine(store)
zrb = ZRBFlask(app, engine)

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    return User(user_id, f"user{user_id}")

@app.route("/")
def index():
    return (
        "<h3>ZRB University Demo</h3>"
        '<p><a href="/login/1">Login as user 1</a></p>'
        '<p>Then visit <a href="/grade">/grade</a></p>'
    )

@app.route('/login/<user_id>')
def login(user_id):
    u = User(user_id, f"user{user_id}")
    login_user(u)
    zu = ZUser(id=str(user_id), username=f"user{user_id}", email="")
    store.add_user(zu)
    store.assign_user_to_role(zu.id, "root", "faculty_reader")
    return "Logged in"

@app.route('/grade')
@zrb.i_rzbac(operation='grade:view')
def view_grades():
    return "Grades page"

if __name__ == '__main__':
    app.run()
