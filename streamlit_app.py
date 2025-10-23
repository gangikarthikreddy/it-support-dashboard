import streamlit as st
import requests
import psutil
import pandas as pd
import time

# --- CONFIG ---
API_BASE = "http://127.0.0.1:5000"
st.set_page_config(page_title="IT Support Dashboard", layout="wide")

# --- HEADER ---
st.markdown(
    """
    <style>
        body { background-color: #0E1117; color: white; }
        .big-title {
            font-size: 36px; font-weight: 800; color: #4FC3F7;
            text-align: center; margin-bottom: 10px;
        }
        .sub-title {
            font-size: 20px; text-align: center; color: #BBBBBB; margin-bottom: 30px;
        }
        .card {
            background: #1E1E1E; padding: 20px; border-radius: 15px;
            box-shadow: 0 0 15px rgba(79,195,247,0.1);
            margin-bottom: 10px;
        }
        .status-open {color: #FF6B6B; font-weight: bold;}
        .status-progress {color: #FFD93D; font-weight: bold;}
        .status-resolved {color: #6BFF6B; font-weight: bold;}
    </style>
    <div class="big-title">💻 IT Support & Troubleshooting Dashboard</div>
    <div class="sub-title">Monitor system health, manage helpdesk tickets, and automate support tasks</div>
    """,
    unsafe_allow_html=True
)

# --- SYSTEM HEALTH SECTION ---
st.markdown("### 🔍 System Health Monitor")
col1, col2, col3 = st.columns(3)

if st.button("Refresh Health Metrics"):
    try:
        res = requests.get(f"{API_BASE}/health", timeout=5)
        res.raise_for_status()
        data = res.json()
        col1.metric("🧠 CPU Usage", f"{data['cpu_percent']}%")
        col2.metric("💾 Memory Usage", f"{data['memory_percent']}%")
        col3.metric("🧱 Disk Usage", f"{data['disk_percent']}%")
        st.success("System health updated successfully ✅")
    except Exception as e:
        st.error(f"❌ Could not fetch system health: {e}")

st.markdown("---")

# --- LIVE MONITORING SECTION ---
st.markdown("### 📈 Real-Time System Health Charts")

chart_placeholder = st.empty()
status_placeholder = st.empty()

if "monitoring" not in st.session_state:
    st.session_state.monitoring = False
if "cpu_data" not in st.session_state:
    st.session_state.cpu_data, st.session_state.mem_data, st.session_state.disk_data, st.session_state.timestamps = [], [], [], []

col1, col2 = st.columns(2)
start_btn = col1.button("▶️ Start Monitoring")
stop_btn = col2.button("⏹️ Stop Monitoring")

if start_btn:
    st.session_state.monitoring = True
    status_placeholder.info("🟢 Monitoring started... collecting data every 2 seconds.")
if stop_btn:
    st.session_state.monitoring = False
    status_placeholder.warning("🛑 Monitoring stopped.")

if st.session_state.monitoring:
    while st.session_state.monitoring:
        cpu, mem, disk = psutil.cpu_percent(interval=1), psutil.virtual_memory().percent, psutil.disk_usage('/').percent
        ts = time.strftime("%H:%M:%S")

        st.session_state.cpu_data.append(cpu)
        st.session_state.mem_data.append(mem)
        st.session_state.disk_data.append(disk)
        st.session_state.timestamps.append(ts)

        if len(st.session_state.cpu_data) > 20:
            st.session_state.cpu_data.pop(0)
            st.session_state.mem_data.pop(0)
            st.session_state.disk_data.pop(0)
            st.session_state.timestamps.pop(0)

        df = pd.DataFrame({
            "Time": st.session_state.timestamps,
            "CPU (%)": st.session_state.cpu_data,
            "Memory (%)": st.session_state.mem_data,
            "Disk (%)": st.session_state.disk_data
        }).set_index("Time")

        chart_placeholder.line_chart(df)
        time.sleep(2)

st.markdown("---")

# --- LOGIN + TICKET VIEW SECTION ---
st.markdown("### 🔐 Helpdesk Access")

login_col1, login_col2 = st.columns([2, 1])
with login_col1:
    username = st.text_input("Username", value="admin", key="login_username")
    password = st.text_input("Password", type="password", value="password", key="login_password")

with login_col2:
    if st.button("Login & View Tickets"):
        try:
            res = requests.post(f"{API_BASE}/login", json={"username": username, "password": password}, timeout=5)
            if res.status_code == 200:
                st.success("✅ Logged in successfully!")

                t = requests.get(f"{API_BASE}/tickets", timeout=5)
                t.raise_for_status()
                tickets = t.json()

                if tickets:
                    st.markdown("### 🎟️ Current Tickets")
                    for ticket in tickets:
                        with st.expander(f"Ticket #{ticket['id']} — {ticket['title']}"):
                            st.write(f"**Description:** {ticket['description']}")
                            st.write(f"**Created At:** {ticket['created_at']}")

                            # Status color
                            color_class = (
                                "status-open" if ticket["status"] == "Open" else
                                "status-progress" if ticket["status"] == "In Progress" else
                                "status-resolved"
                            )
                            st.markdown(f"**Current Status:** <span class='{color_class}'>{ticket['status']}</span>", unsafe_allow_html=True)

                            # Dropdown for new status
                            new_status = st.selectbox(
                                "Update Status",
                                ["Open", "In Progress", "Resolved"],
                                index=["Open", "In Progress", "Resolved"].index(ticket["status"]),
                                key=f"status_{ticket['id']}"
                            )

                            if st.button("💾 Save Status", key=f"save_{ticket['id']}"):
                                try:
                                    res = requests.put(f"{API_BASE}/tickets/{ticket['id']}", json={"status": new_status}, timeout=5)
                                    if res.status_code == 200:
                                        st.success(f"✅ Ticket #{ticket['id']} updated to '{new_status}'")
                                    else:
                                        st.error("⚠️ Failed to update ticket.")
                                except Exception as e:
                                    st.error(f"Error: {e}")
                else:
                    st.info("No tickets available yet.")
            else:
                st.error("❌ Invalid username or password.")
        except Exception as e:
            st.error(f"⚠️ Error fetching tickets: {e}")

st.markdown("---")

# --- CREATE NEW TICKET SECTION ---
st.markdown("### 🧾 Create New Support Ticket")

with st.form("create_ticket_form"):
    title = st.text_input("Ticket Title", placeholder="e.g. Network connectivity issue", key="ticket_title")
    description = st.text_area("Description", placeholder="Describe the issue in detail...", key="ticket_description")
    submitted = st.form_submit_button("Submit Ticket")

    if submitted:
        try:
            res = requests.post(f"{API_BASE}/tickets", json={"title": title, "description": description}, timeout=5)
            if res.status_code == 201:
                st.success("🎉 Ticket created successfully!")
            else:
                st.error("⚠️ Failed to create ticket.")
        except Exception as e:
            st.error(f"❌ Error submitting ticket: {e}")

st.markdown("---")

# --- FOOTER ---
st.markdown(
    """
    <div style="text-align:center; color:gray; margin-top:20px;">
        Built with ❤️ using Python, Flask & Streamlit | IT Support Automation © 2025
    </div>
    """,
    unsafe_allow_html=True
)
