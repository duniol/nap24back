import base64
import json
from urllib.parse import parse_qs, unquote

from flask import Blueprint, request, url_for, redirect, abort

from app.routes import napisy24_client
from app.routes.utils import respond_with, return_srt_file
from app.lib.subtitles import extract_and_convert

subtitles_bp = Blueprint('subtitles', __name__)


def _encode_params(payload: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


@subtitles_bp.route('/subtitles/<content_type>/<content_id>.json', methods=["GET"])
def subtitles_json(content_type: str, content_id: str):
    """Proper Stremio subtitles endpoint: extras come as query string."""
    content_id = unquote(content_id)
    video_hash = request.args.get("videoHash")
    video_size = request.args.get("videoSize")
    filename = request.args.get("filename")

    results = []

    try:
        if video_hash and video_size:
            # Use Napisy24 by hash
            response, zipfile, fps, sub_id = napisy24_client.fetch_subtitles_from_hash(
                filehash=video_hash, filename=filename, filesize=video_size
            )
            if response and sub_id:
                enc = _encode_params({"id": sub_id, "fps": fps})
                download_url = url_for('subtitles.download_subtitles_from_id', params=enc, _external=True)
                results.append({
                    "id": f"napisy24:{sub_id}",
                    "url": download_url,
                    "title": "Napisy24 • PL",
                    "lang": "pol",
                    "format": "srt"
                })
        # (opcjonalnie) tu możesz dodać fallback po IMDb/tekście
    except Exception as e:
        return respond_with({"error": str(e)})

    return respond_with(results)


@subtitles_bp.route('/subtitles/<content_type>/<path:rest>', methods=["GET"])
def subtitles_compat(content_type: str, rest: str):
    """Compatibility redirect for old/bad paths that put extras in the URL path.
    Example bad:
      /subtitles/series/tt1234567:1:2/videoHash=abc&videoSize=123.json
    We redirect to:
      /subtitles/series/tt1234567:1:2.json?videoHash=abc&videoSize=123
    """
    rest = unquote(rest)
    # only handle paths that end with .json and contain /videoHash=
    if rest.endswith(".json") and "/videoHash=" in rest:
        core = rest[:-5]  # strip .json
        try:
            id_part, extras = core.split("/videoHash=", 1)
        except ValueError:
            abort(404)
        query = f"videoHash={extras}"
        good = url_for('subtitles.subtitles_json', content_type=content_type, content_id=id_part, _external=True)
        return redirect(f"{good}?{query}", code=301)
    abort(404)


@subtitles_bp.route('/download/id/<params>.srt', methods=["GET"])
def download_subtitles_from_id(params: str):
    try:
        decoded = json.loads(base64.urlsafe_b64decode(params).decode())
        zipfile = napisy24_client.download_subtitle_id(subtitle_id=decoded["id"])
        if zipfile:
            return return_srt_file(extract_and_convert(zipfile, decoded.get("fps")), params)
        return respond_with({"error": "not_found"})
    except Exception as e:
        return respond_with({"error": str(e)})
