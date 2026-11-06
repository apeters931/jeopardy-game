"""WSGI entry point for hosts such as PythonAnywhere."""
from pathlib import Path

from flask import Flask, jsonify

from game.remote_episode import DEFAULT_EPISODE_URL, RemoteEpisode

ROOT = Path(__file__).resolve().parent


def create_app(episode_loader=None) -> Flask:
    app = Flask(__name__, static_folder=str(ROOT / 'static'), static_url_path='')
    load_board = episode_loader if episode_loader is not None else RemoteEpisode(
        DEFAULT_EPISODE_URL, ROOT / '.cache' / 'episode.json'
    )

    @app.after_request
    def prevent_stale_boards(response):
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/')
    def index():
        return app.send_static_file('index.html')

    @app.get('/api/episode')
    def episode():
        try:
            return jsonify(load_board())
        except (OSError, ValueError) as exc:
            return jsonify(error=f'Could not refresh the episode: {exc}'), 503

    return app


application = create_app()
