"""
Digital Wellbeing Tracker
-------------------------------------
Run:
    pip install -r requirements.txt
    streamlit run digital_wellbeing_app.py
"""

from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import uuid

st.set_page_config(page_title="Digital Wellbeing Tracker", layout="wide")

# ---------- Helper Functions ----------
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def duration_minutes(start, end):
    return (pd.to_datetime(end) - pd.to_datetime(start)).total_seconds() / 60.0

def load_sessions():
    if "sessions" not in st.session_state:
        st.session_state.sessions = pd.DataFrame(columns=[
            "id", "start", "end", "app", "category", "notes", "duration_min"
        ])
    return st.session_state.sessions

def save_sessions(df):
    st.session_state.sessions = df.copy()

def add_session(start, end, app, category, notes=""):
    df = load_sessions()
    sid = str(uuid.uuid4())
    dur = round(duration_minutes(start, end), 2)
    new = {"id": sid, "start": start, "end": end, "app": app, "category": category, "notes": notes, "duration_min": dur}
    df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
    save_sessions(df)

def export_csv(df):
    return df.to_csv(index=False).encode("utf-8")

# ---------- UI Layout ----------
st.title("📱 Digital Wellbeing Tracker")
st.markdown("Track your daily screen time, set focus goals, and monitor app usage to improve productivity and mental health.")

# Columns Layout
left, mid, right = st.columns([1,1,1])

# ---------- LEFT: Manual and Live Logging ----------
with left:
    st.header("📋 Add New Session")

    app_name = st.text_input("App / Activity name", value="browser")
    category = st.selectbox("Category", ["Social", "Study", "Productivity", "Entertainment", "Other"])
    start_time = st.datetime_input("Start time", value=datetime.now() - timedelta(minutes=5))
    end_time = st.datetime_input("End time", value=datetime.now())
    notes = st.text_area("Notes (optional)", height=50)

    if st.button("Add Session"):
        if end_time <= start_time:
            st.error("❌ End time must be after start time.")
        else:
            add_session(start_time.strftime("%Y-%m-%d %H:%M:%S"),
                        end_time.strftime("%Y-%m-%d %H:%M:%S"),
                        app_name, category, notes)
            st.success("✅ Session added successfully!")

    st.markdown("---")
    st.header("⏱️ Live Timer")

    if "live_running" not in st.session_state:
        st.session_state.live_running = False

    live_app = st.text_input("Current activity", value="Reading")
    live_cat = st.selectbox("Category", ["Study", "Productivity", "Social", "Entertainment", "Other"], key="live_cat")

    if st.session_state.live_running:
        if st.button("Stop Live Session"):
            st.session_state.live_running = False
            add_session(st.session_state.live_start.strftime("%Y-%m-%d %H:%M:%S"),
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        live_app, live_cat, "Live session")
            st.success("🟢 Live session stopped and saved.")
    else:
        if st.button("Start Live Session"):
            st.session_state.live_running = True
            st.session_state.live_start = datetime.now()
            st.info("Live tracking started!")

    if st.session_state.live_running:
        elapsed = (datetime.now() - st.session_state.live_start).total_seconds() / 60
        st.metric("Live Time (mins)", f"{elapsed:.2f}")

# ---------- MIDDLE: Analytics ----------
with mid:
    st.header("📊 Usage Analytics")

    df = load_sessions()
    if df.empty:
        st.info("No sessions recorded yet. Add one to see analytics.")
    else:
        df["start_dt"] = pd.to_datetime(df["start"])
        df["end_dt"] = pd.to_datetime(df["end"])

        # Filter by date range
        min_date = df["start_dt"].min().date()
        max_date = df["end_dt"].max().date()
        date_range = st.date_input("Select date range", (min_date, max_date))

        mask = (df["start_dt"].dt.date >= date_range[0]) & (df["end_dt"].dt.date <= date_range[1])
        view = df.loc[mask]

        total_min = view["duration_min"].sum()
        st.metric("Total Screen Time (mins)", f"{total_min:.1f}")

        by_app = view.groupby("app")["duration_min"].sum().sort_values(ascending=False)
        by_cat = view.groupby("category")["duration_min"].sum().sort_values(ascending=False)

        st.subheader("Top Apps")
        st.dataframe(by_app.reset_index().rename(columns={"duration_min": "Minutes"}).head(10), height=200)

        st.subheader("Usage by Category")
        st.dataframe(by_cat.reset_index().rename(columns={"duration_min": "Minutes"}), height=150)

        st.line_chart(view.groupby(view["start_dt"].dt.date)["duration_min"].sum())

    st.markdown("---")
    st.header("📂 Import / Export Data")

    uploaded = st.file_uploader("Import CSV file", type=["csv"])
    if uploaded:
        try:
            imp = pd.read_csv(uploaded)
            save_sessions(pd.concat([load_sessions(), imp], ignore_index=True))
            st.success("✅ Data imported successfully.")
        except Exception as e:
            st.error(f"Import failed: {e}")

    if st.button("Export Sessions as CSV"):
        df = load_sessions()
        if df.empty:
            st.warning("No data to export.")
        else:
            csv_data = export_csv(df)
            st.download_button("⬇️ Download CSV", data=csv_data, file_name="digital_wellbeing_sessions.csv", mime="text/csv")

# ---------- RIGHT: Focus Timer and Alerts ----------
with right:
    st.header("🎯 Focus Timer")
    if "focus_running" not in st.session_state:
        st.session_state.focus_running = False

    focus_mins = st.number_input("Focus Duration (min)", 5, 180, 25)
    if not st.session_state.focus_running:
        if st.button("Start Focus Session"):
            st.session_state.focus_running = True
            st.session_state.focus_end = datetime.now() + timedelta(minutes=focus_mins)
            st.info("Focus session started!")
    else:
        if st.button("Stop Focus Session"):
            st.session_state.focus_running = False
            st.success("Focus session stopped.")

    if st.session_state.focus_running:
        remaining = st.session_state.focus_end - datetime.now()
        if remaining.total_seconds() <= 0:
            st.session_state.focus_running = False
            st.balloons()
            st.success("🎉 Focus session completed!")
        else:
            mins = int(remaining.total_seconds() // 60)
            secs = int(remaining.total_seconds() % 60)
            st.metric("Time Remaining", f"{mins} min {secs} sec")

    st.markdown("---")
    st.header("⚠️ Daily Limit Alert")

    if "daily_limit" not in st.session_state:
        st.session_state.daily_limit = 240  # default 4 hours

    daily_limit = st.number_input("Set Daily Limit (minutes)", 30, 1440, st.session_state.daily_limit)
    st.session_state.daily_limit = daily_limit

    df = load_sessions()
    if not df.empty:
        today = datetime.now().date()
        df["start_dt"] = pd.to_datetime(df["start"])
        today_total = df.loc[df["start_dt"].dt.date == today, "duration_min"].sum()

        st.metric("Today's Usage", f"{today_total:.1f} / {daily_limit} mins")
        if today_total >= daily_limit:
            st.error("🚨 You have exceeded your daily limit!")
        elif today_total >= 0.8 * daily_limit:
            st.warning("⚠️ You are close to your daily limit.")

# ---------- Sessions Table ----------
st.markdown("---")
st.subheader("📄 Recorded Sessions")

df = load_sessions()
if df.empty:
    st.info("No sessions available.")
else:
    st.dataframe(df.drop(columns=["start_dt", "end_dt"], errors="ignore"), height=300)

    delete_id = st.text_input("Enter Session ID to delete")
    if st.button("Delete Session"):
        if delete_id.strip():
            new_df = df[df["id"] != delete_id.strip()]
            save_sessions(new_df)
            st.success("Session deleted.")
        else:
            st.warning("Please enter a valid session ID.")
