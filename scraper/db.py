from clickhouse_driver import Client

class DBClient:
    def __init__(self):
        self.client = Client('localhost')

    def create_production_table(self):
        self.client.execute(
            'CREATE TABLE IF NOT EXISTS solar_production (production_date Date, system_id Int32, timestamp DateTime, devices_reporting Int32, power Int32, energy Int32) ENGINE = ReplacingMergeTree() PARTITION BY toYYYYMM(production_date) ORDER BY (system_id, timestamp);'
        )

    def insert_production(self, rows):
        """
        rows = [
            {
                'devices_reporting': ... ,
                'power': ... ,
                'energy': ... ,
                'system_id': ... ,
                'timestamp': ... ,
                'production_date': ...
            }
        ]
        """
        self.client.execute(
            f'INSERT INTO solar_production VALUES', rows
        )

    def create_schedule_table(self):
        self.client.execute(
            'CREATE TABLE IF NOT EXISTS schedule (name String, price_cents UInt32, months Array(UInt8), days Array(UInt8), hours Array(UInt8)) Engine = Memory'
        )

    def insert_schedule(self, rows):
        """
        rows = [
            {
                'name': ... ,
                'price_cents': ... ,
                'months': [...] ,
                'days': [...] ,
                'hours': [...] ,
            }
        ]
        """
        self.client.execute(
            f'INSERT INTO schedule VALUES', rows
        )
