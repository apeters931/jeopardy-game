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

After a successful build, the workflow commits only the root
`jeopardy_seasons.duckdb` back to the default branch so the next run keeps the
updated snapshot history. Logs and dbt result artifacts are kept for 14 days;
a downloadable successful database is kept for 7 days. The bot needs permission
to push to the default branch, including any branch protection requirements.
No database credentials are needed for this local DuckDB file.

To enable the schedule, commit and push the workflow, `requirements.txt`, and
`ci/` files, along with the intended dbt model changes, to the repository's
default branch. You can also run it manually from **Actions → Daily production
dbt build → Run workflow**. Scheduled workflows use the default branch's code
and database, not uncommitted files on your laptop.

The workflow updates the database on GitHub. To use that data locally, pull the
new database once your working tree is ready and restart the game server. The
game currently reads `main.mrt_todays_episode_questions`; serving the production
build requires switching that query to `prod.mrt_todays_episode_questions`.
