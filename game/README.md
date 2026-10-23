# The Daily Board

A local, responsive Jeopardy game that downloads the selected episode published by this repository's GitHub Action. Each successful production build exports `prod.mrt_todays_episode_questions` to `game/published/episode.json` and commits it alongside the database.

## Play the published board

Run from the repository root:

```bash
python3 game/server.py
```

Open **http://localhost:8000**. The default mode needs only Python's standard library, with internet access for the first download. Refreshing the page or choosing **Check for a new game** fetches the published JSON; no database sync or server restart is needed after a new build. GitHub may briefly cache published content.

The last successfully downloaded board is saved in `game/.cache/episode.json`. If a download fails, the server serves that cached board with a visible message. It preserves your browser progress. If no cached board exists, the page shows a retryable error. An updated board is adopted only when you request it, so an active game is not interrupted.

The workflow, exporter, and initial `game/published/episode.json` must be committed and pushed to GitHub before the default download URL works. Run the workflow manually or wait for its daily schedule to publish subsequent boards. Rebuilding on the same day intentionally retains that day's episode.

Override the published URL or cache location with `--episode-url URL` or `--cache PATH`.

## Play from your local database

Local mode continues to read the DuckDB file on your Mac:

```bash
python3 -m venv game/.venv
game/.venv/bin/python -m pip install -r game/requirements.txt
game/.venv/bin/python game/server.py --local
```

It reads `prod.mrt_todays_episode_questions` on each request and closes the connection afterward. Use `--schema main` or `--schema dev` for another dbt target. An explicit database path also enables local mode:

```bash
game/.venv/bin/python game/server.py --db /absolute/path/to/database.duckdb --port 8001
```

The default database path is resolved from the server's location. Local mode requires DuckDB 2.0 or newer. Close DuckDB sessions that hold an incompatible file lock if the database cannot be opened.

To build a local board using your working dbt environment:

```bash
cd dbt
/path/to/your/dbt build --target prod --select +mrt_todays_episode_questions
```

To export the current production board manually, run from the repository root:

```bash
game/.venv/bin/python -m game.export_episode
```

The game never runs dbt or selects an episode automatically.

## Try the interface without a database

```bash
python3 game/server.py --demo
```

The page explicitly says **DEMO BOARD**. Sample clues intentionally repeat across point values for exercising the flow. Demo mode requires no third-party Python packages. It never silently replaces a failed real-data connection.

## Play on your phone

Start the server with:

```bash
game/.venv/bin/python game/server.py --host 0.0.0.0
```

Connect your phone to the same Wi-Fi and open `http://YOUR_MAC_WIFI_IP:8000`. Find that IP in macOS System Settings → Wi-Fi → Details → TCP/IP. Allow incoming connections if macOS asks. Phone and desktop progress are separate.

## Game behavior

- The original episode air date appears at the top. The game sits in a narrow, centered column over a dark star-and-grid background. Each regular round keeps a two-column, three-row category grid on both laptops and phones.
- Click a category to open its point values in a centered overlay without resizing the board. Close it with “Back to categories”, Escape, or a click outside the overlay. Played slots keep their blue background, with the text hidden and selection disabled.
- Correct answers add the clue value; incorrect answers subtract it; “No answer” makes no score change.
- Daily Doubles reveal a wager screen before the clue. The maximum is your score or the round's highest clue value, whichever is greater. Wagers are whole numbers starting at 1. You cannot pass; submitting a blank response loses the wager.
- Use “Check for a new game” after finishing to download the published episode without restarting the server (or reread the database in local mode). If no new episode is available, the game tells you and keeps your results.
- Finish each round to advance. Final Jeopardy, if present, has its own category and a wager from 0 to your positive score; a nonpositive score allows a 0 wager.
- The matcher ignores case, punctuation, accents, leading articles, and standard “What is…”/“Who is…” phrasing. It uses exact normalized text, not AI or fuzzy substring matching. The reveal screen shows only the correct response and a back button inside the board, with the header and score outside it.
- Progress and score are saved in browser storage for this episode's content. Refreshing resumes answered clues; changing the episode starts a new board.

## Data mapping

The mart supplies `question_id`, `air_date`, `round`, `category`, `point_value`, `question`, `answer`, and `is_daily_double`. The existing dataset follows Jeopardy's terminology: `answer` contains the clue to display, and `question` contains the expected player response. The server explicitly swaps these into the UI's clue/response fields without modifying dbt. If you rename those columns upstream, adjust `load_episode()` accordingly.

Each question ID must be unique within the episode. Regular rounds use the source point values, including Daily Double positions. Rounds `1`, `2`, and `3` display as Jeopardy, Double Jeopardy, and Final Jeopardy. Text round names are also supported.

This is a single-player local draft. Answers are delivered to the browser, scores can be corrected by the player, and there is no account, shared leaderboard, or server-side anti-cheat. Browser state does not track which episodes dbt has selected. It has not been published to external hosting; the local DuckDB file stays on your computer. Google Fonts are optional; system fonts work offline.

## Verification

```bash
node --test game/tests/logic.test.mjs
game/.venv/bin/python -m unittest discover -s game/tests
node --check game/static/app.js
```

Tests cover answer normalization, scoring and passes, wager bounds, round ordering, data field mapping, production schema selection, updated database reads, JSON export, remote updates, validation, and offline recovery.
