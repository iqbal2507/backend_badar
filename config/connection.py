from flask import current_app
import pyodbc

def dsn():
    dsn = current_app.config['DSN']
    dsn_string_conn = f"""DSN={dsn}"""
    conn = pyodbc.connect(dsn_string_conn, autocommit=True)
    return conn