from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from safestep.admin_auth import authenticate_admin
from safestep.deployments import DeploymentRegistry, SignalDeployment


registry = DeploymentRegistry()

st.set_page_config(page_title="SafeStep Admin", layout="wide")
st.title("SafeStep Admin Dashboard")

admin_user = os.getenv("SAFESTEP_ADMIN_USER", "admin")
admin_pass = os.getenv("SAFESTEP_ADMIN_PASSWORD", "admin123")

if "authed" not in st.session_state:
    st.session_state.authed = False

if not st.session_state.authed:
    st.subheader("Admin Login")
    st.caption(
        "Use the configured credential values (defaults: username `admin`, password `admin123`). "
        "If needed, entering env var keys such as `SAFESTEP_ADMIN_USER` will resolve to their values."
    )
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate_admin(username, password, admin_user, admin_pass):
            st.session_state.authed = True
            st.success("Logged in")
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

st.subheader("Deployed Signals")

with st.form("add_signal"):
    signal_id = st.text_input("Signal ID", placeholder="SIG-001")
    location = st.text_input("Location", placeholder="Main St & 4th")
    controller_endpoint = st.text_input("Controller Endpoint", placeholder="tcp://controller.local:502")
    emergency_contact = st.text_input("Emergency Contact", placeholder="911")
    camera_ids_raw = st.text_area("Camera IDs (comma-separated)", placeholder="CAM-01,CAM-02")

    submitted = st.form_submit_button("Add / Update Deployment")

    if submitted:
        camera_ids = [item.strip() for item in camera_ids_raw.split(",") if item.strip()]
        if not signal_id.strip() or not location.strip() or not controller_endpoint.strip() or not emergency_contact.strip():
            st.error("Please fill all required deployment fields.")
        else:
            registry.add_deployment(
                SignalDeployment(
                    signal_id=signal_id.strip(),
                    location=location.strip(),
                    controller_endpoint=controller_endpoint.strip(),
                    emergency_contact=emergency_contact.strip(),
                    camera_ids=camera_ids,
                )
            )
            st.success(f"Deployment saved: {signal_id.strip()}")

rows = []
for deployment in registry.list_deployments():
    rows.append(
        {
            "Signal ID": deployment.signal_id,
            "Location": deployment.location,
            "Controller Endpoint": deployment.controller_endpoint,
            "Emergency Contact": deployment.emergency_contact,
            "Camera IDs": ", ".join(deployment.camera_ids),
            "Camera Count": len(deployment.camera_ids),
        }
    )

if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
else:
    st.info("No deployed signals yet. Add one above.")

st.subheader("Connected Cameras")
selected_signal = st.selectbox(
    "Select Signal",
    options=[d.signal_id for d in registry.list_deployments()],
    index=None,
    placeholder="Choose a signal",
)

if selected_signal:
    connections = registry.get_camera_connections(selected_signal)
    camera_rows = [{"Camera ID": c.camera_id, "Connected": c.connected} for c in connections]
    if camera_rows:
        st.dataframe(pd.DataFrame(camera_rows), use_container_width=True)
    else:
        st.warning("No cameras configured for this signal.")
