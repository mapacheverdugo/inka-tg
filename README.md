<<<<<<< HEAD
# Inka Middleware Telegram

Software encargado de conectar Telegram unificando en un mismo chat de servicio al cliente en el proyecto core de Inka.

## 1. Instalación

### 1.1. Requisitos
- Python 3.7 o superior
- `pip3`

### 1.2. Configuración inicial
El archivo de configuración se encuentra en la raíz del proyecto con el nombre de `.env`. Acá un ejemplo:

```
CORE_PORT=9090

FTP_TYPE=ftp
FTP_USER=user@host.cl
FTP_HOST=ftp.host.cl
FTP_PASSWORD=r.2ae3e,6696be
FTP_PORT=21
FTP_PATH=./upload
FTP_URL=https://www.host.cl/url/final/subida

TELEGRAM_VALUE=Telegram
TELEGRAM_PORT=9023

PGUSER=aware
PGHOST=123.12.123.123
PGPASSWORD=r.2ae3e,6696be
PGDATABASE=aware
PGPORT=5432
```

| **Variable**             | **Descripción**                                                                                        |
|--------------------------|--------------------------------------------------------------------------------------------------------|
| `CORE_PORT`              | Puerto del socket TCP del Core.                                                                        |
| `PORT`                   | Puerto donde correrá la API HTTP que donde se hará el proceso de inicio de sesión.                     |
| `FTP_TYPE`               | Tipo del servidor. `ftp` si es FTP o `ftps` si es FTPS                                                 |
| `FTP_USER`               | Usuario del servidor FTP.                                                                              |
| `FTP_HOST`               | IP o host del servidor FTP.                                                                            |
| `FTP_PASSWORD`           | Contraseña del servidor FTP.                                                                           |
| `FTP_PORT`               | Puerto del servidor FTP.                                                                               |
| `FTP_PATH`               | Ubicación interna del servidor FTP donde se guardaran los archivos.                                    |
| `FTP_URL`                | URL publica de donde quedan los archivos. Esta se concatena con el nombr del archivo.                  |
| `TELEGRAM_VALUE`         | Valor en la tabla `inka_app` de las aplicaciones Telegram. Por defecto es `Telegram`.                  |
| `TELEGRAM_PORT`          | Puerto donde correrá el servido socket TCP para recibir mensajes de Telegram.                          |
| `PGUSER`                 | Usuario de la base de datos PostgreSQL.                                                                |
| `PGHOST`                 | IP o host de la base de datos PostgreSQL.                                                              |
| `PGPASSWORD`             | Contraseña de la base de datos PostgreSQL.                                                             |
| `PGDATABASE`             | Nombre de la base de datos PostgreSQL.                                                                 |
| `PGPORT`                 | Puerto de la base de datos PostgreSQL.                                                                 |

### 1.3. Instrucciones

1. Comprobar tener Python 3.7 o una versión superior
```bash
python3 --version
```

2. Instalar requerimientos con `pip`
```bash
pip install -r requirements.txt
```

3. Correr el archivo `main.py`
```bash
python3 main.py
```

## 2. Configuración

### 2.1. Telegram

#### Obtener `api_id` y `api_hash`

1. Inicia sesión con tu cuenta de Telegram [en este enlace](https://my.telegram.org/).
2. Navega hacia  ["API development tools"](https://my.telegram.org/apps)  y rellena el formulario.
3. Obtendrás los parámetros  **`api_id`**  y  **`api_hash`**  requeridos, que corresponden a los valores de `app_data3` y `app_data4` respectivos en la base de datos.

![image](https://user-images.githubusercontent.com/16374322/100661965-0549bf80-3333-11eb-9526-58ae72c5ca4b.png)

#### Configuración de la base de datos

| Columna | Valor |
|--|--|
| `app_name` | `Telegram` |
| `app_data1` | `appKey`. Numero de teléfono + `-tg`. Ej: `56987654321-tg` |
| `app_data2` | Número de teléfono. Ej: `56987654321` |
| `app_data3` | `api_id` obtenida anteriormente. Ej: `1234567` |
| `app_data4` | `api_hash` obtenido anteriormente. Ej: `fcab3735bc4c7f130e1351d55726` |
| `app_data7` | IP o host del Core. Ej: `123.15.12.143` |

#### Inicio de sesión

Deberá iniciar sesión a través de una API HTTP montada dentro del mismo servidor.

1. Lo primero es configurar la cuenta de Telegram en la base de datos como se mostro anteriormente.
2. Iniciar el programa para así habilitar el servidor HTTP.
3. Enviarle al programa la siguiente petición `POST` al endpoint `/code` para recibir un código de inicio de sesión en nuestro teléfono.

```
POST /code HTTP/1.1
Content-Type: application/json

{
    "appKey": "56987654321-tg"      // Correspondiente al appKey definido anteriormente en la base de datos.
}
```

Lo que arrojará una respuesta como la siguiente

```json
{
    "appName": "Telegram",
    "appKey": "56987654321-tg",
    "phone": "56987654321",
    "sendedCode": true,
    "loggedIn": false,
    "message": "Busca en tus mensajes de Telegram el codigo de inicio de sesion y envialo a esta API",
    "codeLength": 5,
    "phoneCodeHash": "4c7f130e13"
}
```

4. Enviarle al programa el código de inicio de sesión recibido, a través de otra petición `POST` al endpoint `/login`.

```
POST /login HTTP/1.1
Content-Type: application/json

{
    "appKey": "56987654321-tg",     // Correspondiente al appKey definido anteriormente en la base de datos.
    "code": "12345",                // Correspondiente al código de inicio de sesión recibido en tu teléfono.
    "phoneCodeHash": "4c7f130e13"   // Correspondiente al phoneCodeHash obtenido en el paso anterior.
}
```

Y si todo sale bien, deberíamos recibir una confirmación en el teléfono y un mensaje de respuesta como este

```json
{
    "appName": "Telegram",
    "appKey": "56987654321-tg",
    "phone": "56987654321",
    "loggedIn": true,
}
```

=======
# inka-telegram

Proyecto Python de Inka para Telegram
>>>>>>> 747ac5c3e2e1a75231124397b64cf89d457faffe
