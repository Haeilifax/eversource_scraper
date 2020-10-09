"""Clean and Insert data scraped from Eversource Account Histories into MySQL database"""
import datetime
from datetime import timedelta
import os

import dotenv

from eversource_scraper import MySQLdbAdapter as mysqldb


def _configure_settings():
    dotenv.load_dotenv()
    config = {
        "dbuser": os.getenv("DATABASE_USERNAME"),
        "dbpassword": os.getenv("DATABASE_PASSWORD"),
        "dbname": os.getenv("DATABASE_NAME")
    }
    return config


def clean(data):
    """Cleans data from selenium_scraper


    """
    clean_data = {}
    for account, address in data.items():
        for name, info in address.items():
            if info:
                unit_data = []
                unit_name = f"{account};{name}"
                records = map(lambda x: x.split(), info)
                for record in records:
                    record_data = {}
                    start_date = datetime.datetime.strptime(record[0], "%m/%d/%Y")
                    record_data["start_date"] = start_date
                    record_data["end_date"] = start_date + timedelta(int(record[2]))
                    record_data["_usage"] = record[1]
                    record_data["charge"] = record[5][1:]
                    record_data["avg_temp"] = record[6]
                    unit_data.append(record_data)
                clean_data[unit_name] = unit_data
    return clean_data


def insert_data(clean_data, config):
    DATABASE = config.get("dbname")
    USER = config.get("dbuser")
    PASSWORD = config.get("dbpassword")
    conn = mysqldb.connect(user=USER, password=PASSWORD, database=DATABASE)
    with conn:
        data_insert_sql = (
        "INSERT INTO "
        "data (unit_name, start_date, end_date, _usage, charge, avg_temp) "
        "VALUES "
        "(%(unit_name)s, %(start_date)s, %(end_date)s, %(_usage)s, %(charge)s, %(avg_temp)s)"
        )
        check_sql = "SELECT unit_name FROM unit_name_map WHERE unit_name=%s"
        unit_name_sql = "INSERT INTO unit_name_map (unit_name) VALUES (%s)"
        print("Inserting data...")
        with conn.cursor() as cur:
            for unit_name, records in clean_data.items():
                for record in records:
                    try:
                        cur.execute(data_insert_sql, {"unit_name": unit_name, **record})
                    except Exception as e:
                        # TODO: make a polite log instead of print
                        print(f"Error encountered on unit {unit_name}, "
                        f"from record dated {record.get('start_date', 'unknown')}, "
                        f"with error: {str(e)}"
                        )
                        raise e
                cur.execute(check_sql, (unit_name,))
                if not cur.fetchall():
                    cur.execute(unit_name_sql, (unit_name,))


def main(data, config=None):
    if not config:
        config = _configure_settings()
    print("Cleaning data...")
    clean_data = clean(data)
    print("Connecting to database...")
    insert_data(clean_data, config)
    print("Finished!")
