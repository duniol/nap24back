import logging

from flask import Flask, render_template, request, url_for, redirect, jsonify
from flask_compress import Compress
from werkzeug.middleware.proxy_fix import ProxyFix

from app.routes.subtitles import subtitles_bp
from app.routes.manifest import manifest_blueprint
from app.routes.utils import cache
from config import Config

app = Flask(__name__, template_folder='./templates', static_folder='./static')
app.config.from_object('config.Config')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=0, x_prefix=0)

app.register_blueprint(manifest_blueprint)
app.register_blueprint(subtitles_bp)

Compress(app)
cache.init_app(app)


# ---- Global CORS for all responses, including errors
_ALLOWED_ORIGINS = {
    "https://app.strem.io",
    "https://web.strem.io",
}

def _origin_allowed(origin: str) -> bool:
    if not origin:
        return False
    if origin in _ALLOWED_ORIGINS:
        return True
    return origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1")


@app.after_request
def add_cors_headers(resp):
    origin = request.headers.get("Origin", "")
    if _origin_allowed(origin):
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Vary"] = "Origin"
    resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


# Preflight handler
@app.route("/", defaults={"_path": ""}, methods=["OPTIONS"])
@app.route("/<path:_path>", methods=["OPTIONS"])
def any_options(_path):
    return ("", 204)


@app.route('/')
@app.route('/configure')
def index():
    base = request.url_root.rstrip("/")
    host_part = base.split("://", 1)[-1]
    manifest_url = f"{base}{url_for('manifest.addon_manifest')}"
    manifest_magnet = f"stremio://{host_part}{url_for('manifest.addon_manifest')}"
    return render_template('index.html', logged_in=True,
                           manifest_url=manifest_url, manifest_magnet=manifest_magnet)


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.route('/callback')
def callback():
    return redirect(url_for('index'))


if __name__ == '__main__':
    from waitress import serve
    serve(app, host=Config.FLASK_HOST, port=int(Config.FLASK_PORT))
