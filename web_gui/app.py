'''
Web GUI для управления Proverkin.

Стек: Python (Flask) + Jinja2 + чистый HTML/CSS, без JS/TS.
Доступ -- HTTP Basic Auth по WEB_ADMIN_USER / WEB_ADMIN_PASSWORD.
'''

# project
from config_data.config import config
from database.connector import PostgresConnector as pg

# misc
import logging
from logging import handlers
import os
from functools import wraps

from flask import Flask, request, Response


# ====== логирование ======
os.makedirs(os.path.dirname(config.lg.path), exist_ok = True)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = handlers.TimedRotatingFileHandler(
    config.lg.path, when = 'midnight', interval = 1
)
file_handler.setFormatter(logging.Formatter(config.lg.log_format))
logger.addHandler(file_handler)

if config.lg.in_terminal:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(config.lg.log_format))
    logger.addHandler(stream_handler)


def basic_auth_required(view_fn):
    @wraps(view_fn)
    def wrapper(*args, **kwargs):
        auth = request.authorization
        if (auth is None
                or auth.username != config.auth.admin_user
                or auth.password != config.auth.admin_password):
            return Response(
                'Auth required', 401,
                {'WWW-Authenticate': 'Basic realm="Proverkin admin"'}
            )
        return view_fn(*args, **kwargs)
    return wrapper


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder = 'templates',
        static_folder = 'static'
    )
    app.secret_key = config.auth.secret_key

    # ждем БД на старте
    if not pg.init_check():
        logger.warning('Postgres init_check вернул False (web_gui продолжает старт)')

    # подключаем blueprint'ы
    from routes.dashboard import bp as dashboard_bp
    from routes.users import bp as users_bp
    from routes.sets import bp as sets_bp
    from routes.user_sets import bp as user_sets_bp
    from routes.queue import bp as queue_bp
    from routes.logs import bp as logs_bp

    for bp in (dashboard_bp, users_bp, sets_bp, user_sets_bp, queue_bp, logs_bp):
        # Basic Auth -- на каждый view внутри blueprint
        for endpoint, view_fn in list(bp.view_functions.items()):
            bp.view_functions[endpoint] = basic_auth_required(view_fn)
        app.register_blueprint(bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host = config.svc.host, port = config.svc.port, debug = False)
