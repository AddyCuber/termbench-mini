# 05 — Batch and report

## What this is

The batch command repeats validated task attempts and saves machine-readable results. The report command turns those results into a small Markdown summary.

## How data flows

1. `termbench batch` resolves `--tasks all` or a comma-separated task list and builds each task image.
2. Each attempt gets a new `Sandbox`; the agent trace is stored under the run directory and hidden tests run after the model stops.
3. `results.json` is written after every attempt, so completed work remains available if a later attempt fails.
4. `--max-total-tokens` stops scheduling new attempts after the accumulated input and output usage reaches the guard.
5. `termbench report runs/<run_id>/results.json` writes `report.md` with pass counts, median steps, and tasks needing review.

## Three questions you should be able to answer

1. Why does each attempt use a fresh sandbox?
2. Which token fields are used by the total-token guard?
3. Why are 0-pass runs and all-pass runs with at least five attempts flagged?