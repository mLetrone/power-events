# Changelog
All notable changes to this project will be documented in this file.

## Power-events

## 2.0.0 (2026-06-09)

### :sparkles: Features

- add routers
- add event converter
- **BREAKING:**
  - end of support for python <3.11
  - `EventResolver` constructor parameter can only be passed by keyword.

### :zap: Performance

- run routes in parallel

### build

- **deps**: bump ruff from 0.15.2 to 0.15.15
- **deps**: bump mike from 2.1.3 to 2.2.0
- upgrading python version

### docs

- add event_converter and routers

## 1.2.0 (2025-11-10)

### :wrench: configuration

- support python 3.14

## 1.1.0 (2024-12-12)

### :recycle: Refactoring

- ValuePath use `get_from` instead of `get`

### :sparkles: Features

- add fallback route
- add exception handling

## 1.0.0 (2024-11-24)

### :sparkles: Features

- change ValuePath
- raise error when value missing
- allow equals at None
- add resolver
- add conditions
