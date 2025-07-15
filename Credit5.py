import streamlit as st
import pandas as pd

st.set_page_config(page_title="Energy Customer Credit Decision Engine", layout="centered")

st.title("⚡ Energy Customer Credit Decision Engine")

st.markdown("## 🔧 Adjust Scoring Weights")

# --- Editable Weights ---
weight_creditsafe = st.slider("Weight: Creditsafe Score", 0.0, 1.0, 0.4, 0.05)
weight_years_trading = st.slider("Weight: Years Trading", 0.0, 1.0, 0.15, 0.05)
weight_sector_risk = st.slider("Weight: Sector Risk", 0.0, 1.0, 0.15, 0.05)
weight_annual_consumption = st.slider("Weight: Annual Consumption", 0.0, 1.0, 0.15, 0.05)
weight_contract_value = st.slider("Weight: Contract Value", 0.0, 1.0, 0.15, 0.05)

weights = {
    "creditsafe": weight_creditsafe,
    "years_trading": weight_years_trading,
    "sector_risk": weight_sector_risk,
    "annual_consumption": weight_annual_consumption,
    "contract_value": weight_contract_value
}

st.markdown("## 🛡️ Set Decision Thresholds")
approve_threshold = st.slider("Threshold: Approve if Total Score >=", 0, 100, 80)
stipulations_threshold = st.slider("Threshold: Approve with Stipulations if Total Score >=", 0, 100, 60)
refer_threshold = st.slider("Threshold: Refer if Total Score >=", 0, 100, 40)

thresholds = {
    "approve": approve_threshold,
    "stipulations": stipulations_threshold,
    "refer": refer_threshold
}

st.markdown("## 📋 Enter Customer Details")

creditsafe_score = st.number_input("Creditsafe Score (0-100)", min_value=0, max_value=100, value=75)
years_trading = st.number_input("Years Trading", min_value=0, max_value=100, value=3)
sector_risk = st.selectbox("Sector Risk", ["Low", "Medium", "High", "Very High"], index=1)
annual_consumption = st.number_input("Annual Consumption (MWh)", min_value=0.0, value=200.0, step=1.0)
contract_value = st.number_input("Contract Value (£)", min_value=0.0, value=30000.0, step=1000.0)

inputs = {
    'creditsafe_score': creditsafe_score,
    'years_trading': years_trading,
    'sector_risk': sector_risk,
    'annual_consumption_mwh': annual_consumption,
    'contract_value': contract_value
}

# --- Credit Decision Engine ---
def credit_decision_engine():
    def score_creditsafe(cs):
        if cs >= 80:
            return 100
        elif cs >= 60:
            return 75
        elif cs >= 40:
            return 50
        else:
            return 25

    def score_years_trading(yt):
        if yt > 5:
            return 100
        elif yt >= 2:
            return 75
        elif yt >= 1:
            return 50
        else:
            return 25

    def score_sector(sr):
        mapping = {"Low": 100, "Medium": 75, "High": 50, "Very High": 25}
        return mapping.get(sr, 50)

    def score_consumption(mwh):
        if mwh < 100:
            return 100
        elif mwh <= 250:
            return 75
        elif mwh <= 500:
            return 50
        else:
            return 25

    def score_contract_value(val):
        if val < 25000:
            return 100
        elif val <= 50000:
            return 75
        elif val <= 100000:
            return 50
        else:
            return 25

    s1 = score_creditsafe(inputs['creditsafe_score']) * weights['creditsafe']
    s2 = score_years_trading(inputs['years_trading']) * weights['years_trading']
    s3 = score_sector(inputs['sector_risk']) * weights['sector_risk']
    s4 = score_consumption(inputs['annual_consumption_mwh']) * weights['annual_consumption']
    s5 = score_contract_value(inputs['contract_value']) * weights['contract_value']

    total_score = s1 + s2 + s3 + s4 + s5

    if total_score >= thresholds['approve']:
        decision = "✅ Approved"
    elif total_score >= thresholds['stipulations']:
        decision = "⚠️ Approved with Stipulations"
    elif total_score >= thresholds['refer']:
        decision = "🔍 Refer / Manual Review"
    else:
        decision = "❌ Decline"

    return {
        "decision": decision,
        "total_score": round(total_score, 1),
        "criteria_scores": {
            "Creditsafe": round(s1, 1),
            "Years Trading": round(s2, 1),
            "Sector Risk": round(s3, 1),
            "Annual Consumption": round(s4, 1),
            "Contract Value": round(s5, 1)
        }
    }

if st.button("Run Credit Decision"):
    with st.spinner("Calculating..."):
        result = credit_decision_engine()
        st.success(f"**Decision: {result['decision']}**")
        st.metric("Total Score", result["total_score"])
        st.subheader("Breakdown of Scores")
        st.json(result["criteria_scores"])
