dis Monorepo — Agent Execution Plan (structure only)

Intent: Create a uv-managed monorepo that ships multiple independent subpackages under a common umbrella distribution named dis, while avoiding stdlib dis import conflicts by using a distinct import namespace (e.g., disx). This plan omits concrete file contents; it lists tasks with inputs/outputs so agents can generate files and folders themselves.

0) Naming & Namespace Decision

Input: Umbrella name = dis; initial subpackages = frame_property_labeler, resource_monitor.

Actions: Use dis as published umbrella dist, disx as import namespace.

Output: Decision doc in repo.

1) Repository Bootstrap

Create git repo.

Add packages/, meta/, .gitignore.

2) Root Development Environment

Add root pyproject.toml with local path deps + dev group.

Run uv sync → produce uv.lock.

3) Subpackage Scaffolding

For each (frame_property_labeler, resource_monitor):

Folder: packages/<name>/src/disx/<name>/

pyproject.toml with metadata, runtime deps, setuptools config.

README.md with purpose/API sketch.

4) Umbrella Distribution

Under meta/dis/, add pyproject.toml that depends on all subpackages.

Optional groups (vision/ops/etc).

5) Continuous Integration

CI workflow:

checkout

install uv

uv sync

lint → ruff

typecheck → mypy

test → pytest

6) Pre-commit (optional)

.pre-commit-config.yaml with ruff + mypy.

Enforce formatting/lint on commit.

7) Private Index Publishing Flow

Build wheels for subpackages → upload to private index.

Build/upload umbrella.

Document teammate install command with uv pip install dis.

8) Versioning & Release Policy

Subpackages: semver, independent.

Umbrella: declare compatible ranges.

Use prereleases (rc) for staging.

9) New Subpackage Workflow

Scaffold packages/<new_pkg>/src/disx/<new_pkg>/.

Add pyproject, add path dep to root, uv sync.

Publish wheel, update umbrella.

10) Optional Plugin Discovery

Define entry points group (e.g., disx.plugins).

Each subpackage registers register().

Loader in consumer app iterates plugins.

11) Documentation Stubs

docs/: Overview, Repo Layout, Dev Guide (uv), Release Process, Index Setup, Namespace rationale.

12) Environment Readiness Checklist

Python ≥ 3.10 installed.

uv installed.

Private index credentials configured.

Editors aware of PEP 420 + src/ layout.

13) Agent Runbook (condensed)

Bootstrap repo (Section 1).

Root pyproject with path deps (Section 2).

Scaffold subpackages (Section 3).

Umbrella dist (Section 4).

uv sync and verify imports.

Add CI/pre-commit (Sections 5–6).

Build/publish subpackages + umbrella (Section 7).

Document install + version policy (Sections 7–8).

For new packages: Section 9.

(Optional) Plugin discovery (Section 10).