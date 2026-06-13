# TODO - deep_research Postgres checkpointer

- [x] Inspect current agent.py (done)
- [x] Implement langgraph-checkpoint-postgres usage in agent.py with sync PostgresSaver
- [x] Wire the checkpointer into create_deep_agent (or underlying LangGraph compilation) so runtime loads synchronously
- [x] Support DATABASE_URI (prefer) falling back to POSTGRES_URI
- [x] Add safe error handling if neither URI is set

- [x] Run any available lint/test or a quick import check for the example



