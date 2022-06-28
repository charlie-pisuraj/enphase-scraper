from config import CLIENT_SECRET
from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import make_wsgi_app

# Create my app
app = Flask(__name__)

app.config.from_object('config')

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

from app import routes