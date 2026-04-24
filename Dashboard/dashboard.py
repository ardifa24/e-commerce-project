import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from datetime import timedelta
st.set_page_config(page_title="E-Commerce Dashboard")

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "customer_unique_id": "nunique",
        "price": "sum"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "customer_unique_id": "customer_count",
        "price": "revenue"
    }, inplace=True)
    return daily_orders_df

def create_monthly_orders_df(df):
    monthly_orders_df = df.resample(rule='ME', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    })
    monthly_orders_df.index = monthly_orders_df.index.strftime('%Y-%m')
    monthly_orders_df = monthly_orders_df.reset_index()
    monthly_orders_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)
    return monthly_orders_df

def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("product_category_name_english").order_item_id.sum()\
        .sort_values(ascending=False).reset_index()
    return sum_order_items_df

def create_customer_state_df(df):
    customer_state_df = df.groupby("customer_state").customer_unique_id.nunique()\
        .sort_values(ascending=False).reset_index()
    customer_state_df.rename(columns={
        "customer_unique_id": "customer_count"
    }, inplace=True)
    return customer_state_df

def create_customer_city_df(df):
    customer_city_df = df.groupby("customer_city").customer_unique_id.nunique()\
        .sort_values(ascending=False).reset_index().head(10)
    customer_city_df.rename(columns={
        "customer_unique_id": "customer_count"
    }, inplace=True)
    return customer_city_df

def create_rfm_df(df):
    recent_date = df['order_purchase_timestamp'].max() + timedelta(days=1)
    rfm_df = df.groupby('customer_unique_id').agg({
        'order_purchase_timestamp': lambda x: (recent_date - x.max()).days,
        'order_id': 'nunique',
        'price': 'sum'
    }).reset_index()
    
    rfm_df.columns = ['customer_unique_id', 'recency', 'frequency', 'monetary']
    return rfm_df


all_df = pd.read_csv("Dashboard/all_data_ecommerce.csv")
all_df["order_purchase_timestamp"] = pd.to_datetime(all_df["order_purchase_timestamp"])


min_date = all_df["order_purchase_timestamp"].min().date()
max_date = all_df["order_purchase_timestamp"].max().date()

with st.sidebar:
    st.header("Filter Data")
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = all_df[(all_df["order_purchase_timestamp"].dt.date >= start_date) & 
                 (all_df["order_purchase_timestamp"].dt.date <= end_date)]

daily_orders_df = create_daily_orders_df(main_df)
monthly_orders_df = create_monthly_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
customer_state_df = create_customer_state_df(main_df)
customer_city_df = create_customer_city_df(main_df)
rfm_df = create_rfm_df(main_df)


st.header("E-Commerce Dashboard 🛒")

# Overview Metrics
st.subheader("Overview")
col1, col2, col3 = st.columns(3)
with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total Orders", value=f"{total_orders:,}")
with col2:
    total_customers = main_df.customer_unique_id.nunique()
    st.metric("Total Customers", value=f"{total_customers:,}")
with col3:
    total_revenue = daily_orders_df.revenue.sum()
    st.metric("Total Revenue", value=f"${total_revenue:,.2f}")

st.markdown("---")

# Tren Revenue (Monthly)
st.subheader("Monthly Revenue Performance")
fig, ax = plt.subplots(figsize=(16, 6))
sns.lineplot(
    x="order_purchase_timestamp", 
    y="revenue", 
    data=monthly_orders_df, 
    marker="o", 
    color="#1A73E8", 
    ax=ax, 
    linewidth=2
)
ax.set_ylabel("Revenue ($)")
ax.set_xlabel("Monthly")
plt.xticks(rotation=45)
st.pyplot(fig)

st.markdown("---")

# Customer Demographics (State & City)
st.subheader("Customer Demographics")
col1, col2 = st.columns(2)
colors_Demografi = ["#1A73E8"] + ["#95C0F8"] * 4

with col1:
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(
        y="customer_count", 
        x="customer_state",
        data=customer_state_df.head(),
        palette=colors_Demografi,
        ax=ax
    )
    ax.set_title("Top 5 States by Customer Count")
    ax.set_xlabel("State")
    ax.set_ylabel("Customer Count")
    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(
        x="customer_city", 
        y="customer_count",
        data=customer_city_df.head(),
        palette=colors_Demografi,
        ax=ax
    )
    ax.set_title("Top 5 Cities by Customer Count")
    ax.set_xlabel("City")
    ax.set_ylabel("Customer Count")
    st.pyplot(fig)

st.markdown("---")

# Best & Worst Performing Products
st.subheader("Best & Worst Performing Products")
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 8))

colors_prod = ["#1A73E8"] + ["#95C0F8"] * 4

sns.barplot(
    x="order_item_id", 
    y="product_category_name_english", 
    data=sum_order_items_df.head(5), 
    palette=colors_prod, 
    ax=ax[0],
    hue="product_category_name_english",
    legend=False
)
ax[0].set_ylabel(None)
ax[0].set_xlabel("Units Sold", fontsize=15)
ax[0].set_title("Top 5 Best Performing Products", loc="center", fontsize=18)
ax[0].tick_params(axis='y', labelsize=15)
ax[0].tick_params(axis='x', labelsize=12)

sns.barplot(
    x="order_item_id", 
    y="product_category_name_english", 
    data=sum_order_items_df.sort_values(by="order_item_id", ascending=True).head(5), 
    palette=["#e5261f"] + ["#95C0F8"]*4, 
    ax=ax[1],
    hue="product_category_name_english",
    legend=False
)
ax[1].set_ylabel(None)
ax[1].set_xlabel("Units Sold", fontsize=15)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Bottom 5 Performing Products", loc="center", fontsize=18)
ax[1].tick_params(axis='y', labelsize=15)
ax[1].tick_params(axis='x', labelsize=12)

st.pyplot(fig)

st.markdown("---")

# 5. RFM Analysis 
st.subheader("Customer Segmentation (RFM Analysis)")

# Ambil 5 customer teratas berdasarkan Recency, Frequency, Monetary
top_recency = rfm_df.sort_values(by="recency", ascending=True).head(5).copy()
top_frequency = rfm_df.sort_values(by="frequency", ascending=False).head(5).copy()
top_monetary = rfm_df.sort_values(by="monetary", ascending=False).head(5).copy()

# Buat label untuk visualisasi supaya lebih deskriptif
top_recency['label'] = [f'Top Recency {i}' for i in range(1, 6)]
top_frequency['label'] = [f'Top Frequency {i}' for i in range(1, 6)]
top_monetary['label'] = [f'Top Monetary {i}' for i in range(1, 6)]

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(30, 10))
colors_rfm = ["#1A73E8"] + ["#95C0F8"] * 4

# Plot untuk Recency
sns.barplot(y="recency", x="label", data=top_recency, palette=colors_rfm, ax=ax[0], hue="label", legend=False)
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("By Recency (days)", loc="center", fontsize=22)
ax[0].tick_params(axis='x', labelsize=15, rotation=45)
ax[0].tick_params(axis='y', labelsize=15)

# Plot untuk Frequency
sns.barplot(y="frequency", x="label", data=top_frequency, palette=colors_rfm, ax=ax[1], hue="label", legend=False)
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].set_title("By Frequency", loc="center", fontsize=22)
ax[1].tick_params(axis='x', labelsize=15, rotation=45)
ax[1].tick_params(axis='y', labelsize=15)

# Plot untuk Monetary
sns.barplot(y="monetary", x="label", data=top_monetary, palette=colors_rfm, ax=ax[2], hue="label", legend=False)
ax[2].set_ylabel(None)
ax[2].set_xlabel(None)
ax[2].set_title("By Monetary", loc="center", fontsize=22)
ax[2].tick_params(axis='x', labelsize=15, rotation=45)
ax[2].tick_params(axis='y', labelsize=15)

plt.suptitle("Best Customers Based on RFM Parameters", fontsize=28, fontweight='bold', y=1.0)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])

st.pyplot(fig)

st.markdown("---")

st.caption("2026 © E-Commerce Dashboard by ardifa")