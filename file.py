import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import io
from PIL import Image
import os

# ------------------------------
# Page config
st.set_page_config(page_title="Mater Hospital - Audit Follow-Up Dashboard", layout="wide")

# ------------------------------
# Load and display logo
logo_path = "mater.png"  # Assuming the image is in the same directory
if os.path.exists(logo_path):
    logo = Image.open(logo_path)
    # Display logo in sidebar
    st.sidebar.image(logo, use_container_width=True)
    # Also display at top of main area (optional)
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image(logo, width=100)
    with col2:
        st.title("🏥 Mater Misericordiae Hospital")
        st.subheader("Internal Audit Follow-Up Tracker")
else:
    st.title("🏥 Mater Misericordiae Hospital")
    st.subheader("Internal Audit Follow-Up Tracker")
    st.sidebar.warning("Logo image 'mater.png' not found. Please place it in the app directory.")

st.markdown("Monitor implementation status of audit recommendations across departments.")

# ------------------------------
# File uploader
uploaded_file = st.sidebar.file_uploader("Upload Audit Tracker Excel File", type=["xlsx", "xls"])

if uploaded_file is not None:
    # Load all sheets
    excel_file = pd.ExcelFile(uploaded_file)
    sheet_names = excel_file.sheet_names
    
    # Load SUMMARY sheet
    if "SUMMARY" in sheet_names:
        df_summary = pd.read_excel(uploaded_file, sheet_name="SUMMARY", header=None)
        # Clean and parse the summary table (assuming structure from the provided data)
        # Let's locate the actual data rows
        summary_start = df_summary[df_summary[0].astype(str).str.contains("DEPARTMENT", na=False, case=False)].index
        if len(summary_start) > 0:
            summary_data = df_summary.iloc[summary_start[0]:].copy()
            summary_data.columns = summary_data.iloc[0]
            summary_data = summary_data[1:].reset_index(drop=True)
            # Rename columns appropriately
            summary_data.columns = ["DEPARTMENT", "RECOMMENDED_ISSUES", "YEAR_OF_ISSUE", "HIGH", "MEDIUM", 
                                    "FULLY_IMPLEMENTED", "PARTIALLY_IMPLEMENTED", "NOT_IMPLEMENTED", "NOT_DUE", "PERCENTAGE_IMPLEMENTATION"]
            # Convert numeric columns
            for col in ["RECOMMENDED_ISSUES", "HIGH", "MEDIUM", "FULLY_IMPLEMENTED", "PARTIALLY_IMPLEMENTED", "NOT_IMPLEMENTED", "NOT_DUE"]:
                summary_data[col] = pd.to_numeric(summary_data[col], errors="coerce")
            # Remove rows where DEPARTMENT is NaN or total row
            summary_data = summary_data.dropna(subset=["DEPARTMENT"])
            summary_data = summary_data[~summary_data["DEPARTMENT"].astype(str).str.contains("Total", na=False)]
        else:
            st.error("SUMMARY sheet format not recognized. Please ensure it has a row starting with 'DEPARTMENT'.")
            st.stop()
    else:
        st.error("SUMMARY sheet not found in the uploaded file.")
        st.stop()
    
    # Load detailed sheets for each department (if needed for drill-down)
    # We'll create a dictionary of department data frames
    dept_sheets = {
        "LABORATORY": "LABORATORY",
        "REVENUE REVERSALS": "REVENUE REVERSALS",
        "REVENUE CYCLE MANAGEMENT": "RCM",
        "SUPPLY CHAIN MANAGEMENT": "SCM",
        "ACCOUNTS PAYABLE": "ACCOUNTS PAYABLE",
        "MATER HEARTRUN": "MATER HEARTRUN",
        "FACILITIES MANAGEMENT": "FACILITIES MANAGEMENT",
        "PHARMACY": "PHARMACY",
        "CAFETERIA": "CAFETERIA",
        "SCHOOL OF NURSING": "SON",
        "PAYROLL": "PAYROLL",
        "RECRUITMENT & ONBOARDING": "RECRUITMENT"
    }
    
    # Load each detailed sheet if exists
    dept_details = {}
    for dept, sheet in dept_sheets.items():
        if sheet in sheet_names:
            try:
                df = pd.read_excel(uploaded_file, sheet_name=sheet)
                # Try to identify columns: finding description, responsible person, due date, risk rating, follow up status
                # The structure varies per sheet. We'll extract based on common patterns.
                # For simplicity, we'll assume the sheet has columns like: 'B' (finding), 'C' (responsible), 'D' (due date), 'E' (risk rating), and maybe 'G' (follow up)
                # We'll rename to standard names
                if df.shape[1] >= 5:
                    # Use first few rows as header detection
                    possible_headers = df.iloc[0].astype(str).str.lower()
                    # Look for common terms
                    cols = {}
                    for i, val in enumerate(df.columns):
                        col_str = str(val).lower()
                        if "finding" in col_str or "observation" in col_str or "issue" in col_str:
                            cols["Finding"] = i
                        elif "responsible" in col_str or "person" in col_str:
                            cols["Responsible"] = i
                        elif "due" in col_str or "date" in col_str:
                            cols["Due_Date"] = i
                        elif "risk" in col_str or "rating" in col_str:
                            cols["Risk_Rating"] = i
                        elif "follow" in col_str or "implementation" in col_str or "status" in col_str:
                            cols["Follow_Up_Status"] = i
                    if cols:
                        # Extract data starting from row 1 (skip header row)
                        detail_df = df.iloc[1:].copy()
                        detail_df = detail_df.iloc[:, list(cols.values())]
                        detail_df.columns = list(cols.keys())
                        # Clean
                        detail_df = detail_df.dropna(how="all")
                        dept_details[dept] = detail_df
                    else:
                        # Fallback: just store raw data
                        dept_details[dept] = df
                else:
                    dept_details[dept] = df
            except Exception as e:
                st.warning(f"Could not load sheet {sheet}: {e}")
    
    # ------------------------------
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Department filter
    departments = summary_data["DEPARTMENT"].unique()
    selected_depts = st.sidebar.multiselect("Select Departments", departments, default=departments)
    
    # Year filter
    years = summary_data["YEAR_OF_ISSUE"].dropna().unique()
    selected_years = st.sidebar.multiselect("Year of Issue", sorted(years), default=sorted(years))
    
    # Implementation status filter
    status_options = ["Fully Implemented", "Partially Implemented", "Not Implemented", "Not Due"]
    selected_status = st.sidebar.multiselect("Implementation Status", status_options, default=status_options)
    
    # Filter summary data
    filtered_summary = summary_data[
        (summary_data["DEPARTMENT"].isin(selected_depts)) &
        (summary_data["YEAR_OF_ISSUE"].isin(selected_years))
    ]
    
    # Also filter detailed sheets by department selection (but we'll show details in expanders)
    
    # ------------------------------
    # Key Metrics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_issues = filtered_summary["RECOMMENDED_ISSUES"].sum()
        st.metric("Total Audit Issues", f"{int(total_issues):,}")
    with col2:
        total_high_risk = filtered_summary["HIGH"].sum()
        st.metric("High Risk Issues", f"{int(total_high_risk)}", delta=None, delta_color="inverse")
    with col3:
        # Overall implementation percentage (weighted by total issues per dept)
        total_impl = (filtered_summary["FULLY_IMPLEMENTED"].sum() + 
                      filtered_summary["PARTIALLY_IMPLEMENTED"].sum() * 0.5)  # partial counts as half
        overall_pct = (total_impl / filtered_summary["RECOMMENDED_ISSUES"].sum()) * 100 if filtered_summary["RECOMMENDED_ISSUES"].sum() > 0 else 0
        st.metric("Overall Implementation", f"{overall_pct:.1f}%")
    with col4:
        depts_with_issues = filtered_summary["DEPARTMENT"].nunique()
        st.metric("Departments", depts_with_issues)
    st.markdown("---")
    
    # ------------------------------
    # Main Dashboard Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Department Summary", "📋 Detailed Findings", "📈 Risk & Progress Analysis", "📅 Overdue Items"])
    
    # ==============================
    # TAB 1: Department Summary
    # ==============================
    with tab1:
        st.subheader("Implementation Status by Department")
        
        # Prepare data for bar chart
        status_cols = ["FULLY_IMPLEMENTED", "PARTIALLY_IMPLEMENTED", "NOT_IMPLEMENTED", "NOT_DUE"]
        status_data = filtered_summary.melt(id_vars=["DEPARTMENT"], value_vars=status_cols, 
                                            var_name="Status", value_name="Count")
        status_data = status_data[status_data["Count"] > 0]
        
        fig1 = px.bar(status_data, x="DEPARTMENT", y="Count", color="Status", 
                      title="Number of Issues by Implementation Status",
                      barmode="stack", color_discrete_map={
                          "FULLY_IMPLEMENTED": "green",
                          "PARTIALLY_IMPLEMENTED": "orange",
                          "NOT_IMPLEMENTED": "red",
                          "NOT_DUE": "gray"
                      })
        st.plotly_chart(fig1, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            # Risk distribution by department
            risk_data = filtered_summary.melt(id_vars=["DEPARTMENT"], value_vars=["HIGH", "MEDIUM"],
                                              var_name="Risk", value_name="Count")
            risk_data = risk_data[risk_data["Count"] > 0]
            fig2 = px.bar(risk_data, x="DEPARTMENT", y="Count", color="Risk",
                          title="Risk Rating Distribution", barmode="group",
                          color_discrete_map={"HIGH": "darkred", "MEDIUM": "gold"})
            st.plotly_chart(fig2, use_container_width=True)
        
        with col2:
            # Implementation percentage per department
            impl_pct = filtered_summary.copy()
            impl_pct["Implementation_%"] = (impl_pct["FULLY_IMPLEMENTED"] + 0.5 * impl_pct["PARTIALLY_IMPLEMENTED"]) / impl_pct["RECOMMENDED_ISSUES"] * 100
            impl_pct = impl_pct.sort_values("Implementation_%", ascending=True)
            fig3 = px.bar(impl_pct, x="Implementation_%", y="DEPARTMENT", orientation="h",
                          title="Implementation Progress (%)", color="Implementation_%",
                          color_continuous_scale="RdYlGn", range_color=[0,100])
            st.plotly_chart(fig3, use_container_width=True)
        
        # Show summary table
        st.subheader("Department Summary Table")
        display_cols = ["DEPARTMENT", "RECOMMENDED_ISSUES", "YEAR_OF_ISSUE", "HIGH", "MEDIUM", 
                        "FULLY_IMPLEMENTED", "PARTIALLY_IMPLEMENTED", "NOT_IMPLEMENTED", "NOT_DUE"]
        st.dataframe(filtered_summary[display_cols], use_container_width=True)
    
    # ==============================
    # TAB 2: Detailed Findings
    # ==============================
    with tab2:
        st.subheader("Detailed Audit Findings by Department")
        for dept in selected_depts:
            if dept in dept_details and not dept_details[dept].empty:
                with st.expander(f"📁 {dept} - Detailed Findings"):
                    df_detail = dept_details[dept]
                    # Show columns if they exist
                    st.dataframe(df_detail, use_container_width=True)
                    # Option to download
                    csv = df_detail.to_csv(index=False).encode('utf-8')
                    st.download_button(f"Download {dept} details", csv, f"{dept}_details.csv", "text/csv")
            else:
                # Try to match by partial name
                matched = False
                for key, df_sheet in dept_details.items():
                    if dept.lower() in key.lower() or key.lower() in dept.lower():
                        with st.expander(f"📁 {dept} - Detailed Findings (from sheet {key})"):
                            st.dataframe(df_sheet, use_container_width=True)
                            csv = df_sheet.to_csv(index=False).encode('utf-8')
                            st.download_button(f"Download {dept} details", csv, f"{dept}_details.csv", "text/csv")
                        matched = True
                        break
                if not matched:
                    st.info(f"No detailed sheet found for {dept}. Only summary data available.")
    
    # ==============================
    # TAB 3: Risk & Progress Analysis
    # ==============================
    with tab3:
        st.subheader("Risk and Progress Analytics")
        
        col1, col2 = st.columns(2)
        with col1:
            # High risk vs implementation scatter
            high_risk_impl = filtered_summary[["DEPARTMENT", "HIGH", "FULLY_IMPLEMENTED"]].copy()
            high_risk_impl["Implementation_Rate"] = (high_risk_impl["FULLY_IMPLEMENTED"] / filtered_summary["RECOMMENDED_ISSUES"]) * 100
            fig4 = px.scatter(high_risk_impl, x="HIGH", y="Implementation_Rate", text="DEPARTMENT",
                              title="High Risk Issues vs Implementation Rate",
                              labels={"HIGH": "Number of High Risk Issues", "Implementation_Rate": "Implementation Rate (%)"},
                              size="HIGH", color="Implementation_Rate", color_continuous_scale="RdYlGn")
            fig4.update_traces(textposition="top center")
            st.plotly_chart(fig4, use_container_width=True)
        
        with col2:
            # Pie chart of overall risk distribution
            total_high = filtered_summary["HIGH"].sum()
            total_medium = filtered_summary["MEDIUM"].sum()
            fig5 = px.pie(values=[total_high, total_medium], names=["High Risk", "Medium Risk"],
                          title="Overall Risk Profile", color_discrete_map={"High Risk": "darkred", "Medium Risk": "orange"})
            st.plotly_chart(fig5, use_container_width=True)
        
        # Heatmap: departments vs implementation status
        heat_data = filtered_summary.set_index("DEPARTMENT")[status_cols]
        fig6 = px.imshow(heat_data, text_auto=True, aspect="auto", 
                         title="Implementation Status Heatmap (Number of Issues)",
                         labels=dict(x="Status", y="Department", color="Count"),
                         color_continuous_scale="Blues")
        st.plotly_chart(fig6, use_container_width=True)
        
        # Gauge chart for overall progress
        overall_impl = overall_pct
        fig7 = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = overall_impl,
            title = {"text": "Overall Implementation Progress (%)"},
            delta = {'reference': 50},
            gauge = {'axis': {'range': [None, 100]},
                     'bar': {'color': "darkgreen"},
                     'steps': [
                         {'range': [0, 30], 'color': "red"},
                         {'range': [30, 70], 'color': "orange"},
                         {'range': [70, 100], 'color': "lightgreen"}],
                     'threshold': {'line': {'color': "black", 'width': 2}, 'thickness': 0.75, 'value': 90}}))
        fig7.update_layout(height=300)
        st.plotly_chart(fig7, use_container_width=True)
    
    # ==============================
    # TAB 4: Overdue Items
    # ==============================
    with tab4:
        st.subheader("Overdue Recommendations")
        st.markdown("Items with due dates that have passed and are not fully implemented.")
        
        # Collect overdue from all detailed sheets
        overdue_list = []
        today = datetime.now().date()
        
        for dept, df_detail in dept_details.items():
            # Look for date column
            date_col = None
            status_col = None
            finding_col = None
            for col in df_detail.columns:
                col_lower = str(col).lower()
                if "due" in col_lower or "date" in col_lower:
                    date_col = col
                elif "status" in col_lower or "follow" in col_lower or "implementation" in col_lower:
                    status_col = col
                elif "finding" in col_lower or "observation" in col_lower or "issue" in col_lower:
                    finding_col = col
            
            if date_col:
                # Convert to datetime
                try:
                    df_detail["parsed_date"] = pd.to_datetime(df_detail[date_col], errors='coerce').dt.date
                except:
                    continue
                # Filter overdue: date < today and status not "Fully Implemented"
                if status_col:
                    not_fully = ~df_detail[status_col].astype(str).str.lower().str.contains("fully", na=False)
                else:
                    not_fully = True
                overdue = df_detail[(df_detail["parsed_date"] < today) & not_fully]
                if not overdue.empty:
                    for idx, row in overdue.iterrows():
                        overdue_list.append({
                            "Department": dept,
                            "Finding": row[finding_col] if finding_col else "N/A",
                            "Due Date": row[date_col],
                            "Status": row[status_col] if status_col else "Unknown",
                            "Responsible": row.iloc[1] if len(row) > 1 else "N/A"
                        })
        
        if overdue_list:
            overdue_df = pd.DataFrame(overdue_list)
            st.dataframe(overdue_df, use_container_width=True)
            csv_overdue = overdue_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Overdue List", csv_overdue, "overdue_items.csv", "text/csv")
        else:
            st.success("No overdue items found! Great progress.")
        
        # Also show upcoming deadlines (next 30 days)
        st.subheader("Upcoming Deadlines (Next 30 Days)")
        upcoming_list = []
        for dept, df_detail in dept_details.items():
            date_col = None
            status_col = None
            finding_col = None
            for col in df_detail.columns:
                col_lower = str(col).lower()
                if "due" in col_lower or "date" in col_lower:
                    date_col = col
                elif "status" in col_lower or "follow" in col_lower:
                    status_col = col
                elif "finding" in col_lower or "observation" in col_lower:
                    finding_col = col
            if date_col:
                try:
                    df_detail["parsed_date"] = pd.to_datetime(df_detail[date_col], errors='coerce').dt.date
                except:
                    continue
                if status_col:
                    not_fully = ~df_detail[status_col].astype(str).str.lower().str.contains("fully", na=False)
                else:
                    not_fully = True
                upcoming = df_detail[(df_detail["parsed_date"] >= today) & (df_detail["parsed_date"] <= today + pd.Timedelta(days=30)) & not_fully]
                if not upcoming.empty:
                    for idx, row in upcoming.iterrows():
                        upcoming_list.append({
                            "Department": dept,
                            "Finding": row[finding_col] if finding_col else "N/A",
                            "Due Date": row[date_col],
                            "Status": row[status_col] if status_col else "Unknown"
                        })
        if upcoming_list:
            upcoming_df = pd.DataFrame(upcoming_list)
            st.dataframe(upcoming_df, use_container_width=True)
        else:
            st.info("No upcoming deadlines in the next 30 days.")
    
    # ------------------------------
    # Download filtered summary data
    st.sidebar.markdown("---")
    csv_summary = filtered_summary.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("Download Filtered Summary (CSV)", csv_summary, "audit_summary.csv", "text/csv")
    
else:
    st.info("👈 Please upload the Audit Follow-Up Excel file to get started.")
    st.markdown("""
    ### Expected File Structure:
    - A sheet named **SUMMARY** with columns: DEPARTMENT, RECOMMENDED_ISSUES, YEAR_OF_ISSUE, HIGH, MEDIUM, FULLY_IMPLEMENTED, PARTIALLY_IMPLEMENTED, NOT_IMPLEMENTED, NOT_DUE.
    - Optional detailed sheets (e.g., LABORATORY, PHARMACY, etc.) with finding details, due dates, responsible persons, and follow-up status.
    
    *The dashboard will automatically parse and visualize the data.*
    """)

st.markdown("---")
st.caption("📌 Mater Misericordiae Hospital - Internal Audit Follow-Up System | Data is for monitoring and decision support.")
