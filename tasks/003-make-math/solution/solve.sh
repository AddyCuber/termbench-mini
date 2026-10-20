#!/usr/bin/env bash
set -euo pipefail

sed -i 's/$(CC) $(CFLAGS) -o $@ $^/$(CC) $(CFLAGS) -o $@ $^ -lm/' /work/Makefile