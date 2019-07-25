# File that can be imported to access the Flask app, if serving directly using a WSGI
# application like gunicorn or uWSGI
from nutrition_app.main import make_app
app = make_app().flask_app
