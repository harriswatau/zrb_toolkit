from flask import Flask, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, current_user
from zrb import ZRB
from zrb.storage.sqlalchemy import SQLAlchemyStore
from zrb.engine.access import AccessEngine
from zrb.web.flask import ZRBFlask

app = Flask(__name__)
app.secret_key = "dev-key"

# Setup ZRB
store = SQLAlchemyStore("sqlite:///university.db")
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
    # In real app, fetch from DB; here dummy
    return User(user_id, f"user{user_id}")

@app.route('/login/<user_id>')
def login(user_id):
    user = User(user_id, f"user{user_id}")
    login_user(user)
    return "Logged in"

# Example protected endpoints
@app.route('/grades')
@zrb.i_rzbac(operation='grade:view')
def view_grades():
    return "Your grades"

@app.route('/grades/submit', methods=['POST'])
@zrb.n_rzbac(operation='grade:submit')   # direct mode, no inheritance
def submit_grades():
    return "Grades submitted"

@app.route('/course/enroll', methods=['POST'])
@zrb.i_rzbac(operation='course:enroll')
def enroll():
    return "Enrolled"

if __name__ == '__main__':
    app.run(debug=True)