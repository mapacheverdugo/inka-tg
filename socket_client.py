import socket
import json
import logging

logger = logging.getLogger('main_app')

class SocketClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def write(self, message):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_address = (self.host, self.port)

        sock.connect(server_address)
        
        try:
            message_ready = json.dumps(message, separators=(',', ':'))
            message_ready += "\n"
            
            sock.send(message_ready.encode())
            logger.debug('Enviado: %s', message)
            pass
        except:
            logger.error('Error inesperado: %s', sys.exc_info())
            raise
        finally:
            logger.debug('Conexión con socket cerrada')
            sock.close()
        