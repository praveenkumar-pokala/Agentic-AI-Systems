# Agentic AI with Memory: Short-Term Scratchpad + Long-Term Personalization

## 1. What this repo is

This repo demonstrates a **Memory-Augmented Agent**.

Most demos stop at "LLM answers you right now."
Real systems need continuity:
- Remember stable facts about the user (role, preferences, constraints).
- Use those in the next answer to behave like a real assistant, not amnesia.
- Keep an auditable record of *why* we saved something.

This repo shows a practical pattern you can actually ship:
1. **Short-term scratchpad**  
   We summarize recent conversation context so the model can stay coherent across turns without dumping the entire transcript.
2. **Long-term memory store**  
   We maintain a structured JSON "memory" file that keeps stable attributes about the user (ex: "User prefers executive-style summaries" or "User travels frequently to Hyderabad for VP-level meetings").  
   This is similar in spirit to retrieval-augmented memory or "profile memory" described in production assistant architectures: storing user preferences and pulling them back in future turns for personalization. This is conceptually adjacent to retrieval-augmented generation, where external context is injected into the prompt to ground the model. The difference is we store *user-specific* context, not generic domain knowledge. citeturn0search0turn0search2turn0search3turn0search8
3. **Memory write policy**  
   We do NOT save everything. We ask a model to classify:
   - Is this stable, high-signal info we should remember for future turns?
   - Or is it temporary / too sensitive / should not be stored?
   This mirrors responsible AI practice: memory must be intentional, auditable, and policy-driven.

Outcome:
- The agent responds using BOTH: (a) current turn context and (b) long-term memory.
- After responding, it decides whether to update memory.

This is how assistants start behaving like "your chief of staff," not just "a smart autocomplete."


---

## 2. Human thought process

Great human assistants naturally keep two kinds of state:

### (A) Scratchpad (short-term working memory)
They remember what just happened in the ongoing conversation:
- "We are discussing a Hyderabad business trip."
- "We already decided Hitech City hotel."
- "He said weather risk is important."

This doesn't have to live forever. It's just to not lose the current thread.

### (B) Long-term memory (stable profile)
They also remember things they will reuse in future interactions:
- "She is a VP."
- "She prefers concise executive summaries, not rambling."
- "She wants risk and cost implications surfaced automatically."

That survives across meetings.

And importantly, a real assistant will **not** store things that are too sensitive or irrelevant.

This repo encodes that exact behavior in code:
- keep a rolling short-term summary of the last interaction
- selectively persist high-value preferences or identity traits in a JSON memory file


---

## 3. Orchestrating that memory loop as an agentic workflow

We will wire four steps into the interaction loop:

### Step 1. Retrieve memory
Before answering the user's new question:
1. Load long-term memory (`memory.json`)
2. Summarize last messages (short-term scratchpad)
3. Feed both into the model as context

The system prompt becomes:
"You are advising this person. Here is what we know about them (memory). Here is what we're currently discussing (scratchpad). Now answer."

This is basically Retrieval-Augmented Personalization.

### Step 2. Generate answer
We ask a reasoning model (like `o4-mini`) to produce the answer,
given:
- user question
- scratchpad summary
- long-term memory profile

We tell it:
"Use these memories when helpful. Respect user's preferences."

### Step 3. Memory write proposal
After we answer, we ask the model again:
"From the user's latest message and your answer, is there anything that should be added or updated in long-term memory?
Return either
SAVE: {"key": "...", "value": "..."}
or
NOSAVE."

This is the memory write policy gate.
It's like an internal "privacy + usefulness" check.

### Step 4. Persist (with guardrails)
If the model returns SAVE, we append/update that memory in `memory.json`.

We now have:
- Auditable store (the JSON file)
- Explicit justification in logs ("model asked to save X")
- A clear boundary between transient scratchpad and persistent profile


---

## 4. Repo layout

- `MemoryAgent_Demo.ipynb`  
  Teaching notebook that walks cell-by-cell:
  - Initialize / view memory
  - Ask a question
  - Build scratchpad summary
  - Retrieve relevant long-term memory
  - Generate an answer with personalization
  - Ask if we should store new memory
  - Update the memory file

- `run_memory_agent.py`  
  CLI runner that:
  - Reads / writes `memory.json`
  - Prints the final personalized answer
  - Prints what (if anything) was stored to memory

- `memory.json`  
  Starts with a tiny seed profile (you can edit). In production this would live in a secure store keyed per-user.

- `requirements.txt`  
  Minimal deps to run.


---

## 5. Setup / Running

### Install
```bash
pip install -r requirements.txt
```

### Environment
```bash
export OPENAI_API_KEY="sk-your-openai-key"
```

### CLI usage
```bash
python run_memory_agent.py "I'm visiting Hyderabad again next week to meet execs. Give me a short briefing with risk points and travel tips. I prefer direct VP tone."
```

You will see:
1. The personalized answer.
2. Whether the agent proposed storing new memory.
3. The updated `memory.json` after the run.


---

## 6. Why this matters in real enterprise assistants

1. **Personal relevance without manual tuning**  
   The agent uses your stored style preferences and priorities automatically.

2. **Continuity across sessions**  
   The assistant remembers that you care about "executive-ready briefings" and "risk/operational impact," so you don't have to repeat yourself.

3. **Ethical memory boundary**  
   We explicitly ask a model to decide:
   - Is this persistent preference info?
   - Is this sensitive / private / volatile and shouldn't be stored?

   That decision step is logged.
   This is critical for compliance and trust.

4. **Auditability**  
   `memory.json` is inspectable, versionable, reviewable.
   You can prove what you remembered and why.

This is how AI stops being "autocomplete in a chat window"
and starts acting like a continuously learning chief of staff,
while still giving you control.
