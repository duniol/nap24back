import logging
import logging from flask import Flask, render_template, session, url_for, redirect from flask_compress import Compress from app.routes.subtitles import subtitles_bp from app.routes.manifest import manifest_blueprint from app.routes.utils import cache from config import Config app = Flask(__name__, template_folder='./templates', static_folder='./static') app.config.from_object('config.Config') app.register_blueprint(manifest_blueprint) app.register_blueprint(subtitles_bp) Compress(app) cache.init_app(app) logging.basicConfig(format='%(asctime)s %(message)s') @app.route('/') @app.route('/configure') def index(): """ Render the index page """ manifest_url = f'{Config.PROTOCOL}://{Config.REDIRECT_URL}/manifest.json' manifest_magnet = f'stremio://{Config.REDIRECT_URL}/manifest.json' return render_template('index.html', logged_in=True, manifest_url=manifest_url, manifest_magnet=manifest_magnet) @app.route('/favicon.ico') def favicon(): """ Render the favicon for the app """ return app.send_static_file('favicon.ico') @app.route('/callback') def callback(): """ Callback URL from MyAnimeList :return: A webpage response with the manifest URL and Magnet URL """ return redirect(url_for('index')) if __name__ == '__main__': from waitress import serve serve(app, host='0.0.0.0', port=5000)
from flask import Flask, render_template, session, url_for, redirect, make_response, request

from flask_compress import Compress
from app.routes.subtitles import subtitles_bp
from app.routes.manifest import manifest_blueprint
from app.routes.utils import cache
from config import Config

# --- konfiguracja aplikacji ---
app = Flask(__name__, template_folder='./templates', static_folder='./static')
app.config.from_object('config.Config')
app.register_blueprint(manifest_blueprint)
app.register_blueprint(subtitles_bp)

Compress(app)
cache.init_app(app)

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

# --- CORS: whitelist originów dopuszczonych do pobierania zasobów (webowe Stremio) ---
ALLOWED_ORIGINS = {
    "https://app.strem.io",
    # Dodatkowo, jeśli testujesz z lokalnego pliku/preview, możesz chwilowo dodać:
    # "http://localhost:3000",
    # "http://127.0.0.1:3000",
}

ALLOWED_METHODS = "GET, HEAD, OPTIONS"
ALLOWED_HEADERS = "Content-Type, Range"
EXPOSE_HEADERS = "Content-Range"   # jeśli gdzieś zwracasz Content-Range i chcesz go widzieć w JS


def _add_cors_headers(resp):
    """
    Dodaje nagłówki CORS do każdej odpowiedzi (w tym dla preflightów).
    """
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Vary"] = "Origin"
    # Metody/nagłówki dozwolone zawsze deklarujemy:
    resp.headers["Access-Control-Allow-Methods"] = ALLOWED_METHODS
    resp.headers["Access-Control-Allow-Headers"] = ALLOWED_HEADERS
    # Nagłówki, które mają być dostępne po stronie JS:
    resp.headers["Access-Control-Expose-Headers"] = EXPOSE_HEADERS
    return resp


@app.after_request
def after_request(response):
    # dokładamy CORS do każdej odpowiedzi
    return _add_cors_headers(response)


# Globalny preflight dla wszystkich ścieżek (także tych z blueprintów)
@app.route('/<path:any_path>', methods=['OPTIONS'])
def cors_preflight(any_path):
    return _add_cors_headers(make_response(("", 204)))


@app.route('/')
@app.route('/configure')
def index():
    """
    Render the index page
    """
    manifest_url = f'{Config.PROTOCOL}://{Config.REDIRECT_URL}/manifest.json'
    manifest_magnet = f'stremio://{Config.REDIRECT_URL}/manifest.json'
    return render_template(
        'index.html',
        logged_in=True,
        manifest_url=manifest_url,
        manifest_magnet=manifest_magnet
    )


@app.route('/favicon.ico')
def favicon():
    """
    Render the favicon for the app
    """
    return app.send_static_file('favicon.ico')


@app.route('/callback')
def callback():
    """
    Callback URL from MyAnimeList
    :return: A webpage response with the manifest URL and Magnet URL
    """
    return redirect(url_for('index'))


if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
