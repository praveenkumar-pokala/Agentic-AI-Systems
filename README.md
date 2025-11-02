
# The Architecture of Agentic AI Systems — A Complete Hands-on Suite

This repository unifies **five complete, working, and educationally brilliant patterns** into one cohesive structure.
It is built for AI system designers, researchers, and engineering leaders who want to understand, demonstrate, and teach
how modern intelligent assistants actually work in production — with autonomy, grounding, memory, and governance.

Each subfolder is a runnable module with notebooks, scripts, and narrative. Together they form a masterclass-level
curriculum in Enterprise-Grade Agentic AI System Design.

---

## 🧠 Contents Overview

| # | Pattern | Core Idea | Analogy | Design Focus |
|---|---------|-----------|---------|--------------|
| 1 | **ReAct Agent** | Reason → Act → Observe → Final Answer | Scientist running experiments | Tool use + traceability |
| 2 | **Reflection Agent** | Draft → Critique → Rewrite | Peer review | Self-correction + tone & compliance |
| 3 | **Planner–Executor–Critic Agent** | Plan → Execute (with tools) → Critique → Synthesize | Chief of Staff | Task decomposition + oversight |
| 4 | **Memory-Augmented Agent** | Short-Term Scratchpad + Long-Term Memory | Personal Chief of Staff | Personalization + continuity |
| 5 | **Router Pattern Governance** | Multi-domain routing and escalation | Call Center Director / Risk Officer | Risk triage + escalation + auditability |

---

## 📂 Folder Structure

```text
agentic_ai_patterns_full_repo/
│
├── 1_ReAct_Agent/
│   ├── AgenticAI_ReAct_LiveTools_Demo.ipynb
│   ├── run_agent.py
│   └── README.md
│
├── 2_Reflection_Agent/
│   ├── Reflection_Agent_Demo.ipynb
│   ├── run_reflection_agent.py
│   └── README.md
│
├── 3_Planner_Executor_Critic/
│   ├── PlannerExecutorCritic_Demo.ipynb
│   ├── run_planner_agent.py
│   └── README.md
│
├── 4_Memory_Agent/
│   ├── MemoryAgent_Demo.ipynb
│   ├── run_memory_agent.py
│   ├── memory.json
│   └── README.md
│
├── 5_Router_Pattern/
│   ├── Router_Pattern_Challenges_Demo.ipynb
│   ├── router_demo.py
│   └── README.md
│
└── requirements.txt  (shared deps)
```

---

## 🚀 How to Get Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

Core packages:
```text
openai>=1.45.0
requests>=2.31.0
nbformat>=5.10.0
jupyter>=1.0.0
```

### 2. Export environment variables for models / tools

Some modules call LLMs or external APIs.

```bash
export OPENAI_API_KEY="sk-your-openai-key"
export OPENWEATHER_API_KEY="your-openweather-key"
```

- `OPENAI_API_KEY` is used for reasoning models like `o4-mini`, which are optimized for multi-step reasoning, tool orchestration, critique, and planning in agent workflows. These models are designed to follow structured prompts (like ReAct-style Thought → Action → Observation loops) and perform iterative refinement. citeturn0search0turn0search2turn0search3turn0search8  
- `OPENWEATHER_API_KEY` is used to get live weather data via OpenWeather's current weather API (`/data/2.5/weather`) that returns real-time conditions and temperature. citeturn0search9turn0search18

### 3. Run a pattern demo (example: ReAct)
```bash
cd 1_ReAct_Agent
python run_agent.py "Find me an exec-suitable hotel near Hitech City in Hyderabad for Monday. Include cost logic and packing/weather tips."
```

Or open the notebook in Jupyter / VS Code and run all cells with narration.

---

## 🔍 Pattern Summaries

### 1. ReAct — Reason + Act + Observe
The agent does not just “answer.” It thinks out loud, calls tools, reads the results, and only then answers.

- Thought → Action → Observation → Final Answer loop  
- Calls live tools like Wikipedia (context), Weather (risk/packing), Corporate Hotel Policy (compliance)  
- Produces an auditable trace

**Message to leadership:** We don't hallucinate logistics. We gather evidence.

---

### 2. Reflection — Draft → Critique → Rewrite
The agent writes a draft, then becomes its own harsh reviewer, then rewrites.

- Step 1: Generate best-effort draft  
- Step 2: Critique the draft for risk, factual uncertainty, tone  
- Step 3: Rewrite final answer with those fixes

**Message to leadership:** We do not ship first drafts. The AI self-reviews and we log that review.

---

### 3. Planner–Executor–Critic — Chief-of-Staff Behavior
We model how real work gets done in an org.

1. Planner: break high-level goal into concrete steps  
2. Executor: run each step with tools (ReAct loops per step)  
3. Critic: audit each step's output for gaps / compliance / usefulness  
4. Synthesizer: produce an executive brief

**Message to leadership:** This is structured autonomy with oversight, not a chatbot.

---

### 4. Memory-Augmented Agent — Responsible Personalization
We introduce working memory and long-term memory.

- Scratchpad: “what we’re doing right now” (short-term context)  
- Long-term memory: “who this user is and how they like to be briefed,” stored in `memory.json`  
- Memory Write Policy: after each turn, the model decides if new info is worth remembering, and if it’s appropriate to save

**Message to leadership:** The AI learns you — but with an auditable gate and explicit policy.

---

### 5. Router Pattern — Governance, Not Just Classification
This module is designed to scare people in the right way.

We show five failure modes of a naive router that tries to send a query to “the right agent”:
1. Multi-intent queries (Travel + Expense in one sentence)  
2. Context starvation (“Book the same place again” with no memory)  
3. Policy vs convenience (“Can I expense dinner at Taj Falaknuma?” → finance/compliance, not lifestyle advice)  
4. Security / escalation (“Reset the firewall on production VPN”)  
5. Overlapping ownership (Tech vs Security vs Travel in one query)

**Message to leadership:**  
Routing is not a classifier. Routing is a risk triage layer.

---

## 🎓 Teaching Flow (80 min masterclass)

1. **ReAct Agent**  
   - Show Thought / Action / Observation trace.  
   - Message: “This is how we ground answers in real data.”

2. **Reflection Agent**  
   - Show Draft → Critique → Rewrite.  
   - Message: “We don’t ship first drafts.”

3. **Planner–Executor–Critic**  
   - Show step planning, tool execution with critique, final executive brief.  
   - Message: “This is a chief of staff, not a chatbot.”

4. **Memory Agent**  
   - Show scratchpad, memory.json, and the memory write gate.  
   - Message: “Personalization with auditability.”

5. **Router Pattern**  
   - Run the stress tests.  
   - Message: “Governance is built into routing logic.”

Close with this line:
> “Autonomy without governance is not intelligence. It’s exposure.”

---

## 🧱 Big Picture Architecture

```text
User Query
   ↓
[Router Layer]
   - Risk-aware intent routing
   - Can say "escalate to human"
   ↓
[Planner]
   - Breaks work into steps
   ↓
[Executor(s)]
   - Use ReAct loops to call tools
   ↓
[Critic / Reflector]
   - Audits, repairs, rewrites
   ↓
[Memory Layer]
   - Injects user preferences safely
   ↓
[Synthesizer]
   - Produces VP-ready brief
```

This repo gives you working building blocks for each box in that pipeline.

---

## 🏆 Credit
Curated for high-agency technical leaders, by Dr. Praveen Kumar Pokala.

When you present this, you are not showing “LLM demos.”  
You are walking executives through what production-grade Agentic AI actually looks like.

---

## 📘 License
MIT — use it to teach, ship, impress.
