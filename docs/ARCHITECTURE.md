# InsightForge AI — Architecture

```text
                    ┌─────────────────────┐
                    │       React UI      │
                    │ Upload + Chat + UI  │
                    └──────────┬──────────┘
                               │ REST
                    ┌──────────▼──────────┐
                    │       FastAPI       │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
      Dataset Profiler    AI Analyst       Safe Executor
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                    Result + Chart Spec
                               │
                               ▼
                         React Charts
```

The critical security boundary is the execution layer. LLM-generated analysis must be validated and restricted before any code is executed.
