Welcome to your new dbt project!

### Using the starter project

Try running the following commands:
- dbt run
- dbt test


### Resources:
- Learn more about dbt [in the docs](https://docs.getdbt.com/docs/introduction)
- Check out [Discourse](https://discourse.getdbt.com/) for commonly asked questions and answers
- Join the [chat](https://community.getdbt.com/) on Slack for live discussions and support
- Find [dbt events](https://events.getdbt.com) near you
- Check out [the blog](https://blog.getdbt.com/) for the latest news on dbt's development and best practices

### Commands for local dev:
```
cd /Users/alecpeters/jepopardy-game
source .venv-dbt/bin/activate
cd dbt
```

### Daily production build

The workflow in [dbt-production.yml](../.github/workflows/dbt-production.yml) runs
`dbt build --project-dir dbt --target prod` every day at **12:00 noon Eastern**
(`America/New_York`, including daylight saving time). GitHub may queue scheduled
runs, so the actual start can be later than noon. This is a complete build of all
models, snapshots, seeds, and configured tests; it does not use `--full-refresh`.

The workflow uses Python 3.12 and the versions in `requirements.txt`, with a
separate CI profile in `ci/profiles.yml`. It reads the raw season tables from
`main` and builds models and snapshot history in `prod`. On the first run,
`ci/prepare_database.py` seeds missing production history from the existing
`main.jeopardy_episodes_history`, preserving previously selected episodes.
Subsequent runs leave production history intact. Database session dates use
Eastern time as well.

After a successful build, the workflow runs `python -m game.export_episode` to
export the production board as `game/published/episode.json`. It commits that JSON
and the root `jeopardy_seasons.duckdb` back to the default branch so the next run keeps the
updated snapshot history. Logs and dbt result artifacts are kept for 14 days;
a downloadable successful database is kept for 7 days. The bot needs permission
to push to the default branch, including any branch protection requirements.
No database credentials are needed for this local DuckDB file.

To enable the schedule, commit and push the workflow, `requirements.txt`, and
`ci/` files, along with the intended dbt model changes, to the repository's
default branch. You can also run it manually from **Actions → Daily production
dbt build → Run workflow**. Scheduled workflows use the default branch's code
and database, not uncommitted files on your laptop.

The game server downloads the published JSON from GitHub by default. Start it with
`python3 game/server.py`, then refresh or choose **Check for a new game** after a
successful build. No local database sync is necessary. The server retains the last
downloaded board for offline use. The workflow and JSON must first be pushed to
the default branch.

For local development, `game/.venv/bin/python game/server.py --local` reads
`prod.mrt_todays_episode_questions` from the database on your Mac. Use `--schema`
to select a different schema. GitHub builds do not directly modify your Mac's file.
