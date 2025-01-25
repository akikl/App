import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='Sales Dashboard', layout='wide')

st.title("Razorpay Agent App Dashboard")
st.markdown("##")

# File upload
st.sidebar.header("Upload Files")
device_order_file = st.sidebar.file_uploader("Upload Device Order Summary", type=["csv"])
fos_file = st.sidebar.file_uploader("Upload Razorpay Agent App", type=["xlsx"])

if device_order_file and fos_file:
    device_order_data = pd.read_csv(device_order_file)
    fos_data = pd.read_excel(fos_file, sheet_name='FOS Master Details')

    # Sidebar filters
    st.sidebar.header("Filters")
    bh = st.sidebar.multiselect("BH:", options=device_order_data["BH_Name"].unique(), default=device_order_data["BH_Name"].unique())
    zone = st.sidebar.multiselect("Zone:", options=device_order_data["Zone"].unique(), default=device_order_data["Zone"].unique())
    device_model = st.sidebar.multiselect("Device model:", options=device_order_data["device_model"].unique(), default=device_order_data["device_model"].unique())
    reporting_manager = st.sidebar.multiselect("Reporting Manager:", options=device_order_data["Reporting Manager"].unique(), default=device_order_data["Reporting Manager"].unique())

    device_order_data_selection = device_order_data.query("BH_Name == @bh & Zone == @zone & device_model == @device_model & Reporting Manager == @reporting_manager")

    # KPI calculations
    total_device_orders = int(device_order_data_selection['device_count'].sum())
    unique_merchants = len(device_order_data_selection['merchant_id'].unique())
    device_order_value = round(device_order_data_selection['order_amount'].sum(), 2)
    tids_received = len(device_order_data_selection[~device_order_data_selection['tid_received_date'].isna()])

    left_column, middle_column_1, middle_column_2, right_column = st.columns(4)
    with left_column:
        st.subheader('Unique Merchants')
        st.subheader(unique_merchants)
    with middle_column_1:
        st.subheader('Total Device Orders 📦')
        st.subheader(total_device_orders)
    with middle_column_2:
        st.subheader('TIDs received')
        st.subheader(tids_received)
    with right_column:
        st.subheader('Total Order Amount')
        st.subheader(f'{device_order_value:,}')

    st.markdown("---")
    
    kyc_qualified = len(device_order_data_selection[~device_order_data_selection['pos_kyc_qualified_date'].isna()])
    installed_cases = len(device_order_data_selection[~device_order_data_selection['installation_date'].isna()])
    under_review = len(device_order_data_selection[~device_order_data_selection['pos_ur_date'].isna()])
    needs_clarification = len(device_order_data_selection[~device_order_data_selection['pos_nc_date'].isna()])
    
    left_column, middle_column_1, middle_column_2, right_column = st.columns(4)
    with left_column:
        st.subheader('KYC Qualified Cases')
        st.subheader(kyc_qualified)
    with middle_column_1:
        st.subheader('Under Review Cases')
        st.subheader(under_review)
    with middle_column_2:
        st.subheader('Needs Clarification Cases')
        st.subheader(needs_clarification)
    with right_column:
        st.subheader('Installed')
        st.subheader(f'{installed_cases}')

    st.markdown("---")
    
    # Bar Charts
    left_column, right_column = st.columns(2)
    device_model_counts = device_order_data_selection['device_model'].value_counts().reset_index()
    device_model_counts.columns = ['device_model', 'orders']

    device_model_installations = device_order_data_selection[~device_order_data_selection['installation_date'].isna()]['device_model'].value_counts().reset_index()
    device_model_installations.columns = ['device_model', 'installed']

    with left_column:
        fig_orders = px.bar(device_model_counts, x='device_model', y='orders', title='Device Model wise Orders', template="plotly_white")
        st.plotly_chart(fig_orders, use_container_width=True)

    with right_column:
        fig_installations = px.bar(device_model_installations, x='device_model', y='installed', title='Device Model wise Installation', template="plotly_white")
        st.plotly_chart(fig_installations, use_container_width=True)

    # Adoption Summary
    grouped_df = device_order_data.groupby(['BH_Name', 'Reporting Manager']).agg(FOS_with_lead=pd.NamedAgg(column='Name of the FOS', aggfunc='nunique'), Login_count=pd.NamedAgg(column='signup_date', aggfunc='count')).reset_index()
    grp_data_1 = fos_data.groupby(['BH_Name', 'Reporting Manager']).agg(Total_FOS=pd.NamedAgg(column='Name of the FOS', aggfunc='nunique'))
    final_data = pd.merge(grp_data_1, grouped_df, on=['BH_Name', 'Reporting Manager'], how='left').fillna(0)
    final_data['%FOS With Lead Entry'] = round((final_data['FOS_with_lead'] / final_data['Login_count']) * 100, 0).fillna(0)
    
    subtotal = final_data.groupby('BH_Name')[['Total_FOS', 'FOS_with_lead', 'Login_count']].sum().reset_index()
    subtotal['Reporting Manager'] = 'Subtotal'
    subtotal['%FOS With Lead Entry'] = round((subtotal['FOS_with_lead'] / subtotal['Login_count']) * 100, 0).fillna(0)
    final_data_with_subtotals = pd.concat([final_data, subtotal], ignore_index=True)
    final_data_with_subtotals.sort_values(by=['BH_Name', 'Reporting Manager'], inplace=True)
    
    st.subheader('Adoption Summary')
    st.dataframe(final_data_with_subtotals)
else:
    st.warning("Please upload both files to generate the dashboard.")
