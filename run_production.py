"""Run the application with the Waitress production WSGI server."""
import logging

from waitress import serve

from app import app
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    if Config.FLASK_DEBUG:
        logger.warning("FLASK_DEBUG is enabled — disable it in production.")

    logger.info(
        "Starting Waitress on %s:%s (env=%s, auth=%s)",
        Config.FLASK_HOST,
        Config.FLASK_PORT,
        Config.APP_ENV,
        "enabled" if Config.is_auth_required() else "disabled",
    )
    serve(app, host=Config.FLASK_HOST, port=Config.FLASK_PORT, threads=4)
