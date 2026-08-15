"""SkinNiX-II Intelligence — Creator Performance Analytics dashboard (dark, login-protected)."""
import os
import urllib.request

import pandas as pd
import streamlit as st

st.set_page_config(page_title="SkinNiX-II Intelligence", page_icon="📊", layout="wide")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Live data: published Google Sheet (auto-fresh). Local CSV fallback for offline dev.
PUB = ("https://docs.google.com/spreadsheets/d/e/"
       "2PACX-1vTDRFXDIkN-ZFJ5SGJWss2R9-jdQyw9j2ITRvcpPOsYp41v_gn42BBONsuzYkducP4-6QWbRDL4GhNo")
DATA_SOURCES = {
    "affiliate_leaderboard.csv": f"{PUB}/pub?gid=1693201907&single=true&output=csv",
    "top_5_products.csv": f"{PUB}/pub?gid=64062940&single=true&output=csv",
    "daily_performance.csv": f"{PUB}/pub?gid=1656789718&single=true&output=csv",
    "weekly_performance.csv": f"{PUB}/pub?gid=1919692199&single=true&output=csv",
    "monthly_performance.csv": f"{PUB}/pub?gid=1288091284&single=true&output=csv",
    "boost_shortlist.csv": f"{PUB}/pub?gid=1124296553&single=true&output=csv",
}

# ---------- dark styling ----------
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .kpi-card {
        background: #151B2B; border: 1px solid #232C44; border-radius: 12px;
        padding: 18px 22px; margin-bottom: 8px;
    }
    .kpi-label { color: #8B93A7; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em; }
    .kpi-value { color: #F1F5F9; font-size: 1.7rem; font-weight: 700; margin-top: 4px; }
    .kpi-sub { color: #64748B; font-size: 0.8rem; }
    .rec-card {
        background: #151B2B; border-left: 4px solid #F43F5E; border-radius: 10px;
        padding: 14px 18px; margin: 8px 0;
    }
    .rec-title { color: #F8FAFC; font-weight: 600; font-size: 1rem; }
    .rec-why { color: #94A3B8; font-size: 0.88rem; margin-top: 4px; }
    .rec-tag { display:inline-block; background:#1E293B; color:#CBD5E1; border-radius:6px;
               padding:2px 10px; font-size:0.75rem; margin-right:6px;}
    h1, h2, h3 { color: #F1F5F9 !important; }
    [data-testid="stMetric"] { background:#151B2B; border:1px solid #232C44; border-radius:12px; padding:14px; }
</style>
""", unsafe_allow_html=True)

# ---------- login ----------
def check_login():
    if st.session_state.get("authed"):
        return True
    st.markdown("## 🔐 SkinNiX-II Intelligence")
    st.caption("Sign in to view the creator performance dashboard.")
    with st.form("login_form"):
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        ok = st.form_submit_button("Sign in", type="primary")
    if ok:
        users = st.secrets.get("users", {})
        if user in users and users[user] == pwd:
            st.session_state.authed = True
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Incorrect username or password.")
    return False


def load(name):
    url = DATA_SOURCES.get(name)
    if url:
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                return pd.read_csv(r)
        except Exception:
            pass  # fall back to local CSV
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path)


# ---------- recommendations (SkinNiX-II Intelligence rules) ----------
def build_recommendations(lb, monthly, boost):
    recs = []
    if not lb.empty:
        top = lb.iloc[0]
        if float(top.get("live_share_pct", 0) or 0) >= 70:
            recs.append(("LIVE OPPORTUNITY", f"Ask {top['affiliate']} to run more live sessions this week",
                         f"{top['live_share_pct']}% of their RM {top['gmv_rm']:,.0f} sales come from LIVE — more live time is the highest-leverage ask."))
        video_driven = lb[lb["channel"] == "VIDEO_DRIVEN"].head(1)
        if not video_driven.empty:
            v = video_driven.iloc[0]
            recs.append(("VIDEO LEVERAGE", f"Send new products to {v['affiliate']} for video content",
                         f"They're VIDEO-driven (RM {v['video_gmv_rm']:,.0f} video sales) — they convert best through videos, not lives."))
        if len(lb) >= 5:
            fifth = lb.iloc[4]
            recs.append(("GROWTH", f"Nurture rising affiliate {fifth['affiliate']}",
                         f"Solid sales (RM {fifth['gmv_rm']:,.0f}) without top billing — a nudge (better commission or product access) could push them up."))
    if not monthly.empty and len(monthly) >= 2:
        cur = monthly.iloc[0]; prev = monthly.iloc[1]
        if float(prev.get("gmv_rm", 0) or 0) > 0:
            delta = (float(cur["gmv_rm"]) - float(prev["gmv_rm"])) / float(prev["gmv_rm"]) * 100
            if delta <= -15:
                recs.append(("TREND WARNING", f"Overall sales down {abs(delta):.0f}% vs last month",
                             f"{prev['period']}: RM {prev['gmv_rm']:,.0f} → {cur['period']}: RM {cur['gmv_rm']:,.0f}. Check stock, pricing and top affiliate availability."))
            elif delta >= 15:
                recs.append(("TREND BOOST", f"Sales up {delta:.0f}% vs last month — keep momentum",
                             f"{prev['period']}: RM {prev['gmv_rm']:,.0f} → {cur['period']}: RM {cur['gmv_rm']:,.0f}. Consider increasing affiliate incentives now."))
    if not boost.empty:
        b = boost.iloc[0]
        recs.append(("BOOST REVIEW", f"Review video {b['video_id']} for ad budget",
                     f"Top candidate: RM {b['sales_rm']:,.0f} sales / {b['orders']} orders by {b['affiliate']}. Staff decision required — never auto-spend."))
    return recs


# ---------- main ----------
if not check_login():
    st.stop()

st.markdown("## 📊 SkinNiX-II Intelligence")
st.caption(f"Signed in as **{st.session_state.get('user')}** · Creator Performance Analytics · data refreshes daily")

lb = load("affiliate_leaderboard.csv")
prods = load("top_5_products.csv")
daily = load("daily_performance.csv")
weekly = load("weekly_performance.csv")
monthly = load("monthly_performance.csv")
boost = load("boost_shortlist.csv")

if lb.empty:
    st.warning("No data yet — run `report.py` first to generate the dashboard data.")
    st.stop()

# KPI row
total_gmv = lb["gmv_rm"].sum()
total_orders = int(lb["orders"].sum())
top_aff = lb.iloc[0]
live_share = total_gmv and (lb["live_gmv_rm"].sum() / total_gmv * 100)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Sales (60d)", f"RM {total_gmv:,.0f}")
with c2:
    st.metric("Orders (60d)", f"{total_orders:,}")
with c3:
    st.metric("Top Affiliate", f"{top_aff['affiliate']} · RM {top_aff['gmv_rm']:,.0f}")
with c4:
    st.metric("LIVE share", f"{live_share:.0f}%")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🏆 Leaderboard", "📦 Products", "📈 Trends", "🚀 Boost List", "💡 Recommendations"])

with tab1:
    st.subheader("Affiliate Leaderboard — LIVE vs VIDEO")
    top15 = lb.head(15).copy()
    chart = top15.melt(id_vars=["affiliate"], value_vars=["live_gmv_rm", "video_gmv_rm"],
                       var_name="channel", value_name="gmv_rm")
    st.bar_chart(chart, x="affiliate", y="gmv_rm", color="channel", height=420)
    st.dataframe(lb.head(50), use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Top 5 Products per Affiliate")
    cols = ["affiliate", "product_name", "gmv_rm", "orders", "live_gmv_rm", "video_gmv_rm"]
    view = prods[cols] if not prods.empty and "product_name" in prods.columns else prods
    st.dataframe(view.head(100), use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Daily Sales Trend")
    if not daily.empty:
        d = daily.copy()
        d["period"] = pd.to_datetime(d["period"])
        st.line_chart(d.set_index("period")[["live_gmv_rm", "video_gmv_rm"]], height=380)
    c_a, c_b = st.columns(2)
    with c_a:
        st.subheader("Weekly")
        st.dataframe(weekly, use_container_width=True, hide_index=True)
    with c_b:
        st.subheader("Monthly")
        st.dataframe(monthly, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Potential Ads Boost — staff review required")
    if not boost.empty:
        b = boost.copy()
        b["staff_decision"] = b["staff_decision"].fillna("")
        edited = st.data_editor(b, use_container_width=True, hide_index=True,
                                column_config={"staff_decision": st.column_config.SelectboxColumn(
                                    "Staff decision", options=["", "boost", "skip", "reviewing"])})
    else:
        st.info("No boost candidates in this window.")

with tab5:
    st.subheader("💡 SkinNiX-II Intelligence — Recommendations")
    st.caption("Suggested actions based on your data. Staff review and decide — nothing runs automatically.")
    for tag, title, why in build_recommendations(lb, monthly, boost):
        st.markdown(
            f'<div class="rec-card"><span class="rec-tag">{tag}</span>'
            f'<div class="rec-title">{title}</div><div class="rec-why">{why}</div></div>',
            unsafe_allow_html=True)
    if st.button("Sign out"):
        st.session_state.authed = False
        st.rerun()
