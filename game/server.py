"""Serve the local Jeopardy game and a read-only snapshot of its dbt mart."""
import argparse
import hashlib
import json
from datetime import date, datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT.parent / 'jeopardy_seasons.duckdb'


def load_episode(db_path: Path) -> dict:
    import duckdb
    if not db_path.is_file():
        raise ValueError(f'Database not found: {db_path}. Build your dbt models first.')
    with duckdb.connect(str(db_path), read_only=True) as con:
        cursor = con.execute('select question_id, air_date, round, category, point_value, question, answer, is_daily_double from main.mrt_todays_episode_questions')
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


def make_handler(episode: dict):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ROOT / 'static'), **kwargs)

        def do_GET(self):
            if self.path.split('?')[0] == '/api/episode':
                body = json.dumps(episode).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                super().do_GET()
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--demo', action='store_true', help='Use explicitly labeled sample questions instead of DuckDB.')
    args = parser.parse_args()
    try:
        episode = json.loads((ROOT / 'demo.json').read_text()) if args.demo else load_episode(args.db.resolve())
    except Exception as exc:
        parser.exit(1, f'Could not load the episode: {exc}\nUse a Python environment with DuckDB 2.0 or newer and build mrt_todays_episode_questions.\n')
    server = ThreadingHTTPServer((args.host, args.port), make_handler(episode))
    print(f'Game ready: http://{args.host}:{args.port} (episode {episode["air_date"]})', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
