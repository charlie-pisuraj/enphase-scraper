#!/usr/bin/python3
from clickhouse_driver import Client
import yaml
import argparse

class DBClient:
    def __init__(self):
        self.client = Client('localhost')

    def drop_schedule_table(self):
        self.client.execute(
            'DROP TABLE IF EXISTS schedule'
        )

    def create_schedule_table(self):
        self.client.execute(
            'CREATE TABLE IF NOT EXISTS schedule (name String, price_cents UInt32, months UInt8, days UInt8, hours UInt8) Engine = Memory'
        )

    def insert_schedule(self, rows):
        """
        rows = [
            {
                'name': ... ,
                'price_cents': ... ,
                'times': [[...],[...]...] ,
            }
        ]
        """
        self.client.execute(
            f'INSERT INTO schedule VALUES', rows
        )

def parse_args():
    parser = argparse.ArgumentParser(description="Upload Schedule Yaml file to Database")
    parser.add_argument("path", metavar='path', type=str, help='path to schedule file')
    return parser.parse_args()
    
def main(args):
    rows = []
    with open(args.path, "r") as f:
        data = yaml.safe_load(f)
    for cron in data["schedule"]:
        _, hours, _, months, days = cron["cron"].split()
        for month in to_list(months, valid="1-12"):
            for day in to_list(days, valid="0-6"):
                # because clickhouse uses 1-7 monday-sunday while cron is 0-6 sunday-saturday
                if day == 0:
                    day = 7
                for hour in to_list(hours, valid="0-23"):
                    row = {
                        'name': cron["name"] ,
                        'price_cents': int(cron["price"] * 100),
                        'months': month, 
                        'days': day,
                        'hours': hour 
                    }
                    rows.append(row)
    client = DBClient()
    client.drop_schedule_table()
    client.create_schedule_table()
    client.insert_schedule(rows)

def to_list(expression, valid):
    result = []
    if expression == "*":
        expression = valid
    for r in expression.split(","):
        if "-" not in r:
            result.append(int(r))
        else:
            start, end = r.split("-") 
            for i in range(int(start), int(end) + 1):
                result.append(i)
    return result



if __name__ == "__main__":
    args = parse_args()
    main(args)