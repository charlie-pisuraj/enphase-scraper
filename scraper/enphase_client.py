import os
import base64
import requests
import json
import inspect
from datetime import datetime
from typing import Dict
from prometheus_client import Counter
from app import app

TOKEN_PATH = "scraper/tokens.json"
API_CALL_COUNT = Counter("enphase_call_count", "Total number of calls made to Enphase", ["action", "method"])
LOGGER = app.logger

class Token:
    
    def from_json(self, token_json: Dict):
        self.raw_json = token_json
        self.access = token_json["access_token"]
        self.refresh = token_json["refresh_token"]
        self.created = token_json.get("refreshed_time", 0)
        self.ttl = token_json["expires_in"]

    def from_file(self):
        self.from_json(self.read_stored_token())

    def read_stored_token(self):
        with open(TOKEN_PATH, "r") as f:
            return json.load(f)
    
    def write_stored_token(self):
        with open(TOKEN_PATH, "w") as f:
            json.dump(self.raw_json, f, indent=2)

    @property
    def expired(self):
        created = int(self.created)
        ttl = int(self.ttl)
        now = int(datetime.now().timestamp())
        expired = now >= (created + ttl)
        LOGGER.info(f"Token Expired: {expired}")
        return expired


class EnphaseClient:
    def __init__(self, api_key, client_id, client_secret, system_auth_code):
        self.enphase_api = "api.enphaseenergy.com"
        self.api_key = api_key
        self.client_id = client_id
        self.client_secret = client_secret
        self.system_auth_code = system_auth_code
        self.token = Token()
        self.get_access_token()
        if self.token.expired:
            self.get_refresh_token()

    def base64_encode(self, input_str) -> str:
        input_string_bytes = input_str.encode("ascii")
        base64_bytes = base64.b64encode(input_string_bytes)
        base64_string = base64_bytes.decode("ascii")
        return base64_string
    
    def get_request(self, path, headers) -> Dict:
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        API_CALL_COUNT.labels(action=calframe[1][3], method="GET").inc()
        url = f"https://{self.enphase_api}{path}"
        resp = requests.get(url, headers=headers)
        return resp

    def post_request(self, path, headers) -> Dict:
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        API_CALL_COUNT.labels(action=calframe[1][3], method="POST").inc()
        url = f"https://{self.enphase_api}{path}"
        resp = requests.post(url, headers=headers)
        return resp

    def auth_bearer_header(self, token) -> Dict:
        return {
            "Authorization" : f"Bearer {token}"
        }

    def get_access_token(self):
        if os.path.isfile(TOKEN_PATH):
            LOGGER.info("Getting Token from local cache")
            self.token.from_file()
            return

        LOGGER.info("Getting Token from Enphase")
        token = self.base64_encode(f"{self.client_id}:{self.client_secret}")
        headers = {
            "Authorization" : f"Basic {token}"
        }
        path = f"/oauth/token?grant_type=authorization_code&redirect_uri=https://api.enphaseenergy.com/oauth/redirect_uri&code={self.system_auth_code}"
        request_time = datetime.now()
        resp = self.post_request(path, headers)
        if resp.status_code != 200:
            raise(resp.content)
        data = resp.json()
        refreshed_time = request_time + resp.elapsed
        data["refreshed_time"] = int(refreshed_time.timestamp())
        self.token.from_json(data)
        self.token.write_stored_token()

    def get_refresh_token(self):
        LOGGER.info("Refreshing Token")
        token = self.base64_encode(f"{self.client_id}:{self.client_secret}")
        headers = {
            "Authorization" : f"Basic {token}"
        }
        path = f"/oauth/token?grant_type=refresh_token&refresh_token={self.token.refresh}"
        request_time = datetime.now()
        resp = self.post_request(path, headers)
        if resp.status_code != 200:
            raise(resp.content)
        data = resp.json()
        refreshed_time = request_time + resp.elapsed
        data["refreshed_time"] = int(refreshed_time.timestamp())
        self.token.from_json(data)
        self.token.write_stored_token()

    def get_system_info(self):
        path = f"/api/v4/systems?key={self.api_key}"
        headers = self.auth_bearer_header(self.token.access)
        resp = self.get_request(path, headers)
        return resp.json()["systems"][0]

    def get_system_production(self, system_id, start_date, end_date=None):
        path = f"/api/v4/systems/{system_id}/telemetry/production_micro?key={self.api_key}"
        path = self.add_param(path, "granularity", "day")
        path = self.add_param(path, "start_date", start_date)
        if end_date is not None:
            path = self.add_param(path, "end_date", end_date)

        headers = self.auth_bearer_header(self.token.access)
        resp = self.get_request(path, headers)
        return resp.json()

    def add_param(self, url, param_name, param_val):
        return f"{url}&{param_name}={param_val}"