"""Inventra as a Deep Agent.

All business logic lives in skills/*/SKILL.md and AGENTS.md.
Python only provides: the model, 3 thin tools (read SQL, write SQL, weather), and a CLI.
"""
import os
import re
import sqlite3
from pathlib import Path

import requests
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from deepagents import create_deep_agent, FilesystemPermission
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend

load_dotenv()
HERE = Path(__file__).parent
DB = HERE / "database" / "inventra.db"
CITIES = {"north": (28.70, 77.10), "south": (13.08, 80.27), "east": (22.57, 88.36),
          "west": (19.08, 72.88), "central": (23.26, 77.41)}


@tool
def query_db(sql: str) -> str:
    """Run ONE read-only SQL SELECT on the Inventra SQLite DB. Returns up to 200 rows, pipe-separated."""
    try:
        with sqlite3.connect(f"file:{DB}?mode=ro", uri=True) as con:
            cur = con.execute(sql)
            cols, rows = [d[0] for d in cur.description or []], cur.fetchmany(200)
        return "\n".join([" | ".join(cols)] + [" | ".join(map(str, r)) for r in rows]) if rows else "(no rows)"
    except Exception as e:
        return f"SQL error: {e}"


@tool
def write_db(sql: str) -> str:
    """Run ONE INSERT or UPDATE statement on the `tickets` or `forecasts` table only."""
    if not re.match(r"^\s*(INSERT\s+INTO|UPDATE)\s+(tickets|forecasts)\b", sql, re.I):
        return "Refused: only INSERT/UPDATE on tickets or forecasts is allowed."
    try:
        with sqlite3.connect(DB) as con:
            cur = con.execute(sql)
        return f"OK: {cur.rowcount} row(s) affected, last id {cur.lastrowid}"
    except Exception as e:
        return f"SQL error: {e}"


@tool
def get_weather(region: str) -> str:
    """5-day, 3-hourly weather forecast for an Indian region: north, south, east, west or central."""
    lat, lon = CITIES.get(region.lower(), CITIES["central"])
    try:
        r = requests.get("https://api.openweathermap.org/data/2.5/forecast", timeout=10, params={
            "lat": lat, "lon": lon, "units": "metric", "appid": os.environ["OPENWEATHER_API_KEY"]})
        r.raise_for_status()
        return "\n".join(f"{i['dt_txt']} | {i['main']['temp']}C | rain {i.get('rain', {}).get('3h', 0)}mm"
                         f" | hum {i['main']['humidity']}% | {i['weather'][0]['main']}" for i in r.json()["list"])
    except Exception as e:
        return f"WEATHER UNAVAILABLE ({type(e).__name__}). Do not invent a forecast."


model = init_chat_model(
    f"google_genai:{os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')}",
    api_key=os.getenv("GEMINI_API_KEY"),
    rate_limiter=InMemoryRateLimiter(requests_per_second=float(os.getenv("LLM_RPM", "4")) / 60),
)

agent = create_deep_agent(
    model=model,
    tools=[query_db, write_db, get_weather],
    # /app/ is the project folder on disk (skills + AGENTS.md); everything else is scratch space in state.
    backend=CompositeBackend(default=StateBackend(),
                             routes={"/app/": FilesystemBackend(root_dir=HERE, virtual_mode=True)}),
    skills=["/app/skills/"],
    memory=["/app/AGENTS.md"],
    permissions=[FilesystemPermission(operations=["write"], paths=["/app/**"], mode="deny")],
    checkpointer=InMemorySaver(),  # conversation memory per thread_id
)


def ask(question: str, thread_id: str = "cli") -> str:
    result = agent.invoke({"messages": [{"role": "user", "content": question}]},
                          {"configurable": {"thread_id": thread_id}})
    return result["messages"][-1].text


if __name__ == "__main__":
    print("INVENTRA (Deep Agent) - type 'quit' to exit\n")
    while (q := input("You: ").strip()).lower() not in {"quit", "exit", "q"}:
        if q:
            print(f"\nInventra: {ask(q)}\n")
