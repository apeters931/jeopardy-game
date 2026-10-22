"""Check the dbt-to-game data contract using an isolated DuckDB file."""
import tempfile
import unittest
from pathlib import Path

import duckdb
from game.server import load_episode


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
        episode = load_episode(self.path)
        q = episode['questions'][0]
        self.assertEqual(q['question'], 'The capital of France')
        self.assertEqual(q['answer'], 'Paris')
        self.assertEqual(q['round'], '1')
        self.assertIs(q['is_daily_double'], True)
        self.assertEqual(episode['id'], load_episode(self.path)['id'])

    def test_empty_mart_has_actionable_error(self):
        with duckdb.connect(str(self.path)) as con:
            con.execute('delete from mrt_todays_episode_questions')
        with self.assertRaisesRegex(ValueError, 'empty'):
            load_episode(self.path)

    def test_multiple_episodes_are_rejected(self):
        with duckdb.connect(str(self.path)) as con:
            con.execute("insert into mrt_todays_episode_questions select 2, date '2000-01-01', 1, 'X', 200, 'Paris', 'Capital', false")
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            load_episode(self.path)

    def test_missing_file_is_not_created(self):
        missing = self.path.parent / 'missing.duckdb'
        with self.assertRaisesRegex(ValueError, 'not found'):
            load_episode(missing)
        self.assertFalse(missing.exists())


if __name__ == '__main__':
    unittest.main()
