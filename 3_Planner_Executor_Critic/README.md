# Agentic AI with Planner → Executor → Critic Loop
## Strategic Task Decomposition + Tool Use + Continuous Self-Evaluation

---

## 1. What this repo is

This repo demonstrates a full **Planner / Executor / Critic** agent loop.

Modern agentic AI in the enterprise is not just "LLM answers a question."  
Serious systems do three things:

1. **Planner**  
   Break the high-level goal into concrete steps like a project lead.
   ("First understand the city. Then check weather risk. Then map to travel policy. Then produce an executive brief.")

2. **Executor**  
   For each step, actually perform work:
   - Use live tools / APIs (Wikipedia REST summaries, OpenWeather weather intel, internal corporate hotel policy).
   - Gather evidence instead of hallucinating.

3. **Critic / Auditor**  
   After each step, ask:
   - Is this result complete?
   - Are there obvious gaps / risks / missing evidence?
   - Do we need to fix or refine before we trust it?

At the end we compose a final brief for the user that is grounded, policy-aware, and already self-reviewed.

This pattern is what you show to leadership when you want to say
> "This system does not just answer. It plans, executes, and audits itself."

It also matches what modern OpenAI reasoning-class models (like `o4-mini`, `o3`, GPT-5 Thinking) are optimized to do: plan multi-step tasks, call tools, adapt based on tool results, and reflect to improve reliability. citeturn0search0turn0search2turn0search3turn0search8

We go beyond ReAct (Thought → Action → Observation) and beyond Reflection (Draft → Critique → Rewrite).  
Here we are now doing:  
**Plan → Execute with Tools → Critically Evaluate each step → Final Executive Brief.**

---

## 2. Human thought process

Imagine you're an operations chief asked:
"Brief me for a business trip to Hyderabad: what is Hyderabad, current weather, and which approved hotel should I book near Hitech City?"

A strong human doesn't jump straight to an answer. They:

1. Plan the work
   - Step 1: Get factual background about Hyderabad
   - Step 2: Get current weather for Hyderabad so I can advise packing / risk
   - Step 3: Check corporate policy for approved hotels near Hitech City
   - Step 4: Summarize in an exec-friendly brief

2. Execute each step
   - Actually pulls data from sources, doesn't invent
   - Uses internal policy for the hotel (compliance requirement)

3. Self-check after each step
   - "Is that description of Hyderabad specific enough for a VP?"
   - "Is weather actionable? Or do I need to warn about rain, heat, etc.?"
   - "Does the hotel recommendation align with travel policy (budget, distance, amenities)?"

4. Deliver a final, confident, accountable answer

That is Planner → Executor → Critic.

---

## 3. Orchestrating that human loop as an agentic workflow

### Phase 1. Planner
We call an OpenAI reasoning model (`o4-mini`) with a **planning prompt**:
- "Break this goal into numbered steps that a smart analyst would take. Be specific and actionable."

The output is a plan like:
1. Summarize Hyderabad's tech/business relevance.
2. Get current weather for Hyderabad.
3. Recommend a policy-approved hotel near Hitech City.
4. Write a short executive brief combining all of the above.

We store these steps as machine-readable text.

### Phase 2. Executor
For each step, we run an **execute_step** loop:
- We tell the model:
  - "Here is the step you're executing."
  - "Here are the tools you are allowed to use."
- The model responds ReAct-style with:
  - Thought: ...
  - Action: <tool_name>
  - Action Input: <args>
  or directly produces a partial result.

We parse that output. If it requests a tool, we run it:
- `wikipedia_summary(topic)` → Wikipedia REST `/page/summary/{title}` returns factual summary text. This endpoint is public and widely used for programmatic entity summaries. citeturn1search1turn1search4turn1search6
- `weather_brief(lat,lon)` → OpenWeather API returns live conditions for coordinates using a key you provide. OpenWeather's "current weather" endpoint (`/data/2.5/weather`) returns temperature, conditions, wind, etc., available on a free tier with API key. citeturn0search0turn0search2turn0search9turn0search18
- `corporate_hotel(city)` → internal, policy-approved hotel logic.

We append the Observation to the step transcript and let the model continue until it returns a `Final Answer:` for that step.

We collect that per-step result.

### Phase 3. Critic
For each step result, we ask a second prompt:
- "Critique this step result. Is it complete, factual, aligned to policy, useful for an executive? Suggest corrections or additions."
This is similar to a reflection pass, but scoped per-step, so low quality gets corrected *before* it contaminates the final brief.

### Phase 4. Final Brief
Finally we ask the model to synthesize the reviewed step outputs (post-critique) into an executive-facing summary for the user.

---

## 4. Repo layout

- `PlannerExecutorCritic_Demo.ipynb`  
  Teaching notebook:
  - Builds the plan
  - Executes each plan step with live tools
  - Critiques each step
  - Produces a final executive brief
  - Prints the full trace

- `run_planner_agent.py`  
  CLI runner for the complete loop.  
  You give it a high-level question and (optionally) lat/lon for weather.  
  It prints:
  - The plan
  - Each step's execution trace
  - Each step's critique
  - The final brief

- `requirements.txt`  
  Minimal runtime deps

---

## 5. Setup and run

### Install
```bash
pip install -r requirements.txt
```

### Environment
```bash
export OPENAI_API_KEY="sk-your-openai-key"
export OPENWEATHER_API_KEY="your-openweather-key"
```

### CLI Example
```bash
python run_planner_agent.py   "Brief me for a Hyderabad business trip: what is Hyderabad, what's the weather (17.44,78.38), and where should I stay near Hitech City?"   --coords "17.44,78.38"
```

You will see:
1. PLAN
2. STEP EXECUTION traces (Thought / Action / Observation / Final Answer per step)
3. STEP CRITIQUES
4. FINAL EXECUTIVE BRIEF

---

## 6. Why this matters for leadership

This pattern demonstrates maturity in three dimensions:

1. **Decomposition / Planning**  
   The agent shows it can take an ambiguous task and break it into deterministic work units.  
   That's how humans lead teams.

2. **Grounded Execution with Tools**  
   Each step calls approved tools instead of guessing.  
   That’s how you avoid hallucinated operational advice.

3. **Built-in Audit / QA**  
   Each step is critiqued before use.  
   The final answer you present has already been reviewed for quality, tone, and policy alignment.

This is not a chatbot.  
This is an analyst that plans, executes using live data + company policy, self-audits, and then briefs you at VP level.

This is the shape of serious Agentic AI in production.
