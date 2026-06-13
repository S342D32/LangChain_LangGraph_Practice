"""Research Agent - Standalone script for LangGraph deployment."""
from __future__ import annotations

import os
from datetime import datetime

from deepagents import create_deep_agent
from langchain_ollama import ChatOllama
from langgraph.checkpoint.postgres import PostgresSaver

from research_agent.prompts import (
    RESEARCHER_INSTRUCTIONS,
    RESEARCH_WORKFLOW_INSTRUCTIONS,
    SUBAGENT_DELEGATION_INSTRUCTIONS,
)
from research_agent.tools import (
    tavily_search,
    think_tool,
    get_database_schema,
    execute_database_query,
    analyze_data_for_updates,
    generate_image,
    generate_chart,
)

max_concurrent_research_units = 3
max_researcher_iterations = 3
current_date = datetime.now().strftime("%Y-%m-%d")

INSTRUCTIONS = (
    RESEARCH_WORKFLOW_INSTRUCTIONS
    + "\n\n"
    + "=" * 80
    + "\n\n"
    + SUBAGENT_DELEGATION_INSTRUCTIONS.format(
        max_concurrent_research_units=max_concurrent_research_units,
        max_researcher_iterations=max_researcher_iterations,
    )
)

research_sub_agent = {
    "name": "research-agent",
    "description": "Delegate research to the sub-agent researcher. Only give this researcher one topic at a time.",
    "system_prompt": RESEARCHER_INSTRUCTIONS.format(date=current_date),
    "tools": [tavily_search, think_tool, get_database_schema, execute_database_query, analyze_data_for_updates, generate_image, generate_chart],
}

model = ChatOllama(model="gemma4:31b-cloud", temperature=0.0)

agent = create_deep_agent(
    model=model,
    tools=[tavily_search, think_tool, get_database_schema, execute_database_query, analyze_data_for_updates, generate_image, generate_chart],
    system_prompt=INSTRUCTIONS,
    subagents=[research_sub_agent],
    interrupt_on={
        "execute_database_query": True,
        "analyze_data_for_updates": True,
    },
)
