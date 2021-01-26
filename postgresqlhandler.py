import logging
import traceback
import psycopg2

class PostgreSQLHandler(logging.Handler):
    """
    A :class:`logging.Handler` that logs to the `log` PostgreSQL table
    Does not use :class:`PostgreSQL`, keeping its own connection, in autocommit
    mode.
    .. DANGER:
        Beware explicit or automatic locks taken out in the main requests'
        transaction could deadlock with this INSERT!
        In general, avoid touching the log table entirely. SELECT queries
        do not appear to block with INSERTs. If possible, touch the log table
        in autocommit mode only.
    `db_settings` is passed to :meth:`psycopg2.connect` as kwargs
    (``connect(**db_settings)``).
    """

    

    def __init__(self, db_settings, db_name):
        super(PostgreSQLHandler, self).__init__()
        self.db_settings = db_settings
        self.connection = None
        self.cursor = None
        self.query = "INSERT INTO " + db_name + " (timestamp, level, message, social, appkey) " \
             "VALUES (NOW(), %(levelname)s, %(msg)s, %(social)s, %(appKey)s)"

    def emit(self, record):
        try:

            try:
                if self.connection is None:
                    raise psycopg2.OperationalError

                self.cursor.execute(self.query, record.__dict__)

            except psycopg2.OperationalError:
                self.connection = psycopg2.connect(**self.db_settings)
                self.connection.autocommit = True
                self.cursor = self.connection.cursor()

                self.cursor.execute(self.query, record.__dict__)

        except Exception:
            self.handleError(record)