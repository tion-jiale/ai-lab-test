# app.py
import json
from typing import List, Dict, Any, Tuple
import operator
import streamlit as st




OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
}

DEFAULT_RULES: List[Dict[str, Any]] = [
    {
        "name": "Windows open\u2192 turn AC off",
        "priority": 100,
        "conditions": [
            ["windows_open", "==", True]
        ],
        "action": {"ac_mode": "OFF", 
                   "fan_speed": "LOW",
                   "setpoint": None,
                   "reason": "Windows are open"},
    },
    {
        "name": "No one home \u2192 eco mode",
        "priority": 90,
        "conditions": [
            ["occupancy", "==", "EMPTY"],
            ["temperature", ">=", 24]
        ],
        "action": {"ac_mode": "ECO", 
                   "fan_speed": "LOW",
                   "setpoint": 27,
                   "reason": "Home empty; save energy"},
    },
    {
        "name": "Hot & humid (occupied) \u2192 cool strong",
        "priority": 80,
        "conditions": [
            ["occupancy", "==", "OCCUPIED"],
            ["temperature", ">=", 30],
            ["humidity", ">=", 70]
        ],
        "action": {"ac_mode": "COOL", 
                   "fan_speed": "HIGH",
                   "setpoint": 23,
                   "reason": "Hot and humid"},
    },
    {
        "name": "Hot (occupied) \u2192 cool",
        "priority": 70,
        "conditions": [
            ["occupancy", "==", "OCCUPIED"],
            ["temperature", ">=", 28],
        ],
        "action": {"ac_mode": "COOL", 
                   "fan_speed": "MEDIUM",
                   "setpoint": 24,
                   "reason": "Temperature high"},
    },
    {
        "name": "Slightly warm (occupied) \u2192 gentle cool",
        "priority": 60,
        "conditions": [
            ["occupancy", "==", "OCCUPIED"],
            ["temperature", ">=", 26],
            ["temperature", "<", 28],
        ],
        "action": {"ac_mode": "COOL", 
                   "fan_speed": "LOW",
                   "setpoint": 25,
                   "reason": "Slightly warm"},
    },
    {
        "name": "Night (occupied) \u2192 sleep mode",
        "priority": 75,
        "conditions": [
            ["occupancy", "==", "OCCUPIED"],
            ["time_of_day", "==", "NIGHT"],
            ["temperature", ">=", 26],
        ],
        "action": {"ac_mode": "SLEEP", 
                   "fan_speed": "LOW",
                   "setpoint": 26,
                   "reason": "Night comfort"},
    },
    {
        "name": "Too cold \u2192 turn off",
        "priority": 85,
        "conditions": [
            ["temperature", "<=", 22]
        ],
        "action": {"ac_mode": "OFF", 
                   "fan_speed": "LOW",
                   "setpoint": None,
                   "reason": "Already cold"}
    }
]

def evaluate_condition(facts: Dict[str, Any], cond: List[Any]) -> bool:
    """Evaluate a single condition: [field, op, value]."""
    if len(cond) != 3:
        return False
    field, op, value = cond
    if field not in facts or op not in OPS:
        return False
    try:
        return OPS[op](facts[field], value)
    except Exception:
        return False

def rule_matches(facts: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    """All conditions must be true (AND)."""
    return all(evaluate_condition(facts, c) for c in rule.get("conditions", []))

def run_rules(facts: Dict[str, Any], rules: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Returns (best_action, fired_rules)
    - best_action: chosen by highest priority among fired rules (ties keep the first encountered)
    - fired_rules: list of rule dicts that matched
    """
    fired = [r for r in rules if rule_matches(facts, r)]
    if not fired:
        return ({"decision": "REVIEW", "reason": "No rule matched"}, [])

    fired_sorted = sorted(fired, key=lambda r: r.get("priority", 0), reverse=True)
    best = fired_sorted[0].get("action", {"decision": "REVIEW", "reason": "No action"})
    return best, fired_sorted

# ----------------------------
# 2) Streamlit UI
# ----------------------------
st.set_page_config(page_title="Rule-Based System (Streamlit)", page_icon="", layout="wide")
st.title("Simple Rule-Based System (AC Controller)")
st.caption("Enter applicant data, edit rules (optional), and evaluate. Designed to be a small, deployable example.")

with st.sidebar:
    st.header("Temperature Facts")
    temperature = st.number_input("Temperature (°C)", min_value=10, max_value=40, step=1, value=25)
    occupancy = st.selectbox("Occupancy", ["OCCUPIED", "EMPTY"], index=0)
    humidity = st.number_input("Humidity (%)", min_value=0, max_value=100, step=1, value=50)
    time_of_day = st.selectbox("Time of Day", ["MORNING","AFTERNOON","EVENING","NIGHT"], index=0)
    windows_open = st.selectbox("Windows Open", ["True", "False"], index=1)

    st.divider()
    st.header("Rules (JSON)")
    st.caption("You can keep the defaults or paste your own JSON array of rules.")    
    default_json = json.dumps(DEFAULT_RULES, indent=2)
    rules_text = st.text_area("Edit rules here", value=default_json, height=300)

    run = st.button("Evaluate", type="primary")

facts = {
    "temperature": float(temperature),
    "occupancy": occupancy,
    "humidity": float(humidity),
    "time_of_day": time_of_day,
    "windows_open": windows_open == "True",
}

st.subheader("Applicant Facts")
st.json(facts)

# Parse rules (fall back to defaults if invalid)
try:
    rules = json.loads(rules_text)
    assert isinstance(rules, list), "Rules must be a JSON array"
except Exception as e:
    st.error(f"Invalid rules JSON. Using defaults. Details: {e}")
    rules = DEFAULT_RULES

st.subheader("Active Rules")
with st.expander("Show rules", expanded=False):
    st.code(json.dumps(rules, indent=2), language="json")

st.divider()

if run:
    action, fired = run_rules(facts, rules)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Decision")
        badge = action.get("decision", "REVIEW")
        reason = action.get("reason", "-")
        if badge == "APPROVE":
            st.success(f"APPROVE — {reason}")
        elif badge == "REJECT":
            st.error(f"REJECT — {reason}")
        else:
            st.warning(f"REVIEW — {reason}")

    with col2:
        st.subheader("Matched Rules (by priority)")
        if not fired:
            st.info("No rules matched.")
        else:
            for i, r in enumerate(fired, start=1):
                st.write(f"**{i}. {r.get('name','(unnamed)')}** | priority={r.get('priority',0)}")
                st.caption(f"Action: {r.get('action',{})}")
                with st.expander("Conditions"):
                    for cond in r.get("conditions", []):
                        st.code(str(cond))

else:
    st.info("Set input values and click **Evaluate**.")
