import streamlit as st

st.set_page_config(page_title="Energy Customer Credit Decision Engine", layout="centered")

st.title("⚡ Energy Customer Credit Decision Engine")

st.markdown("## 🏢 Enter Business Information")

business_name = st.text_input("Business Name")
company_reg = st.text_input("Company Registration Number (if applicable)")

st.markdown("## 1️⃣ Enter Customer Data")

creditsafe_score = st.number_input("Creditsafe Score (0-100)", min_value=0, max_value=100, value=75)
years_trading = st.number_input("Years Trading", min_value=0, max_value=100, value=3)
sector_risk = st.selectbox("Sector Risk", ["Low", "Medium", "High", "Very High"], index=1)
annual_consumption = st.number_input("Annual Consumption (MWh)", min_value=0.0, value=200.0, step=1.0)
contract_value = st.number_input("Contract Value (£)", min_value=0.0, value=30000.0, step=1000.0)

st.markdown("## 2️⃣ Adjust Scoring Weights")

weight_creditsafe = st.number_input("Weight: Creditsafe Score", min_value=0.0, max_value=1.0, value=0.4, step=0.01)
weight_years_trading = st.number_input("Weight: Years Trading", min_value=0.0, max_value=1.0, value=0.15, step=0.01)
weight_sector_risk = st.number_input("Weight: Sector Risk", min_value=0.0, max_value=1.0, value=0.15, step=0.01)
weight_annual_consumption = st.number_input("Weight: Annual Consumption", min_value=0.0, max_value=1.0, value=0.15, step=0.01)
weight_contract_value = st.number_input("Weight: Contract Value", min_value=0.0, max_value=1.0, value=0.15, step=0.01)

st.markdown("## 3️⃣ Set Decision Thresholds")

approve_threshold = st.number_input("Threshold for Approved", min_value=0, max_value=100, value=80)
stipulations_threshold = st.number_input("Threshold for Approved with Stipulations", min_value=0, max_value=100, value=60)
refer_threshold = st.number_input("Threshold for Refer / Manual Review", min_value=0, max_value=100, value=40)

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

    s1 = score_creditsafe(creditsafe_score) * weight_creditsafe
    s2 = score_years_trading(years_trading) * weight_years_trading
    s3 = score_sector(sector_risk) * weight_sector_risk
    s4 = score_consumption(annual_consumption) * weight_annual_consumption
    s5 = score_contract_value(contract_value) * weight_contract_value

    total_score = s1 + s2 + s3 + s4 + s5

    if total_score >= approve_threshold:
        decision = "✅ Approved"
    elif total_score >= stipulations_threshold:
        decision = "⚠️ Approved with Stipulations"
    elif total_score >= refer_threshold:
        decision = "🔍 Refer / Manual Review"
    else:
        decision = "❌ Decline"

    messages = []

    if contract_value > 250000:
        messages.append("The contract value requires authorisation at Director level.")
    elif contract_value > 100000:
        messages.append("The contract value requires authorisation from the Commercial Manager.")

    if decision == "🔍 Refer / Manual Review":
        messages.append("Please refer this to the Commercial Team for approval.")

    return {
        "decision": decision,
        "total_score": round(total_score, 1),
        "messages": messages
    }

if st.button("Run Credit Decision"):
    with st.spinner("Calculating..."):
        result = credit_decision_engine()
        st.success(f"**Decision: {result['decision']}**")
        st.metric("Total Score", result["total_score"])
        
        st.markdown(f"**Business Name:** {business_name}")
        if company_reg:
            st.markdown(f"**Company Reg Number:** {company_reg}")

        if result['messages']:
            st.subheader("Additional Notes")
            for msg in result['messages']:
                st.info(msg)
