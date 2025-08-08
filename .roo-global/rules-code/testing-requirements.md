# Testing Requirements

Scope
Global testing philosophy for Code mode, adapted from [RULES.md](RULES.md) and [PLAN.md](PLAN.md). Python examples use pytest, but principles are language-agnostic.

Philosophy
- Test behavior, not implementation details.
- Prefer offline-friendly tests: avoid real network unless explicitly allowed.
- Focus on observable outputs and file system effects.
- Isolate side effects; stub or inject dependencies.

Test coverage focus
- Input→output fidelity for extractors and transformers.
- Network-bound features: discovery, enumeration, snapshotting (use stubs).
- CLI flags and defaults; end-to-end flows through the CLI entrypoint [lrn/cli.py](lrn/cli.py).
- Deterministic paths and encodings in emitted artifacts.

Fixtures and isolation
- Use temporary directories for file-system tests.
- Use isolated caches where applicable.
- Ensure UTF-8 encoding for all read/write operations.

Stubbing and doubles
- Replace network calls with fixtures or fakes; assert timeout and backoff handling via logs.
- Stub external converters (e.g., marker) to simulate success/failure without invoking binaries.

Logging expectations
- Assert concise [INFO] progress lines and [WARN] degradations.
- Example assertions reference emitted logs, not internal function calls.

Examples (pytest)
- Behavior-oriented:
  - See [python.test_cli_history_integration()](tests/test_cli_history_integration.py:1) for CLI flow patterns.
- Temp directories:
  - See [python.tmp_path usage](tests/test_extract_basic.py:1) for isolated output checks.
- Network stubbing:
  - See [python.test_history_discovery()](tests/test_history_discovery.py:1) showing discovery without live network.

CI considerations
- Keep tests deterministic; avoid reliance on wall clock or external services.
- Use seeded randomness if randomness is unavoidable.
- Emit minimal logs by default; enable verbose logs via flag when debugging.

Acceptance criteria
- Tests validate artifacts exist at stable paths with expected structures.
- No real network calls in default test run.
- Clear failure messages; quick to diagnose.