# TypeScript Rules

Scope
Minimal, concrete TS rules aligned with repository principles in [RULES.md](RULES.md) and [PLAN.md](PLAN.md).

Compiler settings
- "strict": true (enables strictNullChecks, noImplicitAny, etc.)
- "noImplicitAny": true
- "noImplicitThis": true
- "alwaysStrict": true
- "noUncheckedIndexedAccess": true (prefer safer index access)
- "useUnknownInCatchVariables": true
- "target": "ES2020" (or newer when runtime allows)
- "module": "ESNext"
- "moduleResolution": "Bundler" or "NodeNext" depending on toolchain
- "esModuleInterop": true
- "resolveJsonModule": true
- "skipLibCheck": true (speed; revisit if library types are critical)
- "forceConsistentCasingInFileNames": true
- "exactOptionalPropertyTypes": true

Project structure
- Use src/ for sources and dist/ or build/ for outputs.
- Do not commit build artifacts.

Imports and ordering
- Order: standard libs, external deps, internal modules; blank line between groups.
- Prefer explicit, extension-less imports; avoid deep relative chains via baseUrl/paths.
- No default exports for large modules; named exports improve clarity.

Error handling and side effects
- Isolate side-effectful code (IO, network) from pure logic; inject dependencies for testability.
- Propagate errors with contextual messages; prefer Result-like patterns or typed errors where applicable.
- Log actionable info; avoid noisy console output in libraries.

Types and APIs
- Prefer explicit types on public functions and exported constants.
- Use readonly for immutable shapes.
- Narrow unknown via type guards.
- Avoid any; prefer unknown or proper generics.
- Model domain concepts with discriminated unions where useful.

Linting recommendations
- ESLint with:
  - @typescript-eslint/recommended
  - import/order for grouping and sorting
  - no-floating-promises to avoid unhandled async
  - consistent-type-imports for type-only imports
  - no-implicit-any-catch
- Prettier for formatting; keep formatting rules minimal and deterministic.

Testing
- Behavior-focused tests; decouple from implementation details.
- Stub network and time; use temporary directories or in-memory fs when relevant.
- Keep tests offline-friendly.

Examples
- Import ordering:
  - // Node stdlib
  - // Third-party
  - // Local modules
- Type-only imports:
  - See [typescript.import type](lrn/cli.py:1) style adapted for TS using import type Foo from "…".