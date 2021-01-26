import os
import sys
import logging
import psycopg2
import asyncio
from dotenv import load_dotenv
from multiprocessing import Process
from threading import Thread

from telegram import Telegram
from socket_server import SocketServer
from socket_client import SocketClient
from http_server import HttpServer

load_dotenv()

logger = logging.getLogger('main_app')
logger.setLevel(logging.INFO)

stream_formatter = logging.Formatter('[%(levelname)s] %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(stream_formatter)
logger.addHandler(stream_handler)

file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler = logging.FileHandler("main.log")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

logging.getLogger('telethon').setLevel(level=logging.WARNING)
logging.getLogger('werkzeug').setLevel(level=logging.WARNING)

db_config = {
    "host": os.getenv("PGHOST"),
    "database": os.getenv("PGDATABASE"),
    "port": os.getenv("PGPORT"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD")
}

rows = []
tgs = []

def get_tg(app_key):
    founded = None

    for tg in tgs:
        if (tg.app_key == app_key):
            founded = tg
    
    return founded

async def on_client_message(message, host):
    client = SocketClient(host, int(os.getenv("CORE_PORT")))
    client.write(message)

async def on_response_message(data):
    app_key = data["keyApp"]
    tg = get_tg(app_key)
    await tg.send_message(data)

async def init_server():
    server = SocketServer(int(os.getenv("TELEGRAM_PORT")), on_response_message)
    await server.create()

async def listen_telegrams():
    try:
        conn = psycopg2.connect(**db_config)

        cursor = conn.cursor()
        query = "SELECT * FROM inka_app WHERE app_activo = 1"
        cursor.execute(query)
        rows = cursor.fetchall()

        conn.close()

        for row in rows:
            app_name = str(row[2]).strip().replace("\n", "")
            if (app_name.lower() == str(os.getenv("TELEGRAM_VALUE")).lower().strip()):
                app_key = str(row[4]).strip().replace("\n", "")
                phone = str(row[5]).strip().replace("\n", "")
                api_id = str(row[6]).strip().replace("\n", "")
                api_hash = str(row[7]).strip().replace("\n", "")
                host = str(row[10]).strip().replace("\n", "")
                tg = Telegram(app_key, phone, api_id, api_hash, host, on_client_message)
                tgs.append(tg)

        tasks = []

        for tg in tgs:
            tasks.append(tg.start())

        await asyncio.gather(*tasks)

    except:
        logger.error('Error inesperado: %s', sys.exc_info())
        raise

def _init_server():
    asyncio.run(init_server())

def _listen_telegrams():
    asyncio.run(listen_telegrams())

def _init_http_server():
    asyncio.run(HttpServer.run())

async def main():
    try:
        thread1 = Thread(name="SocketServer", target=_init_server)
        thread1.start()

        thread2 = Thread(name="HttpServer", target=_init_http_server)
        thread2.start()

        thread3 = Thread(name="TelegramMain", target=_listen_telegrams)
        thread3.start()
        pass
    except:
        logger.error('Error inesperado: %s', sys.exc_info())
        raise
    
asyncio.run(main())