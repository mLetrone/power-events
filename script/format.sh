#!/usr/bin/env bash
set -x

ruff check power_events tests script --fix
ruff format power_events tests script
