
# 1. ReAct Agent — Reasoning + Tool Use with Evidence

**Pattern goal:** The agent should not just answer.
It should *think*, decide what info it needs, call tools to go get that info, read the results, and then answer with that evidence.

This loop is called ReAct (Reason + Act). It looks like:

1. Thought: what do I need?
2. Action: call a tool (weather API, Wikipedia, corporate hotel policy)
3. Observation: tool result
4. Repeat Thought/Action/Observation until satisfied
5. Final Answer: produce grounded answer

Why this matters in enterprise:
- You get an auditable trace of what the agent did.
- The agent is not hallucinating logistics or policy.
- You can replay and inspect every step when someone asks “Why did we say that?”

This folder contains:
- `run_agent.py` : CLI demo
- `AgenticAI_ReAct_LiveTools_Demo.ipynb` : teaching notebook for live walkthrough
