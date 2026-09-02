# MarketPlace Agentic AI

An agentic AI system for marketplace workflows.

> **Status:** Early scaffold. This repository is currently being set up — the sections
> below are placeholders to be filled in as the project takes shape.

## Overview

_Describe what the project does: the marketplace it targets, the agents involved,
and the problems they automate._

## Getting Started

### Prerequisites

_List runtime and tooling requirements (language version, package manager, etc.)._

### Installation

```bash
git clone git@github.com:AdityaOnam/MarketPlace_Agentic_AI.git
cd MarketPlace_Agentic_AI
```

### Configuration

_Document required environment variables and API keys here. Never commit secrets._

### Running

_Add the command(s) to run the project._

## Project Structure

```
.
├── .claude/
│   └── skills/
│       ├── round3-spec/     # canonical Round 3 task context (spec, schema, rubric)
│       └── project-flow/    # session rituals, phase plan, invariants
├── docs/
│   ├── round3-handout.pdf   # source of truth for the task
│   ├── PROGRESS.md          # current phase / done / next / blocked
│   ├── DECISIONS.md         # append-only decision log
│   └── RESEARCH.md          # mechanism-anchored signals (Phase 1)
└── README.md
```

> Note: the root `README.md` **of the submitted marketplace** is a separate file that
> will live at the marketplace root, describing each skill and how the entrypoint
> composes them (required by the handout). This file is the repository README.

## Working with Claude Code

This repository includes skills under [`.claude/skills/`](.claude/skills/) that give
Claude Code project-specific context and workflows. See the
[skills README](.claude/skills/README.md) for details on adding your own.

## License

_Add a license._
