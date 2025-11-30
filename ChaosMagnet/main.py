# main.py
import dearpygui.dearpygui as dpg
import config
import threading
import zmq
import json
import time
from core import ChaosEngine
from harvester import SystemHarvester, AudioHarvester, VideoHarvester, MouseHarvester, TRNGHarvester

print("DEBUG: Starting Application...")

# --- Init Engine ---
try:
    engine = ChaosEngine()
    print("DEBUG: Engine Init Complete.")
except Exception as e:
    print(f"FATAL: Engine failed to init: {e}")
    exit(1)

# --- Init Harvesters ---
harvesters = {
    "System/CPU": SystemHarvester(engine, "SYS", config.RATE_SYSTEM),
    "Hardware/TRNG": TRNGHarvester(engine, "TRNG", config.RATE_TRNG),
    "Audio (Mic)": AudioHarvester(engine, "AUDIO", config.RATE_AUDIO),
    "Video (Cam)": VideoHarvester(engine, "VIDEO", config.RATE_VIDEO),
    "HID (Mouse)": MouseHarvester(engine)
}

# Start Harvesters
print("DEBUG: Starting Harvesters...")
for h_name, h_obj in harvesters.items():
    if hasattr(h_obj, 'start') and not isinstance(h_obj, MouseHarvester):
        h_obj.start()

# --- ZMQ Faucet (Server Thread) ---
# This allows other LOCAL apps to ask for keys via TCP (Legacy/Local support)
def faucet_server():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    try:
        socket.bind("tcp://*:5555")
        engine.log("FAUCET: Listening on tcp://*:5555")
        
        while True:
            message = socket.recv()
            if message == b"GET_PQC":
                # Automatically saves to Vault inside this function
                bundle = engine.get_pqc_bundle(requester="REMOTE_CLIENT")
                if bundle:
                    socket.send_json(bundle)
                    engine.log("FAUCET: Dispensed & Vaulted Key")
                else:
                    socket.send_string("ERROR: PQC Not Loaded")
            elif message == b"STATUS":
                metrics = engine.get_metrics()
                socket.send_json({"entropy": metrics['current_entropy'], "pool": metrics['pool_hex']})
            else:
                socket.send_string("UNKNOWN COMMAND")
    except Exception as e:
        engine.log(f"FAUCET ERROR: {e}")

faucet_thread = threading.Thread(target=faucet_server, daemon=True)
faucet_thread.start()

# --- GUI Callbacks ---
def toggle_harvester(sender, app_data, user_data):
    h_name = user_data
    harvester = harvesters[h_name]
    if not harvester.available:
        dpg.set_value(sender, False)
        return
    state = app_data
    harvester.toggle(state)
    status = "Active" if state else "Inactive"
    engine.log(f"Toggle: {h_name} -> {status}")

def toggle_network(sender, app_data, user_data):
    """Toggles the HTTP export to Ayatoki"""
    engine.network_mode = app_data
    status = "ENABLED" if app_data else "DISABLED"
    engine.log(f"MANUAL: Network Uplink -> {status}")

def manual_gen_key(sender, app_data, user_data):
    """Callback for the GUI Button"""
    bundle = engine.get_pqc_bundle(requester="GUI_USER")
    if bundle:
        dpg.set_value("txt_last_key", f"Last Key: {bundle['kyber_pk'][:16]}... (Saved)")
    else:
        dpg.set_value("txt_last_key", "Error: PQC Engine Offline")

def update_gui():
    metrics = engine.get_metrics()
    
    # Update Plots and Stats
    dpg.set_value("series_entropy", [list(range(len(metrics["history"]))), metrics["history"]])
    dpg.set_value("txt_bytes", f"Bytes Harvested: {metrics['total_bytes']}")
    
    # Entropy Quality (Now uses the fixed Display Pool math)
    dpg.set_value("txt_quality", f"Current Pool Entropy: {metrics['current_entropy']:.4f} / 8.0")
    dpg.set_value("txt_pool", metrics["pool_hex"])
    dpg.set_value("txt_console", "\n".join(metrics["logs"]))
    
    # Update PQC Status
    if metrics["pqc_ready"]:
         dpg.configure_item("txt_pqc_status", default_value="PQC STATUS: ACTIVE (Kyber/Falcon)", color=config.COLOR_PLOT_LINE)
    else:
         dpg.configure_item("txt_pqc_status", default_value="PQC STATUS: DISABLED (Missing Lib)", color=config.COLOR_ERROR)

    # Update Network Status (New Phase 3 Indicator)
    if metrics["net_mode"]:
        dpg.configure_item("txt_net_status", default_value="UPLINK: ONLINE (Ayatoki)", color=config.COLOR_PLOT_LINE)
    else:
        dpg.configure_item("txt_net_status", default_value="UPLINK: OFFLINE (Local Mode)", color=config.COLOR_WARN)


# --- Build UI ---
dpg.create_context()
with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, config.COLOR_WINDOW)
        dpg.add_theme_color(dpg.mvThemeCol_Text, config.COLOR_TEXT)
        dpg.add_theme_color(dpg.mvThemeCol_CheckMark, config.COLOR_ACCENT)
        dpg.add_theme_color(dpg.mvThemeCol_Button, config.COLOR_ACCENT_DIM)
        dpg.add_theme_color(dpg.mvThemeCol_PlotLines, config.COLOR_PLOT_LINE)
        dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)

dpg.bind_theme(global_theme)

with dpg.window(tag="Primary Window"):
    dpg.add_text("PROJECT CHAOS MAGNET // COBRA LAB", color=config.COLOR_ACCENT)
    
    # Status Indicators
    with dpg.group(horizontal=True):
        dpg.add_text("PQC STATUS: INIT...", tag="txt_pqc_status")
        dpg.add_spacer(width=20)
        dpg.add_text("UPLINK: INIT...", tag="txt_net_status")

    dpg.add_separator()
    
    with dpg.group(horizontal=True):
        # Left: Controls
        with dpg.group(width=200):
            dpg.add_text("SOURCE CONTROL")
            for name in harvesters.keys():
                enabled = harvesters[name].available
                dpg.add_checkbox(label=name, callback=toggle_harvester, user_data=name, default_value=False, enabled=enabled)
                if not enabled:
                    dpg.add_text("(Not Detected)", color=config.COLOR_ERROR)
            
            dpg.add_spacer(height=10)
            dpg.add_text("NETWORK CONTROL")
            dpg.add_checkbox(label="Ayatoki Uplink", default_value=True, callback=toggle_network)
            
            dpg.add_spacer(height=10)
            dpg.add_text("VAULT CONTROL")
            dpg.add_button(label="MINT KEYPAIR", callback=manual_gen_key, width=-1)
            dpg.add_text("Waiting...", tag="txt_last_key", color=config.COLOR_ACCENT)

        # Right: Stats
        with dpg.group():
            dpg.add_text("BYTES HARVESTED: 0", tag="txt_bytes")
            dpg.add_text("POOL QUALITY: 0.0", tag="txt_quality", color=config.COLOR_ACCENT)

    dpg.add_spacer(height=10)
    with dpg.plot(label="Real-time Entropy Quality", height=200, width=-1):
        dpg.add_plot_legend()
        dpg.add_plot_axis(dpg.mvXAxis, label="Time (Ticks)", no_tick_labels=True)
        with dpg.plot_axis(dpg.mvYAxis, label="Shannon Entropy"):
            dpg.set_axis_limits(dpg.last_item(), 0, 8.5)
            dpg.add_line_series([], [], label="Pool Entropy", tag="series_entropy")

    dpg.add_spacer(height=10)
    dpg.add_text("LIVE POOL STATE (SHA-3 MIX):")
    dpg.add_input_text(tag="txt_pool", width=-1, readonly=True)
    dpg.add_spacer(height=10)
    dpg.add_text("AUDIT LOG:")
    dpg.add_input_text(tag="txt_console", width=-1, height=150, multiline=True, readonly=True)

dpg.create_viewport(title="Cobra Lab // ChaosMagnet", width=700, height=800)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)

while dpg.is_dearpygui_running():
    update_gui()
    dpg.render_dearpygui_frame()

for h in harvesters.values():
    if hasattr(h, 'stop_event'):
        h.stop_event.set()
dpg.destroy_context()