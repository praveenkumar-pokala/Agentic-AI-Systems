
import os, re, requests, textwrap
from typing import Dict, Callable

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "<PUT_YOUR_KEY_HERE>")

WIKI_HEADERS = {"User-Agent": "react-agent-demo/1.0"}

def wikipedia_summary(topic: str) -> str:
    """Use Wikipedia REST API /page/summary/{title} to get concise factual summary."""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic}"
    r = requests.get(url, headers=WIKI_HEADERS, timeout=10)
    if r.status_code != 200:
        return f"[wiki] error {r.status_code}: {r.text[:200]}"
    d = r.json()
    return f"{d.get('title','')} — {d.get('description','')}\n{d.get('extract','')}"

def weather_brief(latlon: str) -> str:
    """OpenWeather current weather snapshot for lat,lon. Needs OPENWEATHER_API_KEY on env."""
    if OPENWEATHER_API_KEY.startswith("<PUT_"):
        return "[weather] Please set OPENWEATHER_API_KEY"
    lat, lon = [float(x.strip()) for x in latlon.split(",")]
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY}
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        return f"[weather] error {r.status_code}: {r.text[:200]}"
    d = r.json()
    k2c = lambda k: round(k - 273.15, 1)
    desc = d["weather"][0]["description"]
    temp_c = k2c(d["main"]["temp"])
    return f"{desc}, {temp_c}°C"

def corporate_hotel(city: str) -> str:
    """Stub for travel policy."""
    if city.lower() == "hyderabad":
        return (
            "MetroLink Executive Suites (~₹5400/night). "
            "5-10 min to Hitech City. Breakfast, meeting room, gym. "
            "Commonly approved for VP/executive travel."
        )
    return "No pre-approved executive hotel found for that city."

TOOLS: Dict[str, Callable[[str], str]] = {
    "wikipedia_summary": wikipedia_summary,
    "weather_brief": weather_brief,
    "corporate_hotel": corporate_hotel,
}

def react_demo(user_query: str):
    """
    Offline simulation of a ReAct loop.
    In production you'd drive this with an LLM (e.g. o4-mini) that produces Thought/Action steps,
    but here we show the trace deterministically so it runs anywhere.
    """

    trace = []

    # Step 1
    step1 = textwrap.dedent(f"""
    Thought: The user is asking about an executive-suitable hotel near Hitech City in Hyderabad and weather/packing tips.
    Thought: I should gather factual context about Hyderabad first.
    Action: wikipedia_summary
    Action Input: Hyderabad
    """).strip()
    trace.append(step1)
    obs1 = wikipedia_summary("Hyderabad")
    trace.append(f"Observation: {obs1}")

    # Step 2
    step2 = textwrap.dedent(f"""
    Thought: I should get current weather so I can advise packing.
    Action: weather_brief
    Action Input: 17.44,78.38
    """).strip()
    trace.append(step2)
    obs2 = weather_brief("17.44,78.38")
    trace.append(f"Observation: {obs2}")

    # Step 3
    step3 = textwrap.dedent(f"""
    Thought: I should retrieve a policy-approved executive hotel near Hitech City.
    Action: corporate_hotel
    Action Input: Hyderabad
    """).strip()
    trace.append(step3)
    obs3 = corporate_hotel("Hyderabad")
    trace.append(f"Observation: {obs3}")

    final_answer = textwrap.dedent(f"""
    Final Answer: Hyderabad is a major Indian tech/business hub centered around Hitech City.
    Recommended stay: {obs3}
    Weather right now: {obs2}
    Guidance: Stay within ~10 min of Hitech City to cut transit risk. Pack for actual conditions.
    Mention the approved property in your expense note to avoid reimbursement issues.
    """).strip()
    trace.append(final_answer)

    return "\n\n".join(trace)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        user_q = "Find me an exec-suitable hotel near Hitech City in Hyderabad for Monday. Include cost logic and packing/weather tips."
    else:
        user_q = " ".join(sys.argv[1:])

    print("USER QUERY:", user_q)
    print("=== REACT TRACE ===")
    print(react_demo(user_q))
