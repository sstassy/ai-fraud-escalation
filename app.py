import streamlit as st
import os
import json
import openai
import pandas as pd
import altair as alt
from dotenv import load_dotenv
from datetime import datetime

# Load API key
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Page setup
st.set_page_config(page_title="AI Fraud Risk Escalation Engine", layout="wide")
st.title("AI-Native Fraud Risk Escalation Engine")
st.markdown("Simulating senior-level fraud triage with AI-supported escalation.")

st.subheader("Transaction Details")

# Preset scenarios
preset = st.selectbox(
    "Load Test Scenario",
    ["Custom", "Low Risk Example", "High Risk Example"]
)

# Default values
default_amount = 500
default_location = "Toronto, Canada"
default_device_changed = "No"
default_account_age = 24
default_past_flags = 0
default_behavior_score = 20

# Preset overrides
if preset == "Low Risk Example":
    default_amount = 120
    default_location = "Toronto, Canada"
    default_device_changed = "No"
    default_account_age = 36
    default_past_flags = 0
    default_behavior_score = 15
elif preset == "High Risk Example":
    default_amount = 4800
    default_location = "Unknown overseas IP"
    default_device_changed = "Yes"
    default_account_age = 2
    default_past_flags = 2
    default_behavior_score = 87

# Render input fields (always editable)
amount = st.number_input("Transaction Amount ($)", value=default_amount)
location = st.text_input("Transaction Location", value=default_location)
device_changed = st.selectbox(
    "New Device?", 
    ["No", "Yes"], 
    index=0 if default_device_changed=="No" else 1
)
account_age = st.number_input("Account Age (months)", value=default_account_age)
past_flags = st.number_input("Previous Fraud Flags", value=default_past_flags)
behavior_score = st.slider("Behavioral Anomaly Score (0-100)", 0, 100, value=default_behavior_score)

# Button to assess risk
if st.button("Assess Risk"):

    user_input = {
        "amount": amount,
        "location": location,
        "device_changed": device_changed,
        "account_age_months": account_age,
        "previous_flags": past_flags,
        "behavioral_anomaly_score": behavior_score
    }

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

    # Call OpenAI API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        temperature=0.2,
        max_tokens=800
    )

    result_text = response.choices[0].message.content.strip()

    # Extract JSON safely
    try:
        json_start = result_text.find("{")
        json_end = result_text.rfind("}") + 1
        json_string = result_text[json_start:json_end]
        parsed = json.loads(json_string)

        # Stage 1: Automatic actions for low/medium risk
        auto_executed = False
        human_required = False

        if parsed["recommended_action"] in ["auto_approve", "step_up_verification", "temporary_freeze"]:
            auto_executed = True
            st.success(f"✅ Automatic Action Executed: {parsed['recommended_action']}")
        elif parsed["recommended_action"] in ["permanent_freeze", "escalate_to_human"]:
            human_required = True

        # Stage 2: Human approval for critical actions
        human_decision = None
        if human_required:
            st.warning("⚠️ Critical Action Requires Human Approval")
            st.markdown(
                f"**AI Recommendation:** {parsed['recommended_action']}  \n"
                f"**Reasoning:** {parsed['reasoning']}  \n"
                f"**Confidence:** {parsed['confidence']}"
            )
            if st.checkbox("Approve this critical action"):
                human_decision = "approved"
                st.success("Action approved ✅. Proceeding...")
            else:
                human_decision = "pending"
                st.info("Action pending human approval. No automated execution.")

        # Stage 3: Display Risk Assessment
        st.subheader("Risk Assessment")
        st.metric("Risk Score", parsed["risk_score"])
        st.write("**Risk Level:**", parsed["risk_level"])
        st.write("**Recommended Action:**", parsed["recommended_action"])
        st.write("**Confidence:**", parsed["confidence"])
        st.markdown("### Reasoning")
        st.write(parsed["reasoning"])
        st.markdown("### Customer Communication Draft")
        st.write(parsed["customer_message"])

        # Audit logging with human decision
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "input": user_input,
            "AI_output": parsed,
            "human_decision": human_decision
        }
        with open("audit_log.txt", "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    except Exception as e:
        st.error("Failed to parse model response as JSON.")
        st.write(result_text)

# ------------------- Audit Log Viewer -------------------
st.subheader("Audit Log")

logs = []
if os.path.exists("audit_log.txt"):
    with open("audit_log.txt", "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue  # skip empty lines
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                st.warning(f"Skipped corrupted log line: {line[:50]}...")

    if logs:
        # Prepare dataframe safely, supports old logs too
        df = pd.DataFrame([{
            "Amount": log["input"]["amount"],
            "Location": log["input"]["location"],
            "Device Changed": log["input"]["device_changed"],
            "Account Age": log["input"]["account_age_months"],
            "Past Flags": log["input"]["previous_flags"],
            "Behavior Score": log["input"]["behavioral_anomaly_score"],
            "Risk Score": log.get("AI_output", log.get("output", {})).get("risk_score", None),
            "Risk Level": log.get("AI_output", log.get("output", {})).get("risk_level", None),
            "Action": log.get("AI_output", log.get("output", {})).get("recommended_action", None),
            "Human Decision": log.get("human_decision", "")
        } for log in logs])

        st.dataframe(df)

        # CSV download
        csv_data = pd.DataFrame([{
            **log["input"],
            **log.get("AI_output", log.get("output", {})),
            "human_decision": log.get("human_decision", "")
        } for log in logs])
        st.download_button("Download Audit Log CSV", csv_data.to_csv(index=False), "audit_log.csv")

        # Risk score chart
        chart = alt.Chart(df.reset_index()).mark_line(point=True).encode(
            x=alt.X('index', title='Transaction #'),
            y=alt.Y('Risk Score', title='Risk Score'),
            color='Risk Level'
        )
        st.altair_chart(chart, use_container_width=True)

        # Button to clear logs safely
        if st.button("Clear Audit Log"):
            os.remove("audit_log.txt")
            st.success("Audit log cleared. Please reload the page.")
            st.stop()  # stops script, forces Streamlit to refresh
    else:
        st.info("No audit logs yet.")
else:
    st.info("No audit logs yet.")