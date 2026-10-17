import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

PLANNER_PROMPT = """You are a project planner for a multi-agent coding system.
The following two coding agents are available: {agents}.

Split the user's project goal into 2 independent workstreams (one per agent, in the given
order) that can be built in parallel WITHOUT touching the same files. Clearly divide file
ownership (e.g. the first agent owns frontend/, the second owns backend/).

Respond with ONLY a JSON object:
{{
  "project": "<short project name, kebab-case>",
  "tasks": [
    {{
      "agent": "{agent1}",
      "name": "<kebab-case task name>",
      "summary": "<one line>",
      "prompt": "<detailed self-contained instructions: what to build, exact files/folders it owns, tech stack, and an explicit list of paths it must NOT touch>",
      "paths": ["frontend/"]
    }},
    {{
      "agent": "{agent2}",
      "name": "<kebab-case task name>",
      "summary": "<one line>",
      "prompt": "<...>",
      "paths": ["backend/"]
    }}
  ]
}}

Rules:
- Exactly 2 tasks, one per agent, preserving the agent order given.
- Each prompt must be fully standalone (agents cannot see each other).
- Each prompt must state: shared interface contract (API endpoints / types) so the halves fit together.
- Keep prompts under 250 words each."""


def get_client() -> OpenAI:
    """Create an OpenAI client using Zen API credentials."""
    key = os.environ.get("ZEN_API_KEY")
    if not key:
        raise RuntimeError(
            "ZEN_API_KEY not found in .env. "
            "Get a free key at https://opencode.ai/zen or set it in your .env file."
        )
    base_url = os.environ.get("ZEN_BASE_URL", "https://opencode.ai/zen/v1")
    return OpenAI(api_key=key, base_url=base_url)


def plan(goal: str, agents: list[str] | None = None) -> dict:
    """Use LLM to split a project goal into 2 parallel workstreams."""
    agents = agents or ["codex", "opencode"]
    if len(agents) < 2:
        raise ValueError("At least 2 agents required for parallel execution")

    prompt = PLANNER_PROMPT.format(
        agents=" and ".join(agents),
        agent1=agents[0],
        agent2=agents[1],
    )
    client = get_client()
    raw = None
    last_error = None

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=os.environ.get("ZEN_MODEL", "nemotron-3-ultra-free"),
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Project goal: {goal}\n\nAgent order: {agents[0]} first, {agents[1]} second."},
                ],
                temperature=0.2,
                max_tokens=1500,
            )
            if response.choices[0].message.content:
                raw = response.choices[0].message.content
                break
            last_error = RuntimeError("Planner returned empty response")
        except Exception as e:
            last_error = e

    if raw is None:
        raise RuntimeError(
            f"Planner failed after 3 attempts: {last_error}. "
            "Check your ZEN_API_KEY and network connection."
        )

    start, end = raw.find("{"), raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise RuntimeError(f"Planner returned non-JSON response: {raw[:200]}...")

    try:
        plan_data = json.loads(raw[start:end])
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Planner returned invalid JSON: {e}")

    tasks = plan_data.get("tasks", [])
    if len(tasks) != 2:
        raise RuntimeError(
            f"Planner must return exactly 2 tasks, got {len(tasks)}. "
            "Try rephrasing your goal to be more specific."
        )

    return plan_data
