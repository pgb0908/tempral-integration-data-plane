# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

This repository is in its initial state. The only file is a PyCharm-generated `main.py` placeholder. No dependencies, build system, or architecture have been established yet.

## Intended Purpose

Based on the repository name (`tempral-integration-data-plane`), this project is intended to implement a **Temporal integration data plane** — likely a service or worker that integrates with the [Temporal](https://temporal.io/) workflow orchestration platform.

## Setup (once dependencies are added)

When a `requirements.txt` or `pyproject.toml` is added, install dependencies with:

```bash
pip install -r requirements.txt
# or
pip install -e .
```

## Running

```bash
python main.py
```
