"""Serve the Jeopardy game with a GitHub-published board or a local dbt mart."""
import argparse
import hashlib
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT.parent / 'jeopardy_seasons.duckdb'

# Support both direct script execution and module imports.
if __package__:
    from .remote_episode import DEFAULT_EPISODE_URL, RemoteEpisode
else:
    from remote_episode import DEFAULT_EPISODE_URL, RemoteEpisode


def load_episode(db_path: Path, schema: str = 'prod') -> dict:
    import duckdb
    if not db_path.is_file():
        raise ValueError(f'Database not found: {db_path}. Build your dbt models first.')
    quoted_schema = '"' + schema.replace('"', '""') + '"'
    with duckdb.connect(str(db_path), read_only=True) as con:
        cursor = con.execute(f'select question_id, air_date, round, category, point_value, question, answer, is_daily_double from {quoted_schema}.mrt_todays_episode_questions')
        columns = [column[0] for column in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    if not rows:
        raise ValueError('The episode mart is empty. Select an episode and rebuild its questions model.')
    dates = {str(row['air_date']) for row in rows}
    if len(dates) != 1:
        raise ValueError('The episode mart must contain exactly one air date.')
    for row in rows:
        row['id'] = str(row.pop('question_id'))
        row['air_date'] = str(row['air_date'])
        row['point_value'] = int(row['point_value'] or 0)
        row['is_daily_double'] = str(row['is_daily_double']).lower() in ('true', '1')
        row['round'] = str(row['round'])
        # The source dataset uses Jeopardy's terminology: answer = clue, question = response.
        row['question'], row['answer'] = row['answer'], row['question']
    rows.sort(key=lambda row: (row['round'], row['category'], row['point_value'], row['id']))
    digest = hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest()[:16]
    return {'id': digest, 'air_date': next(iter(dates)), 'questions': rows}


def make_handler(episode: dict, db_path: Path | None = None, schema: str = 'prod', episode_loader=None):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ROOT / 'static'), **kwargs)

        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')
            super().end_headers()

        def do_GET(self):
            if self.path.split('?')[0] == '/api/episode':
                try:
                    current_episode = episode_loader() if episode_loader else (load_episode(db_path, schema) if db_path is not None else episode)
                    body = json.dumps(current_episode).encode()
                    status = 200
                except Exception as exc:
                    body = json.dumps({'error': f'Could not refresh the episode: {exc}'}).encode()
                    status = 503
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                super().do_GET()
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, help='Read a local DuckDB file instead of GitHub.')
    parser.add_argument('--local', action='store_true', help='Read the default local DuckDB file.')
    parser.add_argument('--episode-url', default=DEFAULT_EPISODE_URL)
    parser.add_argument('--cache', type=Path, default=ROOT / '.cache' / 'episode.json')
    parser.add_argument('--schema', default='prod', help='DuckDB schema containing the episode mart (default: prod).')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--demo', action='store_true', help='Use explicitly labeled sample questions instead of DuckDB.')
    args = parser.parse_args()
    db_path = (args.db or DEFAULT_DB).resolve() if args.local or args.db else None
    loader = None if args.demo or db_path else RemoteEpisode(args.episode_url, args.cache)
    try:
        if args.demo:
            episode = json.loads((ROOT / 'demo.json').read_text())
        elif loader:
            # Fetch through the API so a first-download failure has a retry button.
            episode = None
        else:
            episode = load_episode(db_path, args.schema)
    except Exception as exc:
        parser.exit(1, f'Could not load the episode: {exc}\nCheck your connection and the published episode. Use --local to read the local DuckDB mart.\n')
    server = ThreadingHTTPServer((args.host, args.port), make_handler(episode, None if args.demo else db_path, args.schema, loader))
    source = f'episode {episode["air_date"]}' if episode else "GitHub-published board"
    print(f'Game ready: http://{args.host}:{args.port} ({source})', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
