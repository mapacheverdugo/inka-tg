import flask
import psycopg2
import os
import logging
import asyncio

from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.types import User
from telethon.sessions import SQLiteSession
from flask.logging import default_handler

load_dotenv()

app = flask.Flask(__name__)
app.config["DEBUG"] = False
app.use_reloader = False

async def sendCode(app_key, api_id, api_hash, phone):
    client = TelegramClient(SQLiteSession("auth/" + app_key), api_id, api_hash)
    await client.connect()
    res = await client.sign_in(phone)
    return res

async def loginWithCode(app_key, api_id, api_hash, phone, code, hash):
    client = TelegramClient(SQLiteSession("auth/" + app_key), api_id, api_hash)
    await client.connect()
    await client.sign_in(phone=phone, code=code, phone_code_hash=hash)
    return True

def code(appKey):
    conn = psycopg2.connect(
        host = os.getenv("PGHOST"),
        database = os.getenv("PGDATABASE"),
        port = os.getenv("PGPORT"),
        user = os.getenv("PGUSER"),
        password = os.getenv("PGPASSWORD")
    )

    cursor = conn.cursor()
    query = "SELECT * FROM inka_app WHERE app_activo = 1"
    cursor.execute(query)
    rows = cursor.fetchall()

    conn.close()

    for row in rows:
        app_name = str(row[2]).strip().replace("\n", "")
        if (app_name.lower() == str(os.getenv("TELEGRAM_VALUE")).lower().strip()):
            app_key = str(row[4]).strip().replace("\n", "")
            if (app_key == appKey):
                phone = str(row[5]).strip().replace("\n", "")
                api_id = str(row[6]).strip().replace("\n", "")
                api_hash = str(row[7]).strip().replace("\n", "")

                res = asyncio.run(sendCode(app_key, api_id, api_hash, phone))

                if (not isinstance(res, User)):
                    return {
                        'appName': app_name,
                        'appKey': app_key,
                        'phone': phone,
                        'sendedCode': True,
                        'loggedIn': False,
                        'message': 'Busca en tus mensajes de Telegram el codigo de inicio de sesion y envialo a esta API',
                        'codeLength': res.type.length,
                        'phoneCodeHash': res.phone_code_hash
                    }
                else:
                    return {
                        'appName': app_name,
                        'appKey': app_key,
                        'phone': phone,
                        'sendedCode': False,
                        'loggedIn': True,
                        'message': 'El usuario ya esta loggeado correctamente',
                        'codeLength': None,
                        'phoneCodeHash': None
                    }

    
    return {
        'error': True,
        'message': 'No se encontró Telegram con ese appKey'
    }

def login(appKey, code, hash):
    conn = psycopg2.connect(
        host = os.getenv("PGHOST"),
        database = os.getenv("PGDATABASE"),
        port = os.getenv("PGPORT"),
        user = os.getenv("PGUSER"),
        password = os.getenv("PGPASSWORD")
    )

    cursor = conn.cursor()
    query = "SELECT * FROM inka_app WHERE app_activo = 1"
    cursor.execute(query)
    rows = cursor.fetchall()

    conn.close()

    for row in rows:
        app_name = str(row[2]).strip().replace("\n", "")
        if (app_name.lower() == str(os.getenv("TELEGRAM_VALUE")).lower().strip()):
            app_key = str(row[4]).strip().replace("\n", "")
            if (app_key == appKey):
                phone = str(row[5]).strip().replace("\n", "")
                api_id = str(row[6]).strip().replace("\n", "")
                api_hash = str(row[7]).strip().replace("\n", "")

                res = asyncio.run(loginWithCode(app_key, api_id, api_hash, phone, code, hash))

                return {
                    'appName': app_name,
                    'appKey': app_key,
                    'phone': phone,
                    'loggedIn': res
                }

    
    return {
        'error': True,
        'message': 'No se encontró Telegram con ese appKey'
    }

@app.route('/telegram/code', methods=['POST'])
def _code1():
    json = request.get_json(force=True)
    return code(json["appKey"])

@app.route('/telegram/login', methods=['POST'])
def _login1(appKey, code, hash):
    json = request.get_json(force=True)
    return login(json["appKey"], json["code"], json["phoneCodeHash"])

# Para pruebas
""" @app.route('/code/<appKey>', methods=['GET'])
def _code2(appKey):
    return code(appKey)

@app.route('/login/<appKey>/<code>/<hash>', methods=['GET'])
def _login2(appKey, code, hash):
    return login(appKey, code, hash) """




class HttpServer:
    def run():
        app.run(host='0.0.0.0')
