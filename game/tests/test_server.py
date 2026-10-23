"""Check the dbt-to-game data contract using an isolated DuckDB file."""
import json
import threading
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen
import tempfile
import unittest
from pathlib import Path

import duckdb
from game.server import load_episode, make_handler


class EpisodeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'episode.duckdb'
        with duckdb.connect(str(self.path)) as con:
            con.execute('''create table mrt_todays_episode_questions as
                select 1 as question_id, date '1996-04-09' as air_date,
                1 as round, 'GEOGRAPHY' as category, 200 as point_value,
                'Paris' as question, 'The capital of France' as answer,
                true as is_daily_double''')

    def tearDown(self):
        self.temp.cleanup()

    def test_source_terminology_maps_to_playable_clue(self):
        episode = load_episode(self.path, schema='main')
        q = episode['questions'][0]
        self.assertEqual(q['question'], 'The capital of France')
        self.assertEqual(q['answer'], 'Paris')
        self.assertEqual(q['round'], '1')
        self.assertIs(q['is_daily_double'], True)
        self.assertEqual(episode['id'], load_episode(self.path, schema='main')['id'])

    def test_api_refreshes_updated_data_and_recovers_from_empty_mart(self):
        original = load_episode(self.path, schema='main')
        server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(original, self.path, schema='main'))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{server.server_port}/api/episode'
        try:
            with urlopen(url) as response:
                self.assertEqual(json.load(response)['id'], original['id'])
                self.assertEqual(response.headers['Cache-Control'], 'no-store')
            with duckdb.connect(str(self.path)) as con:
                con.execute("update mrt_todays_episode_questions set answer = 'A new clue'")
            with urlopen(url) as response:
                updated = json.load(response)
            self.assertNotEqual(updated['id'], original['id'])
            self.assertEqual(updated['questions'][0]['question'], 'A new clue')
            with duckdb.connect(str(self.path)) as con:
                con.execute('delete from mrt_todays_episode_questions')
            with self.assertRaises(HTTPError) as failure:
                urlopen(url)
            self.assertEqual(failure.exception.code, 503)
            self.assertIn('empty', json.load(failure.exception)['error'])
            with duckdb.connect(str(self.path)) as con:
                con.execute("insert into mrt_todays_episode_questions values (2, date '2001-01-01', 1, 'NEW', 200, 'Paris', 'Capital', false)")
            with urlopen(url) as response:
                self.assertEqual(json.load(response)['air_date'], '2001-01-01')
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_default_schema_reads_production(self):
        with duckdb.connect(str(self.path)) as con:
            con.execute('create schema prod')
            con.execute('create table prod.mrt_todays_episode_questions as select * from main.mrt_todays_episode_questions')
            con.execute("update prod.mrt_todays_episode_questions set air_date = date '1998-05-15'")
        self.assertEqual(load_episode(self.path)['air_date'], '1998-05-15')
        self.assertEqual(load_episode(self.path, schema='main')['air_date'], '1996-04-09')

    def test_empty_mart_has_actionable_error(self):
        with duckdb.connect(str(self.path)) as con:
            con.execute('delete from mrt_todays_episode_questions')
        with self.assertRaisesRegex(ValueError, 'empty'):
            load_episode(self.path, schema='main')

    def test_multiple_episodes_are_rejected(self):
        with duckdb.connect(str(self.path)) as con:
            con.execute("insert into mrt_todays_episode_questions select 2, date '2000-01-01', 1, 'X', 200, 'Paris', 'Capital', false")
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            load_episode(self.path, schema='main')

    def test_missing_file_is_not_created(self):
        missing = self.path.parent / 'missing.duckdb'
        with self.assertRaisesRegex(ValueError, 'not found'):
            load_episode(missing, schema='main')
        self.assertFalse(missing.exists())


if __name__ == '__main__':
    unittest.main()
