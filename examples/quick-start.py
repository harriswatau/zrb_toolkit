from zrb import ZRB
from zrb.storage.sqlalchemy import SQLAlchemyStore
from zrb.engine import AccessEngine

# Set up storage
store = SQLAlchemyStore("sqlite:///zrb.db")
store.create_all()

# Create engine
engine = AccessEngine(store)

# Use in your web app (Flask example)
from flask import Flask
from zrb.web.flask import ZRBFlask

app = Flask(__name__)
zrb = ZRBFlask(app, engine)

@app.route('/grade')
@zrb.i_rzbac(operation='grade:view')
def view_grades():
    return "Grades"