"""Export the production episode in the same format served to the game."""
import argparse
import json
from pathlib import Path

from game.remote_episode import validate_episode
from game.server import DEFAULT_DB, load_episode


def export_episode(db_path: Path, output: Path, schema: str = 'prod') -> None:
    episode = validate_episode(load_episode(db_path, schema))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(episode, ensure_ascii=False, indent=2) + '\n')
    print(f'Exported {episode["air_date"]}: {len(episode["questions"])} clues to {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--schema', default='prod')
    parser.add_argument('--output', type=Path, default=Path('game/published/episode.json'))
    args = parser.parse_args()
    export_episode(args.db, args.output, args.schema)
