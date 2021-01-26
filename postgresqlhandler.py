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

    _query = "INSERT INTO log " \
                "(created, level, logger, message, function, " \
                " filename, line_no, traceback, " \
                " request_path, flask_endpoint, remote_addr, " \
                " session_id, user_id) " \
             "VALUES " \
                "(utcnow(), %(level)s, %(logger)s, " \
                " %(message)s, %(function)s, %(filename)s, " \
                " %(line_no)s, %(traceback)s, " \
                " %(request_path)s, %(flask_endpoint)s, %(remote_addr)s, " \
                " %(session_id)s, %(user_id)s)"

    # see TYPE log_level
    _levels = ('debug', 'info', 'warning', 'error', 'critical')

    def __init__(self, db_settings):
        super(PostgreSQLHandler, self).__init__()
        self.db_settings = db_settings
        self.connection = None
        self.cursor = None

    def emit(self, record):
        try:
            level = record.levelname.lower()
            if level not in self._levels:
                level = "debug"

            if record.exc_info:
                lines = traceback.format_exception(*record.exc_info)
                traceback_text = ''.join(lines)
            else:
                traceback_text = None

            args = {
                "level": level,
                "message": record.getMessage(),
                "logger": record.name,
                "function": record.funcName,
                "filename": record.pathname,
                "line_no": record.lineno,
                "traceback": traceback_text,
                "request_path": getattr(record, "request_path", None),
                "flask_endpoint": getattr(record, "flask_endpoint", None),
                "remote_addr": getattr(record, "remote_addr", None),
                "session_id": getattr(record, "session_id", None),
                "user_id": getattr(record, "user_id", None)
            }

            try:
                if self.connection is None:
                    raise psycopg2.OperationalError

                self.cursor.execute(self._query, args)

            except psycopg2.OperationalError:
                self.connection = psycopg2.connect(**self.db_settings)
                self.connection.autocommit = True
                self.cursor = self.connection.cursor()

                self.cursor.execute(self._query, args)

        except Exception:
            self.handleError(record)