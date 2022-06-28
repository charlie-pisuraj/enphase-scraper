from scraper.enphase_client import EnphaseClient
from scraper.db import DBClient
from datetime import datetime, timedelta
import pytz

class System:
    def __init__(self, api_key, client_id, client_secret, system_auth_code):
        self.enphase = EnphaseClient(api_key, client_id, client_secret, system_auth_code)
        system_info = self.enphase.get_system_info()
        self.update_info(system_info)
        self.db = DBClient()
        self.db.create_production_table()

    def update_info(self, data):
        self.state = data["address"]["state"]
        self.country = data["address"]["country"]
        self.postal_code = data["address"]["postal_code"]
        self.timezone = data["timezone"]
        self.system_id = data["system_id"]

    def get_production(self, start_date=None):
        today = datetime.now()
        start_dt = today.date()
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        start_date_str = start_dt.strftime('%Y-%m-%d')

        end_dt = (start_dt + timedelta(days=1)).date()
        end_date_str = end_dt.strftime('%Y-%m-%d')
        if end_dt > today.date():
            end_date_str = None

        data = self.enphase.get_system_production(
            self.system_id,
            start_date_str,
            end_date_str
        )
        self.store_production_data(data)
        return data

    def store_production_data(self, data):
        rows = []
        for item in data["intervals"]:
            dt = datetime.fromtimestamp(item["end_at"], pytz.timezone(self.timezone))
            rows.append(
                {
                    'devices_reporting': item["devices_reporting"],
                    'power': item["powr"],
                    'energy': item["enwh"],
                    'system_id': self.system_id,
                    'timestamp': dt,
                    'production_date': dt.date()
                }
            )
        self.db.insert_production(rows)

    def get_id(self):
        return str(self.system_id)