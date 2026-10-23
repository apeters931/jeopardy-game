"""Fetch the published board and retain a validated copy for offline play."""
import json
import logging
import tempfile
import threading
import time
from pathlib import Path
from urllib.request import Request, urlopen

DEFAULT_EPISODE_URL = 'https://raw.githubusercontent.com/apeters931/jepopardy-game/HEAD/game/published/episode.json'


def validate_episode(episode: dict) -> dict:
    if not isinstance(episode, dict) or not isinstance(episode.get('id'), str) or not episode['id']:
        raise ValueError('Published board has no episode ID.')
    time.strptime(episode['air_date'], '%Y-%m-%d')
    questions = episode.get('questions')
    if not isinstance(questions, list) or not questions:
        raise ValueError('Published board has no clues.')
    ids = set()
    for question in questions:
        if not isinstance(question, dict):
            raise ValueError('Published board has an invalid clue.')
        for field in ('id', 'round', 'category', 'question', 'answer'):
            if not isinstance(question.get(field), str):
                raise ValueError(f'Published clue has an invalid {field}.')
        if question['id'] in ids:
            raise ValueError('Published board has duplicate clue IDs.')
        ids.add(question['id'])
        if type(question.get('point_value')) is not int or type(question.get('is_daily_double')) is not bool:
            raise ValueError('Published clue has invalid scoring fields.')
    return episode


class RemoteEpisode:
    def __init__(self, url: str, cache_path: Path):
        self.url = url
        self.cache_path = cache_path
        self.cached = None
        self.lock = threading.Lock()
        try:
            self.cached = validate_episode(json.loads(cache_path.read_text()))
        except (OSError, ValueError, KeyError, TypeError):
            pass

    def __call__(self) -> dict:
        with self.lock:
            try:
                separator = '&' if '?' in self.url else '?'
                request = Request(f'{self.url}{separator}refresh={time.time_ns()}', headers={'Cache-Control': 'no-cache'})
                with urlopen(request, timeout=10) as response:
                    body = response.read(2_000_001)
                if len(body) > 2_000_000:
                    raise ValueError('Published board exceeds the size limit.')
                episode = validate_episode(json.loads(body))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                if self.cached is None:
                    raise ValueError(f'Could not download the board and no cached board is available: {exc}') from exc
                return {**self.cached, 'refresh_warning': 'GitHub could not be reached or returned an invalid board. Showing the last downloaded board; try again later.'}
            self.cached = episode
            temporary = None
            try:
                self.cache_path.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(mode='w', dir=self.cache_path.parent, delete=False) as handle:
                    temporary = Path(handle.name)
                    json.dump(episode, handle)
                temporary.replace(self.cache_path)
            except OSError as exc:
                logging.warning('Could not save the offline board: %s', exc)
                return {**episode, 'refresh_warning': 'The current board loaded, but its offline copy could not be saved.'}
            finally:
                if temporary is not None:
                    try:
                        temporary.unlink(missing_ok=True)
                    except OSError:
                        pass
            return episode
