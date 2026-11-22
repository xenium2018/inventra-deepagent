# Inventra — Deep Agent + Skills edition

The same Inventra assistant, rebuilt on **LangChain Deep Agents**. The business logic
(intent routing, SQL, reorder formula, vendor ranking, weather reasoning, ticket rules,
response formats) now lives in **Markdown skills** instead of Python.

```
inventra-deepagent/
├── agent.py        # ~100 lines: model + 3 thin tools + create_deep_agent + CLI
├── app.py          # ~25 lines: Streamlit chat UI
├── AGENTS.md       # always-loaded memory: persona, DB schema, data conventions, output style
├── skills/
│   ├── inventory-status/SKILL.md
│   ├── sales-analysis/SKILL.md
│   ├── financial-report/SKILL.md
│   ├── reorder-recommendation/SKILL.md
│   ├── sales-opportunity/SKILL.md
│   ├── vendor-selection/SKILL.md
│   └── ticket-management/SKILL.md
└── database/       # inventra.db + schema.sql + CSVs (unchanged)
```

## Run
```bash
pip install -r requirements.txt
cp .env.example .env        # add GEMINI_API_KEY and OPENWEATHER_API_KEY
python agent.py             # CLI
streamlit run app.py        # web UI
```

## How it works
1. `AGENTS.md` is injected into every prompt (memory).
2. Only each skill's `name` + `description` is in the prompt. When a question matches, the agent
   reads that `SKILL.md` with `read_file` (progressive disclosure) and follows its steps.
3. Skills call three tools:
   - `query_db` — read-only SQL (database opened in `mode=ro`)
   - `write_db` — INSERT/UPDATE on `tickets` and `forecasts` only
   - `get_weather` — OpenWeatherMap 5-day forecast per region
4. The project folder is mounted at `/app/` read-only for the agent (it can't edit its own skills);
   all other file paths are scratch space in agent state.
5. Conversation memory = LangGraph `InMemorySaver` keyed by `thread_id`.

## Old → new mapping
| Old Python | Now |
|---|---|
| `coordinator.py` (classify → gather → decide → respond graph) | Deep Agent picks a skill from its description |
| `report_agent.py`, `data_pipeline.py`, `tools/finance.py` | SQL in `inventory-status`, `sales-analysis`, `financial-report` |
| `decision_agent.py` prompts | `reorder-recommendation`, `sales-opportunity`, `vendor-selection` |
| `ticket_manager.py` | `ticket-management` |
| `memory_manager.py` (conversations, forecasts) | checkpointer + `INSERT INTO forecasts` step in a skill |
| `tools/weather.py` | `get_weather` tool |

## Add a new capability
Create `skills/<name>/SKILL.md` with `name` and `description` frontmatter and the steps.
No Python changes needed.

## Optional upgrades
- Human approval for DB writes: add `interrupt_on={"write_db": True}` to `create_deep_agent`
  (then resume with `Command(resume=...)` in the CLI/UI).
- Persistent chat memory: swap `InMemorySaver` for `SqliteSaver`.
- LangSmith tracing: set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` in `.env`.
