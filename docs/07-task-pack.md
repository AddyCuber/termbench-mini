# 07 — Task pack

## What this is

The task pack is a collection of ten small broken-machine scenarios. Each task has an image build context, a human-only reference solution, and a verifier that checks the outcome rather than the commands used.

## How data flows

1. `task.yaml` gives the model the prompt and execution limits while keeping human notes separate.
2. Docker builds only from `environment/`, so tests and solutions cannot leak into the model image.
3. The validator runs untouched and solved containers three times, then checks prompt leaks, image hygiene, and network isolation.
4. Only tasks passing all seven checks should be included in model batches.

The current ten tasks cover web serving, shell quoting, C linking, SSH configuration, file permissions, symlinks, service settings, archive restore, JSON configuration, and log rotation.

## Three questions you should be able to answer

1. Why must a task fail before its reference solution is copied in?
2. Which task files are human-only and how is that enforced?
3. What evidence is required before a task is fair to include in a model batch?