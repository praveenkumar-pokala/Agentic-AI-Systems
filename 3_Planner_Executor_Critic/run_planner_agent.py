import os, sys, re, json, requests, textwrap
from typing import Dict, Callable, List
from openai import OpenAI

# ---------- Environment / Setup ----------

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY in environment.")

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "<PUT_YOUR_KEY_HERE>")
client = OpenAI(api_key=OPENAI_API_KEY)

WIKI_HEADERS = {"User-Agent": "planner-executor-critic-demo/1.0"}

# ---------- Tools ----------

def wikipedia_summary(topic: str) -> str:
    """
    Wikipedia REST /page/summary/{title} gives a concise factual summary
    for entities like cities and companies, commonly used for programmatic context.
    """
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic}"
    r = requests.get(url, headers=WIKI_HEADERS, timeout=10)
    if r.status_code != 200:
        return f"[wiki] error {r.status_code}: {r.text[:200]}"
    d = r.json()
    return f"{d.get('title','')} — {d.get('description','')}\n{d.get('extract','')}"

def weather_brief(latlon: str) -> str:
    """
    OpenWeather 'current weather' endpoint returns live conditions for given lat/lon
    (temp, description). Requires API key, free tier available.
    """
    if OPENWEATHER_API_KEY.startswith("<PUT_"):
        return "[weather] Please set OPENWEATHER_API_KEY."
    try:
        lat, lon = [float(x.strip()) for x in latlon.split(",")]
    except Exception as e:
        return f"[weather] bad lat/lon input: {latlon} ({e})"
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY}
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        return f"[weather] error {r.status_code}: {r.text[:200]}"
    d = r.json()
    def k2c(k): return round(k - 273.15, 1)
    desc = d["weather"][0]["description"]
    temp_c = k2c(d["main"]["temp"])
    return f"{desc}, {temp_c}°C"

def corporate_hotel(city: str) -> str:
    """
    Internal policy hook. In real life, this would talk to travel policy DB.
    Here we hardcode Hyderabad as corporate-approved.
    """
    if city.lower() == "hyderabad":
        return (
            "MetroLink Executive Suites (~₹5400/night). "
            "Walkable to Hitech City offices. Breakfast+gym included. "
            "Policy-approved for business stays."
        )
    return "No approved hotel found for this city."

TOOLS: Dict[str, Callable[[str], str]] = {
    "wikipedia_summary": wikipedia_summary,
    "weather_brief": weather_brief,
    "corporate_hotel": corporate_hotel,
}

# ---------- Helper: call OpenAI ----------

def call_model(system_prompt: str, user_prompt: str) -> str:
    """
    Unified call helper for OpenAI reasoning model (o4-mini).
    o4-mini is optimized for stepwise reasoning, planning, and tool-use flows.
    """
    resp = client.responses.create(
        model="o4-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    # Try Responses API .output_text first
    if hasattr(resp, "output_text"):
        return resp.output_text
    # Fallbacks
    try:
        return resp.choices[0].message.content
    except Exception:
        if hasattr(resp, "output"):
            if isinstance(resp.output, list):
                return "\n".join(str(x) for x in resp.output)
            return str(resp.output)
        return str(resp)

# ---------- 1. PLANNER ----------

SYSTEM_PLANNER = """
You are a planning agent.
Break the high-level GOAL into a short numbered plan (3-6 steps).
Each step must be concrete, observable, and something we can attempt with tools.

Your output format MUST be:

PLAN:
1. ...
2. ...
3. ...
4. ...

Do not add anything else.
"""

def make_plan(goal: str) -> List[str]:
    plan_text = call_model(
        SYSTEM_PLANNER,
        f"GOAL:\n{goal}\n\nCreate the PLAN now."
    )
    # Extract numbered steps after "PLAN:"
    steps = []
    in_plan = False
    for line in plan_text.splitlines():
        line = line.strip()
        if line.upper().startswith("PLAN"):
            in_plan = True
            continue
        if in_plan:
            m = re.match(r"^\d+\.\s*(.+)$", line)
            if m:
                steps.append(m.group(1).strip())
    return steps

# ---------- 2. EXECUTOR (per step) ----------

SYSTEM_EXECUTOR = """
You are an execution agent with tool access.

TOOLS you MAY REQUEST:
1. wikipedia_summary(topic: str)
   - factual summary for a city / company / concept.
2. weather_brief(lat,lon as string \"LAT,LON\")
   - live weather snapshot for planning travel.
3. corporate_hotel(city: str)
   - corporate-approved hotel guidance.

Protocol:
- Think out loud using Thought: ...
- If you need a tool, respond with:
  Action: <tool_name>
  Action Input: <argument>
- After I run that tool, I will give you:
  Observation: <tool_result>
  Then you continue.
- When done with THIS STEP ONLY, respond with:
  Final Answer: <concise result for this step>

Rules:
- Stay focused ONLY on the given step description, not the whole mission.
- If you already know the answer, skip the tool call.
"""

ACTION_RE = re.compile(
    r"Action:\s*(?P<tool>\w+)\s*[\r\n]+Action Input:\s*(?P<input>.+)",
    re.I
)
FINAL_RE = re.compile(
    r"Final Answer:\s*(?P<final>.*)",
    re.I | re.S
)

def interpret_executor_output(text: str):
    # final?
    m_final = FINAL_RE.search(text)
    if m_final:
        return {"type":"final","answer":m_final.group("final").strip(),"raw":text}
    # action?
    m_act = ACTION_RE.search(text)
    if m_act:
        return {
            "type":"action",
            "tool":m_act.group("tool").strip(),
            "input":m_act.group("input").strip(),
            "raw":text,
        }
    # fallback
    return {"type":"final","answer":text.strip(),"raw":text}

def execute_step(step_desc: str) -> dict:
    """
    Run a ReAct-like loop for ONE step in the plan.
    The agent can call tools multiple times until it returns Final Answer for that step.
    """
    trace = ""
    step_result = None

    for _ in range(5):
        llm_out = call_model(
            SYSTEM_EXECUTOR,
            f"STEP DESCRIPTION:\n{step_desc}\n\nTRACE SO FAR:\n{trace}\n\nFollow the protocol."
        )
        decision = interpret_executor_output(llm_out)
        trace += llm_out + "\n"

        if decision["type"] == "final":
            step_result = decision["answer"]
            break

        # run tool
        tool_fn = TOOLS.get(decision["tool"])
        if tool_fn is None:
            obs = f"[ERROR] Unknown tool '{decision['tool']}'"
        else:
            obs = tool_fn(decision["input"])

        trace += f"Observation: {obs}\n"

    return {
        "trace": trace,
        "result": step_result
    }

# ---------- 3. CRITIC (per step result) ----------

SYSTEM_CRITIC = """
You are a critical reviewer.
Given the STEP DESCRIPTION and the STEP RESULT,
identify any gaps, vagueness, factual risk, compliance or policy risk,
or missing executive relevance. Then rewrite an improved version of the STEP RESULT.

Your output format MUST be:

CRITIQUE:
- bullet points of issues...

REVISED STEP RESULT:
<improved version>
"""

def critique_step(step_desc: str, step_result: str) -> dict:
    critic_out = call_model(
        SYSTEM_CRITIC,
        f"STEP DESCRIPTION:\n{step_desc}\n\nSTEP RESULT:\n{step_result}\n\nNow critique and revise."
    )

    # naive split
    parts = critic_out.split("REVISED STEP RESULT:")
    critique_text = parts[0].strip()
    revised = parts[1].strip() if len(parts) > 1 else step_result

    return {
        "critique": critique_text,
        "revised": revised
    }

# ---------- 4. FINAL SYNTHESIS ----------

SYSTEM_SYNTHESIZER = """
You are an executive briefing agent.

Given all REVISED STEP RESULTS from the mission,
write a single concise executive brief for the user.
Assume the user is a VP who wants signal, not fluff.

Format:
EXECUTIVE BRIEF:
<short paragraphs or bullet points with clear guidance>
"""

def synthesize_final(goal: str, revised_steps: List[str]) -> str:
    joined = "\n\n".join(
        f"- {txt}" for txt in revised_steps if txt and txt.strip()
    )
    final_out = call_model(
        SYSTEM_SYNTHESIZER,
        f"USER GOAL:\n{goal}\n\nREVISED STEP RESULTS:\n{joined}\n\nNow write the EXECUTIVE BRIEF."
    )
    return final_out

# ---------- Orchestration main ----------

def run_full_pipeline(goal: str, coords_for_weather: str = None):
    """
    1. Plan steps
    2. Execute each step (with tool calls)
    3. Critique each step
    4. Synthesize final brief
    """
    plan_steps = make_plan(goal)
    # If we got coords, try to auto-inject them into any weather step text
    if coords_for_weather:
        # crude heuristic: append coords hint to any step mentioning 'weather'
        plan_steps = [
            (s + f" Use coordinates {coords_for_weather} for weather.")
            if "weather" in s.lower()
            else s
            for s in plan_steps
        ]

    executed_info = []
    critiqued_info = []

    for idx, step_desc in enumerate(plan_steps, start=1):
        step_exec = execute_step(step_desc)
        executed_info.append((step_desc, step_exec))

        crit = critique_step(step_desc, step_exec["result"] or "")
        critiqued_info.append(crit["revised"])

    final_brief = synthesize_final(goal, [c for c in critiqued_info])

    return {
        "plan_steps": plan_steps,
        "executed": executed_info,
        "critiqued_revised_steps": critiqued_info,
        "final_brief": final_brief,
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_planner_agent.py \"your high-level goal\" [--coords \"LAT,LON\"]")
        sys.exit(1)

    if "--coords" in sys.argv:
        coords_index = sys.argv.index("--coords")
        goal = " ".join(sys.argv[1:coords_index])
        coords = sys.argv[coords_index+1] if coords_index+1 < len(sys.argv) else None
    else:
        goal = " ".join(sys.argv[1:])
        coords = None

    result = run_full_pipeline(goal, coords_for_weather=coords)

    print("========== PLAN ==========")
    for i, step_text in enumerate(result["plan_steps"], start=1):
        print(f"{i}. {step_text}")

    print("\n========== STEP EXECUTION TRACES ==========")
    for i, (desc, exec_info) in enumerate(result["executed"], start=1):
        print(f"\n--- Step {i}: {desc} ---")
        print(exec_info["trace"])
        print("Step Result:", exec_info["result"])

    print("\n========== CRITIQUED & REVISED STEP RESULTS ==========")
    for i, revised in enumerate(result["critiqued_revised_steps"], start=1):
        print(f"\nRevised Step {i}:")
        print(revised)

    print("\n========== FINAL EXECUTIVE BRIEF ==========")
    print(result["final_brief"])

if __name__ == "__main__":
    main()
