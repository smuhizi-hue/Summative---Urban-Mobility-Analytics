import datetime
import decimal
import pymysql
import config

def get_connection():
    #open connection to mysql database
    return pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor, #this returns rows in dictionariez
    )

def make_json_friendly(value):
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (datetime.date, datetime.datetime)):
        return str(value)
    return value

def run_query(sql, params=()):
    # runs a select and returns the rows as list of dictionaries
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
    finally:
        connection.close()

    for row in rows:
        for column in row:
            row[column] = make_json_friendly(row[column])
    return rows 


