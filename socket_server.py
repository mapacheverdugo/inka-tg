import socket
import json
import asyncio
import logging
from threading import Thread

HOST = '0.0.0.0'

class SocketServer:
    def __init__(self, port, on_message):
        self.port = port
        self.on_message = on_message

    def handle_message(self, data):
        logging.debug('Recibido: %s', data)
        type = data['type']
        if (type == "RELOAD_CONFIGURATION"):
            logging.info('Recargando configuraciones...')
        elif (type == "RESPONSE_MESSAGE"):
            asyncio.run(self.on_message(data))
            

    async def create(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        sock.bind((HOST, self.port))
        sock.listen()

        logging.info('Socket esperando conexión en %s puerto %s', HOST, self.port)
        
        while True:
            connection, client_address = sock.accept()

            logging.debug('Nueva conexión desde %s', client_address)

            try:
                while True:
                    data = connection.recv(1024)
                    data_str = data.decode("ISO-8859-1")

                    if (data and data_str and data_str.startswith("{")):
                        
                        json_data = json.loads(data_str)

                        thread = Thread(target=self.handle_message, args=[json_data])
                        thread.start()
                        response = json.dumps({
                            "code": "000",
                            "description": "Success Proccess"
                        })
                        response += "\n"
                        connection.sendall(response.encode())
                    else:
                        logging.debug('No se recibió información desde %s', client_address)
                        break
            finally:
                logging.debug('Conexión con %s cerrada', client_address)
                connection.close()
        
        sock.close()