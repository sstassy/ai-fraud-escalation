import streamlit as st
import os
import json
import random
import openai
import pandas as pd
import altair as alt
from dotenv import load_dotenv
from datetime import datetime

# Realistic locations and risk-related presets for Random scenario
_LOCATIONS = [
    "Toronto, Canada",
    "New York, USA",
    "London, UK",
    "Sydney, Australia",
    "Unknown overseas IP",
    "VPN / Proxy detected",
    "São Paulo, Brazil",
    "Singapore",
    "Berlin, Germany",
    "Mumbai, India",
]


def init_client():
    load_dotenv()
    return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_random_transaction():
    """Generate realistic transaction details for quick demos (Random scenario)."""
    # Amount: mix of small, medium, large; occasionally very high
    amount_choice = random.choices(
        [random.randint(20, 200), random.randint(250, 1500), random.randint(2000, 8000), random.randint(9000, 25000)],
        weights=[50, 30, 15, 5],
    )[0]
    return {
        "amount": amount_choice,
        "location": random.choice(_LOCATIONS),
        "device_changed": random.choice(["No", "No", "Yes"]),  # bias toward No
        "account_age_months": random.choices(
            [random.randint(1, 6), random.randint(7, 24), random.randint(25, 120)],
            weights=[25, 35, 40],
        )[0],
        "previous_flags": random.choices([0, 1, 2, 3], weights=[70, 18, 8, 4])[0],
        "behavioral_anomaly_score": random.randint(5, 95),
    }


client = init_client()


def render_landing():
    st.set_page_config(page_title="AI Fraud Risk Escalation Engine", layout="wide")

    with st.container():
        col1, col2 = st.columns([1.2, 1])

        with col1:
            st.markdown("##### AI Fraud Risk Escalation")
            st.markdown(
                "<h1 style='font-size:2.5rem;line-height:1.1;margin-bottom:0.4rem;'>"
                "Evaluate <span style='background:linear-gradient(120deg,#2563eb,#22c55e);"
                "-webkit-background-clip:text;color:transparent;'>Smarter, Faster</span>"
                "</h1>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='color:#4b5563;font-size:0.98rem;max-width:34rem;'>"
                "Run evaluations with ease and get actionable insights instantly. "
                "Give your fraud, risk, and compliance teams a calm, guided escalation workflow."
                "</p>",
                unsafe_allow_html=True,
            )

            st.write("")
            col_cta_1, col_cta_2 = st.columns([1.3, 1])
            with col_cta_1:
                if st.button("Start Evaluation", type="primary"):
                    st.session_state["page"] = "evaluation"
                    st.experimental_rerun()
            with col_cta_2:
                st.caption("No credit card required. Start in under 2 minutes.")

            st.write("")
            st.markdown("**Built for** · Fraud Ops · Risk · Compliance")

        with col2:
            st.markdown("###### Workflow preview")
            with st.container(border=True):
                st.caption("High-level flow (placeholder UI)")
                step_cols = st.columns(3)
                with step_cols[0]:
                    st.metric("1. Ingest", "Case data")
                with step_cols[1]:
                    st.metric("2. Evaluate", "Guided Q&A")
                with step_cols[2]:
                    st.metric("3. Decide", "AI insights")
                st.progress(0.6, text="Average time-to-decision reduction")

    st.write("---")

    st.markdown("### Features")
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        st.markdown("#### Step-by-Step Guidance")
        st.caption(
            "Replace scattered checklists with a single guided flow that adapts to each "
            "case and reduces manual errors."
        )
    with f_col2:
        st.markdown("#### Save & Resume")
        st.caption(
            "Pause and pick up where you left off with auto-saved evaluation states "
            "across analysts and handoffs."
        )
    with f_col3:
        st.markdown("#### Export Results")
        st.caption(
            "Generate clean, standardized evaluation summaries ready for PDF, CSV, or "
            "your internal systems."
        )
    with f_col4:
        st.markdown("#### Real-Time Insights")
        st.caption(
            "See instant AI-backed risk signals, confidence levels, and suggested "
            "next steps as you work."
        )

    st.write("---")
    st.markdown("### How it works")
    hw_col1, hw_col2 = st.columns([1, 1])
    with hw_col1:
        st.markdown("1. **Connect your case data**")
        st.caption(
            "Import transaction details, user metadata, and alerts from your fraud stack "
            "or upload a simple file."
        )
        st.markdown("2. **Answer guided questions**")
        st.caption(
            "Follow a structured, configurable flow that keeps coverage consistent "
            "across analysts."
        )
        st.markdown("3. **Review AI insights**")
        st.caption(
            "Surface anomalies, patterns, and suggested escalation paths in real time."
        )
        st.markdown("4. **Share & export**")
        st.caption(
            "Instantly generate a clear, auditable summary for stakeholders and systems."
        )
    with hw_col2:
        st.info(
            "🎥 Product demo placeholder\n\n"
            "Drop GIFs or screenshots of the evaluation experience here."
        )

    st.write("---")
    st.markdown("### What teams are saying (placeholder)")
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.markdown("**Alex Lee** · Head of Fraud Operations")
        st.caption(
            "“Placeholder quote about cutting evaluation times and standardizing reviews "
            "without adding headcount.”"
        )
    with t_col2:
        st.markdown("**Riya Menon** · Director of Risk & Compliance")
        st.caption(
            "“Placeholder quote about having consistent, defensible documentation for "
            "every high-risk escalation.”"
        )


def _get_preset_defaults(preset, session_state):
    """Resolve default transaction values from preset or Random (stored in session).
    Low/High Risk: always return preset values so fields update every time.
    Random: keep last generated set until user clicks 'New random case'.
    """
    if preset == "Low Risk Example":
        return {
            "amount": 120,
            "location": "Toronto, Canada",
            "device_changed": "No",
            "account_age_months": 36,
            "previous_flags": 0,
            "behavioral_anomaly_score": 15,
        }
    if preset == "High Risk Example":
        return {
            "amount": 4800,
            "location": "Unknown overseas IP",
            "device_changed": "Yes",
            "account_age_months": 2,
            "previous_flags": 2,
            "behavioral_anomaly_score": 87,
        }
    if preset == "Random":
        if "random_tx" not in session_state or session_state.get("random_tx") is None:
            session_state["random_tx"] = generate_random_transaction()
        return session_state["random_tx"].copy()
    # Custom
    return {
        "amount": 500,
        "location": "Toronto, Canada",
        "device_changed": "No",
        "account_age_months": 24,
        "previous_flags": 0,
        "behavioral_anomaly_score": 20,
    }


def _run_assessment(user_input):
    """Call OpenAI and return (parsed_dict, None) or (None, error_message)."""
    system_prompt = """
You are a senior fraud risk analyst at a regulated fintech company.

Fraud detection is adversarial and high-stakes.

Your job:
Evaluate structured transaction signals and simulate expert fraud reasoning.

Rules:
- Weigh behavioral anomaly score significantly.
- New device + young account increases risk.
- Prior fraud flags increase risk materially.
- Avoid overreacting to a single weak signal.
- If confidence is below 60%, escalate to human.
- Permanent account freezes require human approval.

Return STRICT JSON only. No explanations outside JSON.

Format:

{
  "risk_score": number (0-100),
  "risk_level": "low | medium | high | critical",
  "recommended_action": "auto_approve | step_up_verification | temporary_freeze | permanent_freeze | escalate_to_human",
  "reasoning": "clear professional explanation referencing signals",
  "confidence": number (0-100),
  "customer_message": "clear, compliant message suitable for regulated environment"
}
"""
    message = f"Transaction data:\n{json.dumps(user_input)}"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        temperature=0.2,
        max_tokens=800,
    )
    result_text = response.choices[0].message.content.strip()
    try:
        json_start = result_text.find("{")
        json_end = result_text.rfind("}") + 1
        return json.loads(result_text[json_start:json_end]), None
    except Exception:
        return None, result_text


def render_evaluation():
    st.set_page_config(page_title="AI Fraud Risk Escalation Engine", layout="wide")

    # ----- Header row: title, scenario -----
    head_col1, head_col2 = st.columns([1, 1.2])
    with head_col1:
        st.markdown("### Evaluation")
    with head_col2:
        preset = st.selectbox(
            "Load Test Scenario",
            ["Custom", "Low Risk Example", "High Risk Example", "Random"],
            key="eval_preset",
        )
        if preset == "Random":
            st.caption("New random values each time you switch to Random.")
    defaults = _get_preset_defaults(preset, st.session_state)

    # When preset changes, force form fields to show that preset's values (Streamlit
    # otherwise keeps the previous widget values in session state).
    # When switching TO Random, generate a new random set so values differ every time.
    last_preset = st.session_state.get("eval_last_preset")
    if last_preset != preset:
        st.session_state["eval_last_preset"] = preset
        if preset == "Random":
            st.session_state["random_tx"] = generate_random_transaction()
            defaults = st.session_state["random_tx"].copy()
        st.session_state["tx_amount"] = defaults["amount"]
        st.session_state["tx_location"] = defaults["location"]
        st.session_state["tx_device"] = defaults["device_changed"]
        st.session_state["tx_age"] = defaults["account_age_months"]
        st.session_state["tx_flags"] = defaults["previous_flags"]
        st.session_state["tx_behavior"] = defaults["behavioral_anomaly_score"]

    # ----- Transaction form + Assess Risk (left column) -----
    tx_col1, tx_col2 = st.columns(2)
    with tx_col1:
        with st.container(border=True):
            st.markdown("**Transaction Details**")
            r1a, r1b = st.columns(2)
            with r1a:
                amount = st.number_input("Amount ($)", value=defaults["amount"], key="tx_amount")
                location = st.text_input("Location", value=defaults["location"], key="tx_location")
            with r1b:
                device_changed = st.selectbox(
                    "New Device?",
                    ["No", "Yes"],
                    index=0 if defaults["device_changed"] == "No" else 1,
                    key="tx_device",
                )
                account_age = st.number_input("Account Age (mo)", value=defaults["account_age_months"], key="tx_age")
            r2a, r2b = st.columns(2)
            with r2a:
                past_flags = st.number_input("Past Flags", value=defaults["previous_flags"], key="tx_flags")
            with r2b:
                behavior_score = st.slider(
                    "Behavior Score (0–100)",
                    0,
                    100,
                    value=defaults["behavioral_anomaly_score"],
                    key="tx_behavior",
                )

        # Button directly below Transaction Details
        assess_clicked = st.button("Assess Risk", type="primary", use_container_width=True, key="assess_risk_btn")

    user_input = {
        "amount": amount,
        "location": location,
        "device_changed": device_changed,
        "account_age_months": account_age,
        "previous_flags": past_flags,
        "behavioral_anomaly_score": behavior_score,
    }

    # ----- Run assessment on button click -----
    if assess_clicked:
        parsed, err = _run_assessment(user_input)
        if err:
            st.session_state["last_assessment_error"] = err
            st.session_state["last_assessment"] = None
        else:
            st.session_state["last_assessment_error"] = None
            human_required = parsed["recommended_action"] in [
                "permanent_freeze",
                "escalate_to_human",
            ]
            st.session_state["last_assessment"] = {
                "parsed": parsed,
                "user_input": user_input,
                "human_decision": None if human_required else "auto",
            }
            if not human_required:
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "input": user_input,
                    "AI_output": parsed,
                    "human_decision": "auto",
                }
                with open("audit_log.txt", "a") as f:
                    f.write(json.dumps(log_entry) + "\n")

    # ----- Assessment Results panel -----
    with tx_col2:
        with st.container(border=True):
            st.markdown("**Assessment Results**")
            last = st.session_state.get("last_assessment")
            err = st.session_state.get("last_assessment_error")
            if err:
                st.error("Failed to parse model response as JSON.")
                st.code(err[:500], language=None)
            elif last:
                p = last["parsed"]
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Risk Score", p["risk_score"])
                m2.metric("Level", p["risk_level"])
                m3.metric("Action", p["recommended_action"])
                m4.metric("Confidence", p["confidence"])
                if last["human_decision"] is None:
                    st.warning("Critical action requires human approval.")
                    if st.button("Approve and log"):
                        st.session_state["last_assessment"]["human_decision"] = "approved"
                        log_entry = {
                            "timestamp": datetime.utcnow().isoformat(),
                            "input": last["user_input"],
                            "AI_output": p,
                            "human_decision": "approved",
                        }
                        with open("audit_log.txt", "a") as f:
                            f.write(json.dumps(log_entry) + "\n")
                        st.rerun()
                else:
                    with st.expander("Reasoning"):
                        st.caption(p["reasoning"])
                    with st.expander("Customer message"):
                        st.caption(p["customer_message"])
            else:
                st.caption("Run **Assess Risk** to see results here.")

    # ----- Bottom row: Audit Log | Risk Trend Chart -----
    st.markdown("")  # spacing
    log_col, chart_col = st.columns([1, 1])

    with log_col:
        st.markdown("**Audit Log**")
        logs = []
        if os.path.exists("audit_log.txt"):
            with open("audit_log.txt", "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        if logs:
            df = pd.DataFrame(
                [
                    {
                        "Amount": log["input"]["amount"],
                        "Location": log["input"]["location"][:20],
                        "Device": log["input"]["device_changed"],
                        "Age": log["input"]["account_age_months"],
                        "Flags": log["input"]["previous_flags"],
                        "Score": log["input"]["behavioral_anomaly_score"],
                        "Risk": log.get("AI_output", log.get("output", {})).get("risk_score"),
                        "Level": log.get("AI_output", log.get("output", {})).get("risk_level"),
                        "Action": (log.get("AI_output", log.get("output", {})) or {}).get("recommended_action", ""),
                        "Human": log.get("human_decision", ""),
                    }
                    for log in logs
                ]
            )
            st.dataframe(df, use_container_width=True, height=200)
            csv_data = pd.DataFrame(
                [
                    {
                        **log["input"],
                        **(log.get("AI_output") or log.get("output") or {}),
                        "human_decision": log.get("human_decision", ""),
                    }
                    for log in logs
                ]
            )
            st.download_button(
                "Download CSV",
                csv_data.to_csv(index=False),
                "audit_log.csv",
                key="dl_audit",
            )
            if st.button("Clear Audit Log", key="clear_log"):
                os.remove("audit_log.txt")
                if "last_assessment" in st.session_state:
                    del st.session_state["last_assessment"]
                st.rerun()
        else:
            st.info("No audit logs yet.")

    with chart_col:
        st.markdown("**Risk Trend**")
        if logs:
            chart_df = pd.DataFrame(
                [
                    {
                        "index": i,
                        "Risk Score": log.get("AI_output", log.get("output", {})).get("risk_score"),
                        "Risk Level": log.get("AI_output", log.get("output", {})).get("risk_level"),
                    }
                    for i, log in enumerate(logs)
                ]
            )
            chart_df = chart_df.dropna(subset=["Risk Score"])
            if not chart_df.empty:
                chart = (
                    alt.Chart(chart_df)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("index", title="Transaction #"),
                        y=alt.Y("Risk Score", title="Risk Score", scale=alt.Scale(domain=[0, 100])),
                        color="Risk Level",
                    )
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.caption("No risk scores in log yet.")
        else:
            st.caption("Run assessments to see the risk trend here.")


def main():
    if "page" not in st.session_state:
        st.session_state["page"] = "landing"

    with st.sidebar:
        st.markdown("### AI Fraud Risk Escalation")
        page = st.radio(
            "Navigate",
            options=["Landing", "Evaluation"],
            index=0 if st.session_state["page"] == "landing" else 1,
        )
        st.markdown("---")
        st.caption(
            "Use the landing page to introduce the app, then switch to Evaluation "
            "to run live fraud risk reviews."
        )

    if page == "Landing":
        st.session_state["page"] = "landing"
        render_landing()
    else:
        st.session_state["page"] = "evaluation"
        render_evaluation()


if __name__ == "__main__":
    main()
