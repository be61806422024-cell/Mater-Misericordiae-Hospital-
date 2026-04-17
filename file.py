import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ------------------------------
# Page configuration
st.set_page_config(page_title="Mater Hospital Audit Dashboard", layout="wide")

# ------------------------------
# Dashboard title and subtitle
st.title("🏥 Mater Hospital Internal Audit Follow-Up Dashboard")
st.markdown("#### By Musewe Analytics")
st.markdown("---")

# ------------------------------
# Load and prepare data (based on provided table)
data = {
    "DEPARTMENT": [
        "LABORATORY", "REVENUE REVERSALS", "PHARMACY", "REVENUE CYCLE MANAGEMENT",
        "SUPPLY CHAIN MANAGEMENT", "ACCOUNTS PAYABLE", "MATER HEARTRUN",
        "FACILITIES MANAGEMENT", "PAYROLL", "RECRUITMENT & ONBOARDING",
        "CAFETERIA", "MEDICAL CENTRES", "SCHOOL OF NURSING"
    ],
    "RECOMMENDED_ISSUES": [20, 10, 16, 15, 15, 17, 27, 16, 10, 9, 21, 22, 14],
    "YEAR_OF_ISSUE": [2025, 2025, 2025, 2024, 2024, 2025, 2025, 2025, 2025, 2025, 2024, 2025, 2025],
    "HIGH": [16, 6, 16, 12, 15, 13, 25, 15, 9, 5, 20, 17, 11],
    "MEDIUM": [4, 4, 0, 3, 0, 4, 2, 1, 1, 4, 1, 5, 3],
    "FULLY_IMPLEMENTED": [0, 0, 0, 0, 0, 4, 0, 8, 0, 0, 0, 0, 1],
    "PARTIALLY_IMPLEMENTED": [0, 0, 0, 8, 0, 10, 0, 6, 0, 0, 0, 0, 13],
    "NOT_IMPLEMENTED": [0, 0, 0, 6, 0, 3, 0, 2, 0, 0, 0, 0, 0],
    "NOT_DUE": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
}

df = pd.DataFrame(data)

# Calculate percentage of implementation (weighted: fully = 1, partially = 0.5)
df["IMPLEMENTATION_PERCENT"] = (
    (df["FULLY_IMPLEMENTED"] + 0.5 * df["PARTIALLY_IMPLEMENTED"]) / df["RECOMMENDED_ISSUES"]
) * 100
df["IMPLEMENTATION_PERCENT"] = df["IMPLEMENTATION_PERCENT"].round(1).fillna(0)

# Outstanding issues = Total - Fully Implemented
df["OUTSTANDING_ISSUES"] = df["RECOMMENDED_ISSUES"] - df["FULLY_IMPLEMENTED"]

# ------------------------------
# Sidebar filters
st.sidebar.header("🔍 Filter Dashboard")

# Department filter (allows multiple)
dept_list = df["DEPARTMENT"].unique()
selected_depts = st.sidebar.multiselect("Select Department(s)", dept_list, default=dept_list)

# Year filter
year_list = sorted(df["YEAR_OF_ISSUE"].unique())
selected_years = st.sidebar.multiselect("Select Year(s) of Issue", year_list, default=year_list)

# Risk filter (high/medium)
risk_options = ["High", "Medium"]
selected_risks = st.sidebar.multiselect("Select Risk Category", risk_options, default=risk_options)

# Filter the dataframe
filtered_df = df[
    (df["DEPARTMENT"].isin(selected_depts)) &
    (df["YEAR_OF_ISSUE"].isin(selected_years))
]

# For risk-related visuals we need separate handling because risk counts are in columns.
# We'll create a filtered version for risk plots that respects department/year but not risk filter (since we show both)
risk_filtered_df = filtered_df.copy()
if "High" not in selected_risks:
    risk_filtered_df["HIGH"] = 0
if "Medium" not in selected_risks:
    risk_filtered_df["MEDIUM"] = 0

# ------------------------------
# Executive Summary KPIs
st.header("📊 Executive Summary")
col1, col2, col3, col4 = st.columns(4)

total_issues = filtered_df["RECOMMENDED_ISSUES"].sum()
high_risk = filtered_df["HIGH"].sum()
medium_risk = filtered_df["MEDIUM"].sum()
fully_imp = filtered_df["FULLY_IMPLEMENTED"].sum()
partially_imp = filtered_df["PARTIALLY_IMPLEMENTED"].sum()
not_imp = filtered_df["NOT_IMPLEMENTED"].sum()

# Percentages
fully_pct = (fully_imp / total_issues * 100) if total_issues > 0 else 0
partially_pct = (partially_imp / total_issues * 100) if total_issues > 0 else 0
not_imp_pct = (not_imp / total_issues * 100) if total_issues > 0 else 0

# Overall implementation rate (weighted)
overall_impl = (fully_imp + 0.5 * partially_imp) / total_issues * 100 if total_issues > 0 else 0

with col1:
    st.metric("Total Audit Issues", f"{total_issues}")
    st.metric("High-Risk Issues", f"{high_risk}", delta=None, delta_color="inverse")
    st.metric("Medium-Risk Issues", f"{medium_risk}")
with col2:
    st.metric("✅ Fully Implemented", f"{fully_imp} ({fully_pct:.1f}%)")
    st.metric("🔄 Partially Implemented", f"{partially_imp} ({partially_pct:.1f}%)")
with col3:
    st.metric("❌ Not Implemented", f"{not_imp} ({not_imp_pct:.1f}%)")
with col4:
    st.metric("📈 Overall Implementation Rate", f"{overall_impl:.1f}%")
st.markdown("---")

# ------------------------------
# 2. Risk Analysis
st.header("⚠️ Risk Analysis")
col_risk1, col_risk2 = st.columns(2)

with col_risk1:
    # Pie chart: High vs Medium risk distribution
    risk_counts = [risk_filtered_df["HIGH"].sum(), risk_filtered_df["MEDIUM"].sum()]
    risk_labels = ["High Risk", "Medium Risk"]
    fig_risk_pie = px.pie(
        values=risk_counts,
        names=risk_labels,
        title="Distribution of Risk Ratings",
        color_discrete_map={"High Risk": "#d62728", "Medium Risk": "#ff7f0e"},
        hole=0.3
    )
    st.plotly_chart(fig_risk_pie, use_container_width=True)

with col_risk2:
    # Bar chart: High-risk issues by department
    high_risk_by_dept = risk_filtered_df.groupby("DEPARTMENT")["HIGH"].sum().reset_index()
    high_risk_by_dept = high_risk_by_dept[high_risk_by_dept["HIGH"] > 0].sort_values("HIGH", ascending=False)
    if not high_risk_by_dept.empty:
        fig_high_bar = px.bar(
            high_risk_by_dept,
            x="DEPARTMENT",
            y="HIGH",
            title="High-Risk Issues by Department",
            labels={"HIGH": "Number of High-Risk Issues", "DEPARTMENT": ""},
            color="HIGH",
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig_high_bar, use_container_width=True)
    else:
        st.info("No high-risk issues in selected filters.")
st.markdown("---")

# ------------------------------
# 3. Implementation Status
st.header("📋 Implementation Status")
col_impl1, col_impl2 = st.columns(2)

with col_impl1:
    # Stacked bar chart by department
    dept_impl = filtered_df.melt(
        id_vars=["DEPARTMENT"],
        value_vars=["FULLY_IMPLEMENTED", "PARTIALLY_IMPLEMENTED", "NOT_IMPLEMENTED"],
        var_name="Status",
        value_name="Count"
    )
    dept_impl["Status"] = dept_impl["Status"].replace({
        "FULLY_IMPLEMENTED": "Fully Implemented",
        "PARTIALLY_IMPLEMENTED": "Partially Implemented",
        "NOT_IMPLEMENTED": "Not Implemented"
    })
    # Filter out departments with zero counts for cleaner chart
    dept_impl = dept_impl[dept_impl["Count"] > 0]
    if not dept_impl.empty:
        fig_stack = px.bar(
            dept_impl,
            x="DEPARTMENT",
            y="Count",
            color="Status",
            title="Implementation Status by Department",
            barmode="stack",
            color_discrete_map={
                "Fully Implemented": "#2ca02c",
                "Partially Implemented": "#ffc107",
                "Not Implemented": "#d62728"
            }
        )
        st.plotly_chart(fig_stack, use_container_width=True)
    else:
        st.info("No implementation data for selected filters.")

with col_impl2:
    # Pie chart: overall implementation status distribution
    overall_status = {
        "Fully Implemented": fully_imp,
        "Partially Implemented": partially_imp,
        "Not Implemented": not_imp
    }
    status_df = pd.DataFrame(list(overall_status.items()), columns=["Status", "Count"])
    status_df = status_df[status_df["Count"] > 0]
    if not status_df.empty:
        fig_status_pie = px.pie(
            status_df,
            values="Count",
            names="Status",
            title="Overall Implementation Status",
            color="Status",
            color_discrete_map={
                "Fully Implemented": "#2ca02c",
                "Partially Implemented": "#ffc107",
                "Not Implemented": "#d62728"
            },
            hole=0.3
        )
        st.plotly_chart(fig_status_pie, use_container_width=True)
    else:
        st.info("No implementation data.")
st.markdown("---")

# ------------------------------
# 4. Department Performance
st.header("🏆 Department Performance")

# Prepare performance table
perf_df = filtered_df[["DEPARTMENT", "RECOMMENDED_ISSUES", "IMPLEMENTATION_PERCENT"]].copy()
perf_df = perf_df.sort_values("IMPLEMENTATION_PERCENT", ascending=False).reset_index(drop=True)

# Highlight best and worst
best_dept = perf_df.iloc[0]["DEPARTMENT"] if not perf_df.empty else "None"
best_pct = perf_df.iloc[0]["IMPLEMENTATION_PERCENT"] if not perf_df.empty else 0
worst_dept = perf_df.iloc[-1]["DEPARTMENT"] if not perf_df.empty else "None"
worst_pct = perf_df.iloc[-1]["IMPLEMENTATION_PERCENT"] if not perf_df.empty else 0

col_perf1, col_perf2 = st.columns(2)
with col_perf1:
    st.metric("🏅 Best Performing Department", f"{best_dept}", delta=f"{best_pct:.1f}% implementation")
with col_perf2:
    st.metric("⚠️ Worst Performing Department", f"{worst_dept}", delta=f"{worst_pct:.1f}% implementation")

# Bar chart ranking
fig_rank = px.bar(
    perf_df,
    x="DEPARTMENT",
    y="IMPLEMENTATION_PERCENT",
    title="Implementation Percentage by Department (Ranked)",
    labels={"IMPLEMENTATION_PERCENT": "Implementation (%)", "DEPARTMENT": ""},
    color="IMPLEMENTATION_PERCENT",
    color_continuous_scale="RdYlGn",
    range_color=[0, 100]
)
st.plotly_chart(fig_rank, use_container_width=True)

# Table with detailed performance
st.subheader("Department Performance Table")
st.dataframe(
    perf_df.style.format({"IMPLEMENTATION_PERCENT": "{:.1f}%"}),
    use_container_width=True
)
st.markdown("---")

# ------------------------------
# 5. Outstanding Issues / Gap Analysis
st.header("📌 Outstanding Issues (Gap Analysis)")
filtered_df["OUTSTANDING_ISSUES"] = filtered_df["RECOMMENDED_ISSUES"] - filtered_df["FULLY_IMPLEMENTED"]
outstanding_total = filtered_df["OUTSTANDING_ISSUES"].sum()
st.metric("Total Outstanding Issues (Not Fully Implemented)", f"{outstanding_total}")

# Bar chart outstanding by department
outstanding_by_dept = filtered_df.groupby("DEPARTMENT")["OUTSTANDING_ISSUES"].sum().reset_index()
outstanding_by_dept = outstanding_by_dept.sort_values("OUTSTANDING_ISSUES", ascending=False)
if not outstanding_by_dept.empty:
    fig_outstanding = px.bar(
        outstanding_by_dept,
        x="DEPARTMENT",
        y="OUTSTANDING_ISSUES",
        title="Outstanding Issues by Department",
        labels={"OUTSTANDING_ISSUES": "Number of Outstanding Issues", "DEPARTMENT": ""},
        color="OUTSTANDING_ISSUES",
        color_continuous_scale="Oranges"
    )
    st.plotly_chart(fig_outstanding, use_container_width=True)
st.markdown("---")

# ------------------------------
# 6. Year-Based Analysis
st.header("📅 Year-on-Year Comparison")
# Aggregate by year
year_agg = filtered_df.groupby("YEAR_OF_ISSUE").agg({
    "RECOMMENDED_ISSUES": "sum",
    "FULLY_IMPLEMENTED": "sum",
    "PARTIALLY_IMPLEMENTED": "sum"
}).reset_index()
year_agg["IMPLEMENTATION_RATE"] = (
    (year_agg["FULLY_IMPLEMENTED"] + 0.5 * year_agg["PARTIALLY_IMPLEMENTED"]) / year_agg["RECOMMENDED_ISSUES"]
) * 100
year_agg["IMPLEMENTATION_RATE"] = year_agg["IMPLEMENTATION_RATE"].fillna(0).round(1)

# Bar chart: issues raised per year
fig_year_issues = px.bar(
    year_agg,
    x="YEAR_OF_ISSUE",
    y="RECOMMENDED_ISSUES",
    title="Total Audit Issues Raised per Year",
    labels={"RECOMMENDED_ISSUES": "Number of Issues", "YEAR_OF_ISSUE": "Year"},
    color="RECOMMENDED_ISSUES",
    color_continuous_scale="Blues"
)
st.plotly_chart(fig_year_issues, use_container_width=True)

# Implementation rate by year
fig_year_impl = px.bar(
    year_agg,
    x="YEAR_OF_ISSUE",
    y="IMPLEMENTATION_RATE",
    title="Implementation Rate by Year (%)",
    labels={"IMPLEMENTATION_RATE": "Implementation (%)", "YEAR_OF_ISSUE": "Year"},
    color="IMPLEMENTATION_RATE",
    color_continuous_scale="RdYlGn",
    range_color=[0, 100]
)
st.plotly_chart(fig_year_impl, use_container_width=True)
st.markdown("---")

# ------------------------------
# 7. High-Risk Focus
st.header("🔥 High-Risk Focus")
# Departments with high-risk issues > 0 and low implementation (< 50%)
high_risk_depts = filtered_df[filtered_df["HIGH"] > 0].copy()
high_risk_depts["IMPLEMENTATION_RATE"] = (
    (high_risk_depts["FULLY_IMPLEMENTED"] + 0.5 * high_risk_depts["PARTIALLY_IMPLEMENTED"]) / high_risk_depts["RECOMMENDED_ISSUES"]
) * 100
high_risk_depts["IMPLEMENTATION_RATE"] = high_risk_depts["IMPLEMENTATION_RATE"].round(1)
# Show high-risk departments with their implementation status
if not high_risk_depts.empty:
    st.subheader("Departments with High-Risk Issues")
    st.dataframe(
        high_risk_depts[["DEPARTMENT", "HIGH", "IMPLEMENTATION_RATE"]].style.format({"IMPLEMENTATION_RATE": "{:.1f}%"}),
        use_container_width=True
    )
    
    # Implementation of high-risk issues (since we don't have separate tracking per risk, we show overall)
    # We can create a visual: bar chart of high-risk count vs implementation rate
    fig_high_impl = px.scatter(
        high_risk_depts,
        x="HIGH",
        y="IMPLEMENTATION_RATE",
        text="DEPARTMENT",
        title="High-Risk Issues vs Implementation Rate",
        labels={"HIGH": "Number of High-Risk Issues", "IMPLEMENTATION_RATE": "Implementation Rate (%)"},
        color="IMPLEMENTATION_RATE",
        color_continuous_scale="RdYlGn",
        size="HIGH",
        range_y=[0, 100]
    )
    fig_high_impl.update_traces(textposition="top center")
    st.plotly_chart(fig_high_impl, use_container_width=True)
else:
    st.info("No departments with high-risk issues in the selected filters.")
st.markdown("---")

# ------------------------------
# 8. Visual Alerts / Flags
st.header("🚨 Visual Alerts & Flags")

# Alert 1: Departments with 0% implementation
zero_impl_depts = filtered_df[filtered_df["IMPLEMENTATION_PERCENT"] == 0]["DEPARTMENT"].tolist()
if zero_impl_depts:
    st.warning(f"⚠️ **0% Implementation Alert** - The following departments have no implemented issues: {', '.join(zero_impl_depts)}")
else:
    st.success("✅ No departments with 0% implementation.")

# Alert 2: Departments with high-risk issues (>5) and low implementation (<30%)
high_risk_low_impl = filtered_df[
    (filtered_df["HIGH"] > 5) & (filtered_df["IMPLEMENTATION_PERCENT"] < 30)
]
if not high_risk_low_impl.empty:
    st.error("🚨 **Critical Alert** - Departments with many high-risk issues and low implementation (<30%):")
    for _, row in high_risk_low_impl.iterrows():
        st.write(f"- **{row['DEPARTMENT']}**: {row['HIGH']} high-risk issues, {row['IMPLEMENTATION_PERCENT']:.1f}% implemented")
else:
    st.info("No critical high-risk low-implementation departments.")

# Alert 3: Older (2024) unresolved issues (not fully implemented)
old_issues = filtered_df[(filtered_df["YEAR_OF_ISSUE"] == 2024) & (filtered_df["FULLY_IMPLEMENTED"] < filtered_df["RECOMMENDED_ISSUES"])]
if not old_issues.empty:
    st.warning("📅 **Aging Issues** - 2024 issues still not fully resolved:")
    for _, row in old_issues.iterrows():
        outstanding = row["RECOMMENDED_ISSUES"] - row["FULLY_IMPLEMENTED"]
        st.write(f"- **{row['DEPARTMENT']}**: {outstanding} outstanding issues from 2024")
else:
    st.success("No outstanding 2024 issues.")

st.markdown("---")

# ------------------------------
# 9. Additional: Data download & raw data
st.subheader("📎 Data Export")
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("Download Filtered Data as CSV", csv, "audit_dashboard_data.csv", "text/csv")

st.subheader("📄 Raw Filtered Data")
st.dataframe(filtered_df, use_container_width=True)

# Footer
st.markdown("---")
st.caption("Dashboard built with Streamlit | Data as provided by Internal Audit Department")
