import streamlit as st
import pandas as pd

st.set_page_config(page_title="Energy Customer Credit Decision Engine", layout="centered")

st.title("⚡ Energy Customer Credit Decision Engine")

st.markdown("Enter customer details below to assess credit decision:")

# --- Input Grid ---
def get_default_data():
    return pd.DataFrame({
        'Criteria': ['Creditsafe Score', 'Years Trading', 'Sector Risk', 'Annual Consumption (MWh)', 'Contract Value (£)'],
        'Value': [75, 3, 'Medium', 200, 30000]
    })

def get_default_weights():
    return {
        "creditsafe": 0.4,
        "years_trading": 0.15,
        "sector_risk": 0.15,
        "annual_consumption": 0.15,
        "contract_value": 0.15
    }

def get_default_thresholds():
    return {
        "approve": 80,
        "stipulations": 60,
        "refer": 40
    }

def credit_decision_engine(inputs, weights, thresholds):
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

# Display editable grid
data = get_default_data()
edited_data = st.data_editor(data, num_rows="fixed")

# Map inputs
inputs = {
    'creditsafe_score': int(edited_data.loc[edited_data['Criteria'] == 'Creditsafe Score', 'Value'].values[0]),
    'years_trading': int(edited_data.loc[edited_data['Criteria'] == 'Years Trading', 'Value'].values[0]),
    'sector_risk': edited_data.loc[edited_data['Criteria'] == 'Sector Risk', 'Value'].values[0],
    'annual_consumption_mwh': float(edited_data.loc[edited_data['Criteria'] == 'Annual Consumption (MWh)', 'Value'].values[0]),
    'contract_value': float(edited_data.loc[edited_data['Criteria'] == 'Contract Value (£)', 'Value'].values[0])
}

weights = get_default_weights()
thresholds = get_default_thresholds()

if st.button("Run Credit Decision"):
    with st.spinner("Calculating..."):
        result = credit_decision_engine(inputs, weights, thresholds)
        st.success(f"**Decision: {result['decision']}**")
        st.metric("Total Score", result["total_score"])
        st.subheader("Breakdown of Scores")
        st.json(result["criteria_scores"])
