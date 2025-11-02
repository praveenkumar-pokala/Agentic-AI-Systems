"""
router_demo.py

This script simulates a naive router that picks ONE agent for each query.
It then shows you why that's unsafe.

Agents:
- travel_planner_agent
- expense_policy_agent
- tech_support_agent
- security_policy_agent (optional high-sensitivity bucket)

Router: simple keyword heuristic (intentionally naive).
In production this "router" is often just an LLM classification prompt.
We keep it heuristic here to make failure obvious and reproducible.

You run this file directly to produce an audit-style printout.
"""

from typing import Tuple, Dict

########################
# Mock specialist agents
########################

def travel_planner_agent(query: str) -> str:
    return (
        "[travel_planner_agent]\n"
        "I can suggest hotels, locations, and logistics.\n"
        "Example answer: 'Stay near Hitech City. It's close to offices and reduces commute risk.'"
    )

def expense_policy_agent(query: str) -> str:
    return (
        "[expense_policy_agent]\n"
        "I can talk about what's reimbursable, nightly caps, client dinner rules.\n"
        "Example answer: 'Client dinners above ₹8,000 require director approval and receipt.'"
    )

def tech_support_agent(query: str) -> str:
    return (
        "[tech_support_agent]\n"
        "I can help with VPN setup, laptop config, Wi-Fi troubleshooting.\n"
        "Example answer: 'Try switching to the backup VPN gateway and confirm if packet loss drops.'"
    )

def security_policy_agent(query: str) -> str:
    return (
        "[security_policy_agent]\n"
        "I handle production security, access control, whitelisting, firewall changes.\n"
        "I usually should escalate to human approval.\n"
        "Example answer: 'I cannot directly change firewall rules without approval.'"
    )


########################
# Naive router
########################

def naive_router(query: str) -> Tuple[str, str]:
    """
    Return (agent_name, rationale)
    We do super basic keyword routing.
    This is deliberately brittle to expose categories of failure.
    """

    qlow = query.lower()

    # super high risk keywords -> security_policy
    if "firewall" in qlow or "whitelist" in qlow or "production vpn" in qlow:
        return "tech_support_agent", "Looks technical (VPN / firewall), routed to tech_support_agent."

    # expense-ish words
    if "reimburse" in qlow or "reimbursement" in qlow or "expense" in qlow or "₹" in qlow or "rs." in qlow:
        return "expense_policy_agent", "Detected money/expense keywords."

    # travel-ish words
    if "hotel" in qlow or "book a hotel" in qlow or "hitech city" in qlow or "hyderabad" in qlow:
        return "travel_planner_agent", "Detected travel / location keywords."

    # tech-ish words
    if "vpn" in qlow or "wifi" in qlow or "laptop" in qlow:
        return "tech_support_agent", "Detected IT support keywords."

    # fallback
    return "travel_planner_agent", "Defaulted to travel_planner_agent (bad default)."


def run_agent(agent_name: str, query: str) -> str:
    if agent_name == "travel_planner_agent":
        return travel_planner_agent(query)
    if agent_name == "expense_policy_agent":
        return expense_policy_agent(query)
    if agent_name == "tech_support_agent":
        return tech_support_agent(query)
    if agent_name == "security_policy_agent":
        return security_policy_agent(query)
    return "[router] Unknown agent."


########################
# Stress tests
########################

TEST_QUERIES = [
    # Multi-intent: travel + policy
    "Book a hotel near Hitech City in Hyderabad for Monday and confirm the nightly rate is within reimbursement policy.",

    # Context starved follow-up
    "Book the same place again for next Thursday.",

    # Policy vs convenience (sounds like travel but is compliance)
    "Can I expense dinner with a client at Taj Falaknuma if it's more than ₹8,000?",

    # Security / escalation risk
    "Reset the firewall rules in our production VPN and send me the after-action summary.",

    # Overlap: tech + security + travel
    "VPN is dropping every hour from the hotel wifi, can you whitelist my laptop?"
]

RISK_ANALYSIS: Dict[str, str] = {
    TEST_QUERIES[0]: (
        "RISK: This query spans Travel (hotel near Hitech City) and Expense Policy (reimbursement).\n"
        "The router is forced to pick ONE agent so half the request may be silently dropped.\n"
        "Silent scope drop = user walks away thinking they're compliant when they may not be."
    ),
    TEST_QUERIES[1]: (
        "RISK: Router sees only this line, not past context.\n"
        "'the same place' needs memory of prior hotel + budget approval.\n"
        "Without conversation context, routing guesses.\n"
        "Guessed routing => booking wrong property under wrong cost ceiling."
    ),
    TEST_QUERIES[2]: (
        "RISK: This SOUNDS like travel (dinner, Taj) but it's actually EXPENSE COMPLIANCE.\n"
        "If routed to Travel instead of Expense, we might promise reimbursement where policy forbids it.\n"
        "That's a compliance breach, not just a wrong answer."
    ),
    TEST_QUERIES[3]: (
        "RISK: This is SECURITY-SENSITIVE.\n"
        "Router 'hears VPN/firewall' and dumps to tech_support_agent.\n"
        "Tech support might sound confident and imply action.\n"
        "No escalation, no approval path => catastrophic risk."
    ),
    TEST_QUERIES[4]: (
        "RISK: Overlapping domains.\n"
        "Is this Travel (hotel wifi)? Tech Support (VPN stability)? Security (whitelisting device)?\n"
        "Router may choose arbitrarily and then give unsafe advice about whitelisting."
    ),
}

def main():
    for q in TEST_QUERIES:
        agent_name, rationale = naive_router(q)
        answer_preview = run_agent(agent_name, q)

        print("----------------------------------------------------")
        print("USER QUERY:")
        print(q)
        print()
        print("ROUTER DECISION:", agent_name)
        print("ROUTER RATIONALE:", rationale)
        print()
        print("AGENT RESPONSE PREVIEW:")
        print(answer_preview)
        print()
        print(RISK_ANALYSIS[q])
        print("----------------------------------------------------\n\n")

if __name__ == "__main__":
    main()
