import os, json, sys, textwrap
from openai import OpenAI
from pathlib import Path

MEMORY_FILE = Path(__file__).parent / "memory.json"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY in environment.")

client = OpenAI(api_key=OPENAI_API_KEY)

########################################
# Utility: load/save long-term memory
########################################

def load_memory():
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"user_profile": {}, "last_updated": None}

def save_memory(mem):
    mem["last_updated"] = "updated"
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2)

########################################
# 1. Build scratchpad summary
########################################

SYSTEM_SCRATCHPAD = """
You are an analyst.
Summarize the user's latest message into a compact scratchpad context
that captures:
- What the user is trying to do right now
- Any constraints or style requests
Do NOT add new facts. Be concise.
Return ONLY the summary text, no bullet labels.
"""

def build_scratchpad(user_msg: str) -> str:
    resp = client.responses.create(
        model="o4-mini",
        input=[
            {"role": "system", "content": SYSTEM_SCRATCHPAD},
            {"role": "user", "content": user_msg},
        ],
    )
    if hasattr(resp, "output_text"):
        return resp.output_text.strip()
    try:
        return resp.choices[0].message.content.strip()
    except Exception:
        if hasattr(resp, "output"):
            if isinstance(resp.output, list):
                return "\n".join(str(x) for x in resp.output).strip()
            return str(resp.output)
        return str(resp).strip()

########################################
# 2. Answer using memory + scratchpad
########################################

SYSTEM_ANSWER = """
You are an executive briefing assistant.

You will receive:
1. LONG_TERM_MEMORY: stable known preferences about this user
2. SCRATCHPAD: summary of what they just asked
3. USER_QUESTION: the raw question

Your job:
- Answer USER_QUESTION directly
- Respect tone/style preferences in LONG_TERM_MEMORY
- Highlight risk, operational impact, cost if relevant
- Be concise and VP-ready

Output only the final answer for the user.
"""

def answer_with_memory(long_term_memory: dict, scratchpad: str, user_question: str) -> str:
    composite_prompt = textwrap.dedent(f"""
    LONG_TERM_MEMORY:
    {json.dumps(long_term_memory, indent=2)}

    SCRATCHPAD:
    {scratchpad}

    USER_QUESTION:
    {user_question}
    """).strip()

    resp = client.responses.create(
        model="o4-mini",
        input=[
            {"role": "system", "content": SYSTEM_ANSWER},
            {"role": "user", "content": composite_prompt},
        ],
    )

    if hasattr(resp, "output_text"):
        return resp.output_text.strip()
    try:
        return resp.choices[0].message.content.strip()
    except Exception:
        if hasattr(resp, "output"):
            if isinstance(resp.output, list):
                return "\n".join(str(x) for x in resp.output).strip()
            return str(resp.output)
        return str(resp).strip()

########################################
# 3. Memory write proposal
########################################

SYSTEM_MEMORY_WRITE = """
You are a memory write policy checker for an AI assistant.

You get:
- The user's latest message
- The assistant's final answer
- The existing LONG_TERM_MEMORY (JSON)

Your job:
1. Decide if there's a NEW stable preference or identity detail
   that would be valuable to remember long-term.
   Examples:
   - preferred communication style
   - recurring travel location
   - recurring role/seniority context

2. If yes, respond EXACTLY in this JSON format (one line):
SAVE: {"key": "...", "value": "..."}

3. If not, respond EXACTLY:
NOSAVE

Rules:
- DO NOT store secrets, health data, passwords, account numbers.
- DO NOT store extremely sensitive personal identifiers.
- DO NOT store temporary info like "today I am tired".
- Focus on preferences and recurring context that will matter in future answers.
"""

def propose_memory_update(long_term_memory: dict, user_msg: str, final_answer: str) -> str:
    composite_prompt = textwrap.dedent(f"""
    USER_MESSAGE:
    {user_msg}

    ASSISTANT_FINAL_ANSWER:
    {final_answer}

    CURRENT_LONG_TERM_MEMORY:
    {json.dumps(long_term_memory, indent=2)}

    Produce memory decision now.
    """).strip()

    resp = client.responses.create(
        model="o4-mini",
        input=[
            {"role": "system", "content": SYSTEM_MEMORY_WRITE},
            {"role": "user", "content": composite_prompt},
        ],
    )

    if hasattr(resp, "output_text"):
        return resp.output_text.strip()
    try:
        return resp.choices[0].message.content.strip()
    except Exception:
        if hasattr(resp, "output"):
            if isinstance(resp.output, list):
                return "\n".join(str(x) for x in resp.output).strip()
            return str(resp.output)
        return str(resp).strip()

########################################
# 4. Apply memory update if approved
########################################

def apply_memory_update(mem: dict, decision: str) -> (dict, str):
    decision = decision.strip()
    if decision.startswith("NOSAVE"):
        return mem, "No persistent memory update."

    if decision.startswith("SAVE:"):
        # extract JSON after "SAVE:"
        payload = decision[len("SAVE:"):].strip()
        try:
            data = json.loads(payload)
            key = data.get("key")
            value = data.get("value")
        except Exception:
            return mem, f"Memory decision malformed: {decision}"

        if not key or not value:
            return mem, f"Memory decision missing key/value: {decision}"

        # write to mem["user_profile"][key]
        if "user_profile" not in mem or not isinstance(mem["user_profile"], dict):
            mem["user_profile"] = {}
        mem["user_profile"][key] = value
        save_memory(mem)
        return mem, f"Stored memory: {key} = {value}"

    # fallback
    return mem, f"Unrecognized memory decision: {decision}"

########################################
# MAIN PIPELINE
########################################

def run_pipeline(user_msg: str):
    # load existing memory
    mem = load_memory()

    # build scratchpad for this single turn
    scratchpad = build_scratchpad(user_msg)

    # generate personalized answer
    final_answer = answer_with_memory(mem, scratchpad, user_msg)

    # ask model if we should persist anything new
    decision = propose_memory_update(mem, user_msg, final_answer)

    # update memory if allowed
    updated_mem, note = apply_memory_update(mem, decision)

    return {
        "scratchpad": scratchpad,
        "final_answer": final_answer,
        "memory_decision": decision,
        "memory_update_note": note,
        "updated_memory": updated_mem,
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_memory_agent.py \"your message here\"")
        sys.exit(1)

    user_msg = " ".join(sys.argv[1:])
    result = run_pipeline(user_msg)

    print("========== SCRATCHPAD ==========")
    print(result["scratchpad"])
    print("\n========== FINAL ANSWER ==========")
    print(result["final_answer"])
    print("\n========== MEMORY DECISION ==========")
    print(result["memory_decision"])
    print("\n========== MEMORY UPDATE NOTE ==========")
    print(result["memory_update_note"])
    print("\n========== UPDATED MEMORY (memory.json) ==========")
    print(json.dumps(result["updated_memory"], indent=2))

if __name__ == "__main__":
    main()
