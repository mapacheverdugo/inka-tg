import sys
import os
import asyncio
import sqlite3
import logging
import time
import calendar
import queue
from logging.handlers import QueueHandler, QueueListener
from postgresqlhandler import PostgreSQLHandler

from dotenv import load_dotenv
from threading import Thread
from ftplib import FTP, FTP_TLS
from PIL import Image
import ffmpeg

from telethon import TelegramClient, events
from telethon.tl.types import PeerUser, User, UpdateNewMessage, UpdateShortMessage, InputUser
from telethon.tl.functions.users import GetFullUserRequest
from telethon.utils import is_image, is_audio, is_video, is_gif
from telethon.sessions import SQLiteSession

load_dotenv()

db_config = {
    "host": os.getenv("PGHOST"),
    "database": os.getenv("PGDATABASE"),
    "port": os.getenv("PGPORT"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD")
}

logger = logging.getLogger('telegram_app')
logger.setLevel(logging.INFO)

stream_formatter = logging.Formatter('[%(levelname)s] [%(social)s - %(usuario)s] %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(stream_formatter)
logger.addHandler(stream_handler)

file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(social)s - %(usuario)s] %(message)s')
file_handler = logging.FileHandler("main.log")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

que = queue.Queue(-1)
queue_handler = QueueHandler(que)
handler = PostgreSQLHandler(db_config, "inka_logs")
listener = QueueListener(que, handler)
logger.addHandler(queue_handler)
listener.start()

IMAGE_TYPE = "image"
VIDEO_TYPE = "video"
AUDIO_TYPE = "audio"
FILE_TYPE = None
GEO_TYPE = None
CONTACT_TYPE = None

class Telegram:
    def __init__(self, app_key, phone, api_id, api_hash, host, message_cb):
        self.app_key = app_key
        self.phone = phone.replace("+", "")
        self.api_id = api_id
        self.api_hash = api_hash
        self.host = host
        self.client = TelegramClient(SQLiteSession("auth/" + app_key), api_id, api_hash)
        self.message_cb = message_cb

    async def emit_message(self, message):
        await self.message_cb(message, self.host)

    async def login(self):
        try:
            logger.info(
                'Intentando iniciar sesión...',
                extra={
                    "usuario": self.phone,
                    "appKey": self.app_key,
                    "social": "Telegram"
                }
            )

            res = await self.client.sign_in(self.phone)

            if (not isinstance(res, User)):
                logger.info(
                    'Usuario nuevo. Debe realizar proceso de inicio con la API',
                    extra={
                        "usuario": self.phone,
                        "appKey": self.app_key,
                        "social": "Telegram"
                    }
                )
                return False
                
            else:
                logger.info(
                    'Sesión iniciada correctamente. Escuchando mensajes...',
                    extra={
                        "usuario": self.phone,
                        "appKey": self.app_key,
                        "social": "Telegram"
                    }
                )
                return True
            pass
        except:
            logger.error(
                'Error inesperado: %s',
                sys.exc_info(),
                extra={
                    "usuario": self.phone,
                    "appKey": self.app_key,
                    "social": "Telegram"
                }
            )
            raise
        
    async def listen(self):
        try:
            @self.client.on(events.NewMessage)
            async def listener(event):
                parsed = await self.parse_message(event)
                await self.emit_message(parsed)
        except:
            logger.error(
                'Error inesperado: %s',
                sys.exc_info(),
                extra={
                    "usuario": self.phone,
                    "appKey": self.app_key,
                    "social": "Telegram"
                }
            )
            raise
        
     

    async def start(self):
        try:
            if (not self.client.is_connected()):
                await self.client.connect()

            logged = await self.login()

            if (logged):  
                await self.listen()
                await self.client.run_until_disconnected()

            
        except:
            logger.error(
                'Error inesperado: %s',
                sys.exc_info(),
                extra={
                    "usuario": self.phone,
                    "appKey": self.app_key,
                    "social": "Telegram"
                }
            )
            raise

    async def upload_file(self, media):
        url = ""
        file_type = ""  

        if (os.getenv("FTP_TYPE") == "ftps"):
            ftp = FTP_TLS()
        else:
            ftp = FTP()
        
        try:
            ftp.connect(os.getenv("FTP_HOST"), int(os.getenv("FTP_PORT")))
            ftp.login(os.getenv("FTP_USER"), os.getenv("FTP_PASSWORD"))
            logger.debug(
                'Conectado correctamente a servidor FTP %s',
                os.getenv("FTP_HOST"),
                extra={
                    "usuario": self.phone,
                    "appKey": self.app_key,
                    "social": "Telegram"
                }
            )

            gmt = time.gmtime()
            ts = calendar.timegm(gmt)
            file_name = self.app_key + "-" + str(ts)
            file_path = await self.client.download_media(media, './temp/' + file_name)
            file_full_name = file_path.split("/")[-1]

            if (is_image(file_path)):
                file_type = "image"
                image = Image.open(file_path)
                image.save(file_path, quality=20, optimize=True)
            elif (is_video(file_path)):
                file_type = "video"
                stream = ffmpeg.input(file_path)
                stream = stream.output(file_path, vcodec="libx264", crf="28")
                stream = stream.overwrite_output()
                out, err = stream.run(capture_stdout=True, capture_stderr=True)
            elif (is_audio(file_path)):
                file_type = "audio"
                stream = ffmpeg.input(file_path)
                stream = stream.output(file_path, **{'map': '0:a', 'map_metadata': -1, 'b:a': '64k'})
                stream = stream.overwrite_output()
                out, err = stream.run(capture_stdout=True, capture_stderr=True)

            file = open(file_path, 'rb')

            if os.path.exists(file_path):
                os.remove(file_path)

            ftp.cwd(os.getenv("FTP_PATH"))
            ftp.storbinary("STOR " + file_full_name, file)

            file.close()

            url = os.getenv("FTP_URL") + "/" + file_full_name
        except:
            logger.error(
                'Error inesperado: %s',
                sys.exc_info(),
                extra={
                    "usuario": self.phone,
                    "appKey": self.app_key,
                    "social": "Telegram"
                }
            )
            raise
        finally:
            ftp.close()
            return (url, file_type)

    async def parse_message(self, event):
        conn = sqlite3.connect("auth/" + self.app_key + '.cache')

        try:
            c = conn.cursor()
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name='users';"
            c.execute(query)

            if (c.fetchone() is None):
                c.execute("CREATE TABLE users(id INTEGER PRIMARY KEY AUTOINCREMENT, appKey TEXT, telegramId TEXT, accessHash TEXT, date DATETIME)")
                conn.commit()

            sender = await event.get_sender()
            user_id = str(sender.id)
            access_hash = str(sender.access_hash)

            c.execute("SELECT * FROM users u WHERE u.appKey = '" + str(self.app_key) + "' AND u.telegramId = '" + user_id + "' ORDER BY date DESC LIMIT 1", )
            row = c.fetchone()
            if (row is None):
                last_hash = access_hash
                c.execute("INSERT INTO users(appKey, telegramId, accessHash, date) VALUES(?, ?, ?, DATETIME('now'))", (self.app_key, user_id, access_hash))
                conn.commit()
            else:
                last_hash = row[3]

                if (access_hash != last_hash):
                    c.execute("INSERT INTO users(appKey, telegramId, accessHash, date) VALUES(?, ?, ?, DATETIME('now'))", (self.app_key, user_id, access_hash))
                    conn.commit()

            user_key = user_id
            user_name = user_id
            attachment_type = ""
            attachment_url = ""
            mensaje_texto = ""

            if (sender.phone):
                user_name = sender.phone

            message = event.original_update
            if (isinstance(message, UpdateShortMessage)):
                mensaje_texto = message.message
            elif (isinstance(message, UpdateNewMessage)):
                media = message.message.media
                if media is not None:
                    attachment_url, attachment_type = await self.upload_file(media)
                    
                mensaje_texto = message.message.message

            dict = {
                'keyApp': self.app_key,
                'userKey': user_key,
                'msj': {
                    'userName': user_name,
                    'type': "PV",
                    'attachmentType': attachment_type,
                    'attachmentUrl': attachment_url,
                    'mensajeTexto': mensaje_texto
                },
                'type': "new_message"
            }

            return dict
        except:
            logger.error(
                'Error inesperado: %s',
                sys.exc_info(),
                extra={
                    "usuario": self.phone,
                    "appKey": self.app_key,
                    "social": "Telegram"
                }
            )
            raise
        finally:
            conn.close()
        

    async def send_message(self, data):
        conn = sqlite3.connect("auth/" + self.app_key + '.cache')
        try:
            if (data["type"] == "RESPONSE_MESSAGE"):
                user_key = data["userKey"]
                attachment_type = ""
                attachment_url = ""

                user_id = int(user_key)

                c = conn.cursor()
                c.execute("SELECT * FROM users u WHERE u.appKey = '" + str(self.app_key) + "' AND u.telegramId = '" + str(user_id) + "' ORDER BY date DESC LIMIT 1", )
                row = c.fetchone()
                access_hash = int(row[3])

                user = InputUser(user_id=user_id, access_hash=access_hash)
                mensaje = data["msj"]["mensajeTexto"]

                if ("attachmentType" in data["msj"]):
                    attachment_type = data["msj"]["attachmentType"]
                if ("attachmentUrl" in data["msj"]):
                    attachment_url = data["msj"]["attachmentUrl"]
                
                if (attachment_type and attachment_url):
                    if (attachment_type.startswith(IMAGE_TYPE)):
                        await self.client.send_message(user, mensaje, file=attachment_url)
                    elif (attachment_type.startswith(VIDEO_TYPE)):
                        await self.client.send_message(user, mensaje, file=attachment_url)
                    elif (attachment_type.startswith(AUDIO_TYPE)):
                        await self.client.send_file(user, attachment_url, voice_note=True)
                    else:
                        await self.client.send_message(user, mensaje, file=attachment_url)
                else:
                    await self.client.send_message(user, mensaje)
        except:
            logger.error(
                'Error inesperado: %s',
                sys.exc_info(),
                extra={
                    "usuario": self.phone,
                    "appKey": self.app_key,
                    "social": "Telegram"
                }
            )
            raise
        finally:
            conn.close()

        
