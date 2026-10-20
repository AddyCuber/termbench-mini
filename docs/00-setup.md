# 00 — Setup

## What this is

termbench-mini is a Python 3.12 package (`src/termbench/`) plus a `scripts/` folder. Milestone 0 only checks that your machine has Docker, Python, and (optionally) an Anthropic API key. Nothing talks to a model yet.

## How data flows

1. You run `bash scripts/check_env.sh` from the repo root (or any cwd; it does not need files besides the tools on PATH).
2. The script asks Docker and Python for their versions and checks whether the environment variable `ANTHROPIC_API_KEY` is non-empty.
3. It prints three lines and exits 0. It never prints the key. Missing key is reported as `not set` and is still a clean exit — later milestones need the key for `run`/`batch`, not for setup.

`pyproject.toml` lists `pyyaml` and `anthropic`. Traces go under `runs/` (gitignored). Secrets belong in `.env` (also gitignored), not in the repo.

## Three questions you should be able to answer

1. Why does `check_env.sh` still succeed when `ANTHROPIC_API_KEY` is missing?
2. Which two paths must stay out of git, and why?
3. Where does the installable package live on disk (`src/` layout), and which Python version is required?
