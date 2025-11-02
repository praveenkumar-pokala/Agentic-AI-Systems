# Agentic AI with Reflection Pattern (Self-Check + Improvement Loop)

## 1. What this repo is
This repo teaches and demos the **Reflection Pattern** in agentic AI.

Reflection = The model does *not* just answer.
It:
1. Produces an initial draft answer.
2. Critiques its own answer (fact check, gaps, tone, safety).
3. Improves the answer based on that critique.
4. (Optionally) Repeats.

This pattern is used in modern reasoning models to reduce hallucinations, improve clarity, and enforce behavioral constraints like: compliance tone, senior-exec tone, “do not overpromise,” etc. Reflection is a *huge* step toward reliable AI systems in enterprises.

This repo gives you:
- A Jupyter notebook: step-by-step teaching demo.
- A CLI script that runs the reflection loop using OpenAI’s reasoning model (`o4-mini` / GPT-5 Thinking–class models optimised for planning and self-evaluation). These models are explicitly positioned by OpenAI for stepwise reasoning, critique, and revision in tool-augmented agent workflows. citeturn0search0turn0search2turn0search3turn0search8
- A lightweight factual lookup tool (Wikipedia REST summary) that can be injected into the reflection stage so the model can correct itself using external evidence instead of hallucinating. Wikipedia’s public REST API exposes a `/page/summary/{title}` endpoint that returns structured lead-paragraph summaries for entities like cities, companies, places, etc., without requiring auth. citeturn1search1turn1search4turn1search6

Goal:
You can show leadership that your AI doesn’t just “speak fast.”
It *thinks, audits itself, then speaks well.*

---

## 2. Human thought process

When an expert analyst writes an executive brief, they never just send the first draft.
They:
1. Draft quickly.
2. Re-read with a harsh lens:
   - Is this factually correct?
   - Am I overselling?
   - Did I miss business risk?
   - Is the tone right for my audience?
3. Fix it.
4. Only then send.

That second-pass “ruthless self-review” is reflection.
In humans, that’s where quality happens.
In AI, reflection is how you move from “a clever intern that improvises” to “a trusted advisor that self-checks.”

---

## 3. Orchestrating that human reflective loop as an agentic workflow

We’ll turn that process into explicit steps:

### Step 1. Draft Stage
We ask the model:
- “Write the best answer you can to this question.”
We call this `draft_answer`.

### Step 2. Critique Stage
We then feed the draft back to the model with strict review instructions:
- “Act like a critical reviewer. Find factual uncertainty, missing context, overconfident claims, weak structure, unclear reasoning, risky promises. Be brutally honest.”
We call this `critique`.

Optionally in this step:
- We can pull *evidence* from tools. For example:
  - We can call `wikipedia_summary("Hyderabad")`
  - Attach its Observation to the critique prompt
  - Now the reviewer has something external to verify facts with (this is enormous for reducing hallucinations in production systems).

### Step 3. Refine Stage
We then ask the model:
- “Rewrite the final answer using the critique. Keep strengths. Fix weaknesses. Be concise, executive-ready.”
We call this `revised_answer`.

### Step 4. Deliverable
We present:
- Trace: draft → critique → final
- Final Answer: the version that is allowed to ship

This is the Reflection Pattern.

---

## 4. Repo layout

- `Reflection_Agent_Demo.ipynb`
  - Teaching notebook
  - Runs the 3-stage loop (draft → critique → revise)
  - Optionally shows how to inject factual grounding using the Wikipedia REST API

- `run_reflection_agent.py`
  - CLI runner
  - You pass a question
  - It prints the draft, the critique, and the final improved answer

- `requirements.txt`
  - Minimal deps to run (OpenAI SDK, requests, nbformat, jupyter)

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
No OpenWeather key is needed for the reflection agent.  
(Weather is not part of reflection; reflection is about self-checking.)

### CLI usage
```bash
python run_reflection_agent.py "Explain why Hyderabad is important for tech companies and what a VP should know before visiting."
```

You will see:
1. DRAFT ANSWER (raw first attempt)
2. CRITIQUE (self-review: factual gaps, tone issues, unclear claims)
3. FINAL ANSWER (revised, higher quality, safer)

---

## 6. Why this matters in the enterprise

Reflection gives you:
1. **Quality uplift**  
   The model corrects itself before anyone sees the output.

2. **Reduced hallucination risk**  
   The critique step explicitly hunts for “claims that might be wrong.”  
   You can also inject external evidence (Wikipedia summaries, internal KB hits, policy docs) into the critique step to fact-check.

3. **Tone / compliance control**  
   In the critique prompt you can demand alignment:
   - “Remove overpromises.”
   - “Do not give legal advice.”
   - “Keep executive tone: concise, evidence-backed, risk-aware.”

4. **Auditability of thinking**  
   You now have:  
   - the draft,  
   - the critique,  
   - and the final.  
   You can store all 3 for audit, and show you are not shipping unreviewed hallucinations.

This is how you convince leadership your AI output is *defensible*.

You’re no longer shipping “whatever the model said.”
You’re shipping “what the model said AFTER it challenged itself.”
