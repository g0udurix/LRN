# Multitasking Strategy Diagrams

Visual guides for coordinating the parallel governance, corpus, and persistence streams.

## System Overview
```mermaid
flowchart TD
    A[Strategist] --> B[Branch Prep: chore/runner-cli]
    A --> C[Branch Prep: feat/manifest-expansion]
    A --> D[Branch Prep: feat/history-persist]
    B --> E[Governance Runner]
    C --> F[Corpus Wrangler]
    D --> G[Persistence Architect]
    E --> H[Runner CLI + .github updates]
    F --> I[Manifest + Headless Runs]
    G --> J[Persistence Module + Tests]
    H --> K[Docs & Project Board]
    I --> K
    J --> K
    K --> L[Daily Stand-up in chat.md]
    L --> M[48h Sync Review]
```

## Swimlane Workflow
```mermaid
sequenceDiagram
    participant Strat as Strategist
    participant Gov as Governance Runner
    participant Corp as Corpus Wrangler
    participant Persist as Persistence Architect
    Strat->>Strat: Fetch master & refresh PAT reminder
    Strat->>Strat: Create feature branches
    Strat->>Gov: Handoff branch + checklist
    Strat->>Corp: Share manifests + headless targets
    Strat->>Persist: Deliver persistence scope
    loop Daily Stand-up
        Gov->>Strat: Report CLI progress & tests
        Corp->>Strat: Report ingestion runs & logs
        Persist->>Strat: Report schema/tests status
        Strat->>All: Adjust plan / highlight blockers
    end
    Gov->>Strat: Governance artifacts ready
    Corp->>Persist: Provide updated fixtures
    Persist->>Strat: Persistence suite complete
    Strat->>All: Prepare PR summaries & final tests
```

## Timeline
```mermaid
gantt
    title Parallel Stream Timeline
    dateFormat  YYYY-MM-DD
    section Prep
    PAT Refresh & Branch Carve         :a1, 2025-09-18, 1d
    section Governance
    Runner CLI Scaffold                :b1, after a1, 2d
    CI/Docs Update                     :b2, after b1, 1d
    section Corpus
    Manifest QA & Headless Captures    :c1, after a1, 2d
    Ingestion Logs & Issue Updates     :c2, after c1, 1d
    section Persistence
    Schema Draft & Fixtures            :d1, after c2, 2d
    Integration Tests & Docs           :d2, after d1, 2d
    section Wrap
    Full Pytest + PR Packaging         :e1, after b2, c2, d2, 1d
```

## Dependency Matrix
```mermaid
erDiagram
    STRATEGIST ||--|{ GOVERNANCE_RUNNER : briefs
    STRATEGIST ||--|{ CORPUS_WRANGLER : briefs
    STRATEGIST ||--|{ PERSISTENCE_ARCHITECT : briefs
    GOVERNANCE_RUNNER ||--|| GOVERNANCE_ARTIFACT : produces
    CORPUS_WRANGLER ||--|| MANIFEST_FIXTURES : produces
    PERSISTENCE_ARCHITECT ||--|| PERSISTENCE_SCHEMA : produces
    MANIFEST_FIXTURES ||--|| PERSISTENCE_SCHEMA : supports
    GOVERNANCE_ARTIFACT ||--|| PERSISTENCE_SCHEMA : configures
    GOVERNANCE_ARTIFACT ||--|| PROJECT_BOARD : updates
    MANIFEST_FIXTURES ||--|| PROJECT_BOARD : informs
```

## Status Flow
```mermaid
stateDiagram-v2
    [*] --> Prep
    Prep --> Governance
    Prep --> Corpus
    Prep --> Persistence
    Governance --> Validation
    Corpus --> Validation
    Persistence --> Validation
    Validation --> Wrap
    Wrap --> [*]
    Validation --> Blocked : if any stream reports blocker
    Blocked --> StratReview
    StratReview --> Prep : replan and restart
```

## Agent Class Model
```mermaid
classDiagram
    class Strategist {
        +plan_cycle()
        +assign_agents()
        +log_status()
    }
    class GovernanceRunner {
        +scaffold_runner()
        +sync_workflows()
        +run_cli_tests()
    }
    class CorpusWrangler {
        +validate_manifests()
        +headless_capture()
        +ingest_corpus()
    }
    class PersistenceArchitect {
        +design_schema()
        +write_integration_tests()
        +update_docs()
    }
    Strategist --> GovernanceRunner : dispatches
    Strategist --> CorpusWrangler : dispatches
    Strategist --> PersistenceArchitect : dispatches
    GovernanceRunner --> PersistenceArchitect : provides configuration
    CorpusWrangler --> PersistenceArchitect : provides fixtures
```

## Git Branch Plan
```mermaid
gitGraph TD
    commit id: "master" tag: "baseline"
    branch chore/runner-cli
    checkout chore/runner-cli
    commit id: "runner-scaffold"
    commit id: "runner-tests"
    checkout master
    branch feat/manifest-expansion
    checkout feat/manifest-expansion
    commit id: "manifest-updates"
    commit id: "headless-logging"
    checkout master
    branch feat/history-persist
    checkout feat/history-persist
    commit id: "schema-draft"
    commit id: "integration-tests"
    checkout master
    merge chore/runner-cli
    merge feat/manifest-expansion
    merge feat/history-persist
    commit id: "parallel-complete" tag: "release"
```

