from app import app
from flask import request
# from prometheus_client import Counter
from scraper.systems import System
system = System(
    api_key=app.config.get("API_KEY"),
    client_id=app.config.get("CLIENT_ID"),
    client_secret=app.config.get("CLIENT_SECRET"),
    system_auth_code=app.config.get("SYSTEM_CODE")
)

@app.route('/')
def systems():
    return system.get_id()

@app.route('/production', methods=["GET"])
def production():
    args = request.args.to_dict()
    return system.get_production(args.get("date", None))