"""Verify publishing, remote updates, and offline recovery without network access."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import URLError

from game.export_episode import export_episode
from game.remote_episode import RemoteEpisode, validate_episode
from game.server import ROOT


class RemoteEpisodeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cache = Path(self.temp.name) / 'cache' / 'episode.json'
        self.episode = json.loads((ROOT / 'demo.json').read_text())
        self.loader = RemoteEpisode('https://example.com/episode.json', self.cache)

    def download(self, episode):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(episode).encode()
        return response

    @patch('game.remote_episode.urlopen')
    def test_download_updates_and_survives_restart_offline(self, fetch):
        fetch.return_value = self.download(self.episode)
        self.assertEqual(self.loader()['id'], self.episode['id'])
        changed = {**self.episode, 'id': 'new-episode'}
        fetch.return_value = self.download(changed)
        self.assertEqual(self.loader()['id'], 'new-episode')
        self.assertEqual(json.loads(self.cache.read_text())['id'], 'new-episode')
        fetch.side_effect = URLError('offline')
        restored = RemoteEpisode('https://example.com/episode.json', self.cache)()
        self.assertEqual(restored['id'], 'new-episode')
        self.assertIn('refresh_warning', restored)

    @patch('game.remote_episode.urlopen')
    def test_invalid_download_preserves_valid_cache(self, fetch):
        fetch.return_value = self.download(self.episode)
        self.loader()
        fetch.return_value = self.download({'id': 'broken'})
        result = self.loader()
        self.assertEqual(result['id'], self.episode['id'])
        self.assertIn('refresh_warning', result)
        self.assertEqual(json.loads(self.cache.read_text()), self.episode)

    @patch('game.remote_episode.urlopen', side_effect=URLError('offline'))
    def test_first_launch_offline_has_actionable_error(self, fetch):
        with self.assertRaisesRegex(ValueError, 'no cached board'):
            self.loader()

    @patch('game.remote_episode.urlopen')
    def test_unwritable_cache_still_serves_download(self, fetch):
        fetch.return_value = self.download(self.episode)
        self.cache.parent.parent.joinpath('cache').write_text('blocked')
        result = self.loader()
        self.assertEqual(result['id'], self.episode['id'])
        self.assertIn('offline copy', result['refresh_warning'])

    def test_duplicate_clues_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            validate_episode({**self.episode, 'questions': [self.episode['questions'][0]] * 2})

    def test_export_uses_the_server_data_contract(self):
        output = Path(self.temp.name) / 'published' / 'episode.json'
        with patch('game.export_episode.load_episode', return_value=self.episode) as load:
            export_episode(Path('production.duckdb'), output)
        load.assert_called_once_with(Path('production.duckdb'), 'prod')
        self.assertEqual(json.loads(output.read_text()), self.episode)
