# Router Pattern in Agentic AI: Why It's Hard (and Dangerous) in Production

This repo is a teaching/demo pack to explain the **router pattern**:
> "Send each user request to the correct specialist agent."

Sounds clean. In reality, routing is where things quietly break.

We do FOUR things here:
1. We build a naive router with 3 domain agents.
2. We run realistic queries.
3. We *show exactly where routing fails* (ambiguity, lack of context, compliance risk).
4. We extract the lessons you MUST design for in production.

Use this repo in a live session and just scroll / run cells. It's designed to wake up leadership, not just engineers.


---

## 1. The Classic Router Story

Slide version that everyone sells:
- You have multiple expert agents:
  - `travel_planner_agent`
  - `expense_policy_agent`
  - `tech_support_agent`
- You write a `router(question)` that decides which agent should answer.
- Then you call just that agent.

Very pretty.
Very wrong in practice.


---

## 2. The Real-World Challenges (what this repo demonstrates)

### Challenge 1. Multi-intent queries
User:  
> "Book me a hotel near Hitech City in Hyderabad and confirm if the nightly rate is within company reimbursement policy."

Is that:
- Travel planning?
- Expense policy?

Answer: it's BOTH.
But a naive router is coded to pick ONE.
So it drops half the request silently.
That creates liability, not just inaccuracy.

**Key point:** Misrouting is silent scope drop.


### Challenge 2. Context-starved routing
User (after a long chat):  
> "Book the same place again for next Thursday."

Routing only sees this last sentence with no history.
A human knows “same place” = that Hyderabad executive hotel we approved under ₹6000/night.
The naive router has no memory and will guess.

**Key point:** If the router can't see conversation state, it will confidently act on the wrong object.


### Challenge 3. Policy vs convenience
User:  
> "Can I expense dinner with a client at Taj Falaknuma if it's more than ₹8,000?"

This *sounds* like travel/hospitality.
But it's actually an expense compliance question.
If you send this to Travel instead of Policy, you may generate a confident but noncompliant answer.

**Key point:** Routing is risk triage, not semantic similarity.


### Challenge 4. Security / escalation
User:  
> "Reset the firewall rules in our production VPN and send me the after-action summary."

If you don't have a safe "escalate to human / refuse" route,
the router will happily send this to Tech Support and the agent will *sound* like it complied.

**Key point:** Without an explicit "I cannot do this" branch, the system fails loud and wrong.


### Challenge 5. Overlapping agents
User:  
> "VPN is dropping every hour from the hotel wifi, can you whitelist my laptop?"

Is that:
- Tech support (connectivity issue)?
- Security (whitelisting a device on VPN)?
- Travel (the hotel network is unstable)?

Routers trained only as "single-label classifiers" will choose randomly and be wrong in high-risk paths.

**Key point:** You often need hierarchical routing:
1. detect if it's security/compliance-sensitive
2. then figure out which domain agent to use.


---

## 3. What a Production Router Actually Needs (final section in the notebook)

This repo will walk you to these architecture conclusions:

1. **Multi-label or multi-hop routing**
   The system should be able to say:
   - "This is travel + expense"
   - "I'll call two agents or stage them sequentially"

2. **Context-aware routing**
   Router must see conversation memory ("the same place" etc.) or else it *must ask*.

3. **Risk-aware routing**
   Before domain classification, first detect "safety/compliance/security/legal/finance" intent.
   If it's risky, escalate or route to a policy-backed agent.

4. **Fallback path**
   Router **must** be allowed to say:
   "This requires a human" or "I am not authorized."
   No fake promises.

5. **Auditable routing justification**
   Log:
   - "User asked X"
   - "We routed to Y"
   - "Because Z"
   Leadership needs to see this when something goes wrong.

In other words:
> A router in enterprise is not a classifier.  
> A router is governance.


---

## 4. Repo Structure

- `Router_Pattern_Challenges_Demo.ipynb`
  - Live teaching notebook
  - Runs naive router
  - Shows failure cases
  - Annotates risk

- `router_demo.py`
  - Same logic in script form so you can run from terminal
  - Prints routing choice + why that is dangerous

No external API keys are needed. Everything runs locally.


---

## 5. How to Run

### In Notebook
Open `Router_Pattern_Challenges_Demo.ipynb`, run all cells top to bottom.  
Scroll through the printed traces and read the inline markdown commentary.

### In Terminal
```bash
python router_demo.py
```

This will:
- run a batch of tricky user queries
- print which agent the naive router chose
- print the real risk you would face in production


---

## 6. License to Scare (How to Present This)

When you teach this:
- Do NOT say "here's how to fix routing with a better classifier."
- Say "here's why naive routing can create real business, compliance, and security exposure."
- Say "this is why we need guardrails before autonomy."

You're not teaching ML.
You're teaching responsibility.
