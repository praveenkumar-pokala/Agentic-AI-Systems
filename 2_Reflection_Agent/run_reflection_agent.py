import os, requests, sys, textwrap
from openai import OpenAI

# Setup
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY in environment.")

client = OpenAI(api_key=OPENAI_API_KEY)

WIKI_HEADERS = {"User-Agent": "reflection-agent-demo/1.0"}

def wikipedia_summary(topic: str) -> str:
    """
    Fetch factual context about a topic from Wikipedia's REST API summary endpoint.
    This gives us grounding info that can be used by the critique stage to detect hallucinations.
    Wikipedia's REST /page/summary/{title} is a common lightweight way to retrieve an entity summary. [citation: Wikipedia REST API docs] 
    """
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic}"
    r = requests.get(url, headers=WIKI_HEADERS, timeout=10)
    if r.status_code != 200:
        return f"[wiki] error {r.status_code}: {r.text[:200]}"
    d = r.json()
    title = d.get("title","")
    desc = d.get("description","")
    summary = d.get("extract","")
    return f"{title} — {desc}\n{summary}"

SYSTEM_DRAFT = """
You are an expert analyst.
Write the best possible answer to the user's question.
Be structured, factual, and helpful.
Do not mention reflection, critique, steps, or process. Just answer.
"""

SYSTEM_CRITIQUE = """
You are a ruthless senior reviewer.
Your job is to find weaknesses in the DRAFT ANSWER.

Be very direct. Point out:
1. Factual claims that may be wrong or unsupported.
2. Missing important context for an executive.
3. Overpromising / unsafe advice / legal-style risk.
4. Rambling or unclear structure.

You may use the EVIDENCE provided (for example Wikipedia summaries) to fact-check.
After listing issues, give concrete instructions on how to fix them.

Important:
- Do NOT rewrite the final answer here.
- Output only critique + improvement instructions.
"""

SYSTEM_REVISE = """
You are an executive-grade communicator.
Rewrite a FINAL ANSWER using:
- The original user question
- The original draft
- The critique feedback

Goals:
- Keep strong points from the draft.
- Fix factual gaps using the critique.
- Improve clarity, structure, and tone for a VP-level audience.
- Be confident but never overpromise.

Do not include 'critique says...' meta-talk.
Return only the final, improved answer.
"""

def call_oai(system_prompt: str, user_content: str):
    """
    Helper to call the model with a system instruction + user content.
    We use a reasoning-optimized model like `o4-mini`, which OpenAI positions
    for multi-step reasoning, self-critique, and tool integration. [citation: OpenAI model docs] 
    """
    resp = client.responses.create(
        model="o4-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    # normalize
    if hasattr(resp, "output_text"):
        return resp.output_text
    try:
        return resp.choices[0].message.content
    except Exception:
        # fallback (Responses API structure)
        if hasattr(resp, "output"):
            if isinstance(resp.output, list):
                return "\n".join(str(x) for x in resp.output)
            return str(resp.output)
        return str(resp)

def reflection_pipeline(user_question: str, evidence_topics=None):
    """
    Run full reflection loop:
    1. DRAFT
    2. CRITIQUE (with optional factual evidence)
    3. REVISED final answer
    """
    # 1. Draft
    draft = call_oai(
        SYSTEM_DRAFT,
        f"USER QUESTION:\n{user_question}\n\nWrite the draft answer now."
    )

    # 2. Collect evidence (optional grounding)
    evidence_blocks = []
    if evidence_topics:
        for topic in evidence_topics:
            ev = wikipedia_summary(topic)
            evidence_blocks.append(f"[EVIDENCE for {topic}]\n{ev}")
    evidence_text = "\n\n".join(evidence_blocks) if evidence_blocks else "(no external evidence provided)"

    critique_input = textwrap.dedent(f"""
    USER QUESTION:
    {user_question}

    DRAFT ANSWER:
    {draft}

    EVIDENCE:
    {evidence_text}

    Now critique the DRAFT ANSWER.
    """).strip()

    critique = call_oai(SYSTEM_CRITIQUE, critique_input)

    # 3. Revise
    revise_input = textwrap.dedent(f"""
    USER QUESTION:
    {user_question}

    ORIGINAL DRAFT:
    {draft}

    CRITIQUE:
    {critique}

    Now produce the improved FINAL ANSWER.
    """).strip()

    final_answer = call_oai(SYSTEM_REVISE, revise_input)

    return {
        "draft": draft,
        "critique": critique,
        "final": final_answer,
        "evidence_used": evidence_text,
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_reflection_agent.py \"your question here\"")
        print("Optional: add topics for evidence after --topics, comma-separated.")
        print("Example:")
        print("python run_reflection_agent.py \"Why is Hyderabad important for tech?\" --topics Hyderabad")
        sys.exit(1)

    # parse CLI args
    if "--topics" in sys.argv:
        idx = sys.argv.index("--topics")
        question = " ".join(sys.argv[1:idx])
        topics_raw = " ".join(sys.argv[idx+1:])
        topics = [t.strip() for t in topics_raw.split(",") if t.strip()]
    else:
        question = " ".join(sys.argv[1:])
        topics = []

    result = reflection_pipeline(question, evidence_topics=topics)

    print("========== DRAFT ANSWER ==========")
    print(result["draft"])
    print("\n========== CRITIQUE ==========")
    print(result["critique"])
    print("\n========== FINAL ANSWER ==========")
    print(result["final"])
    print("\n========== EVIDENCE USED ==========")
    print(result["evidence_used"])

if __name__ == "__main__":
    main()
