# Jeopardy game

The dbt project builds episode and question models from the season data in DuckDB.

The playable web draft is in [`game/`](game/README.md). For setup, game rules, phone access, and selecting a new episode, see the [game instructions](game/README.md).

Quick demo (no database dependency):

```bash
python3 game/server.py --demo
```

Then open http://localhost:8000.
