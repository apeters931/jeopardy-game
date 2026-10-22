# The Daily Board

A local, responsive Jeopardy game powered by `main.mrt_todays_episode_questions` in your project's DuckDB database. It reads the database once at startup, closes the connection, and serves that episode until restarted. It never runs dbt or selects a new episode automatically.

## Start with your real episode

Run from the repository root:

```bash
cd /Users/alecpeters/jepopardy-game
python3 -m venv game/.venv
game/.venv/bin/python -m pip install -r game/requirements.txt
game/.venv/bin/python game/server.py
```

Open **http://localhost:8000** in your browser. Stop with **Ctrl+C**. After the first setup, only the last command is necessary. The separate game environment avoids changing your dbt dependencies. This database requires DuckDB 2.0 or newer; the server's Python package is separate from the DuckDB CLI.

The default database path is resolved from the server's location, so it works even if your terminal is in a different folder. Override it with:

```bash
game/.venv/bin/python game/server.py --db /absolute/path/to/database.duckdb --port 8001
```

If the mart has not been built yet, use your working dbt environment to run:

```bash
cd dbt
/path/to/your/dbt run --select +mrt_todays_episode_questions
```

This includes the episode-selection model and can select a **new** episode. To rebuild only the questions for the currently selected episode, omit the `+`. Rebuilding the episode does not record it in your dbt snapshot automatically; run `dbt snapshot --select jeopardy_episodes_history` separately if you want to record the selection. Stop/restart the game server after changing the data. Close any DuckDB terminal session that holds an incompatible file lock if the server cannot open the database.

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

Tests cover answer normalization, scoring and passes, wager bounds, round ordering, data field mapping, and missing/empty/multiple-episode database handling.
