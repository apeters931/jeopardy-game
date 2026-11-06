"""Verify the hosted app without starting a standalone HTTP server."""
import unittest
from unittest.mock import Mock

from game.wsgi import create_app


class WsgiTests(unittest.TestCase):
    def setUp(self):
        self.board = {'id': 'example', 'air_date': '2000-01-01', 'questions': []}
        self.loader = Mock(return_value=self.board)
        self.app = create_app(self.loader)
        self.client = self.app.test_client()

    def test_import_does_not_download_a_board(self):
        self.loader.assert_not_called()

    def test_serves_all_browser_assets(self):
        for path, content_type in [('/', 'text/html'), ('/style.css', 'text/css'),
                                   ('/app.js', 'javascript'), ('/logic.mjs', 'javascript')]:
            with self.subTest(path=path), self.client.get(path) as response:
                self.assertEqual(response.status_code, 200)
                self.assertIn(content_type, response.content_type)
                self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_downloads_each_requested_board(self):
        self.assertEqual(self.client.get('/api/episode').json, self.board)
        self.loader.return_value = {**self.board, 'id': 'updated'}
        self.assertEqual(self.client.get('/api/episode').json['id'], 'updated')
        self.assertEqual(self.loader.call_count, 2)

    def test_download_error_is_retryable(self):
        self.loader.side_effect = ValueError('No cached board')
        response = self.client.get('/api/episode')
        self.assertEqual(response.status_code, 503)
        self.assertIn('No cached board', response.json['error'])
        self.loader.side_effect = None
        self.assertEqual(self.client.get('/api/episode').status_code, 200)

    def test_cached_board_warning_reaches_browser(self):
        self.loader.return_value = {**self.board, 'refresh_warning': 'Offline'}
        self.assertEqual(self.client.get('/api/episode').json['refresh_warning'], 'Offline')

    def test_other_source_files_are_not_public(self):
        for path in ['/../remote_episode.py', '/remote_episode.py', '/.cache/episode.json']:
            self.assertEqual(self.client.get(path).status_code, 404)
