"""
webapp.py

Flask-based web dashboard for the network monitor.
"""

from flask import Flask, jsonify, render_template_string, request, session, redirect
from pathlib import Path
import sys
import os
from functools import wraps
from datetime import timedelta


root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from core.flows import get_session, top_flows
from core.alerts import (
    get_alerts,
    get_daily_usage,
    check_thresholds,
    clear_alerts,
)
from utils.config import SETTINGS

app = Flask(__name__)
# Use a more secure secret key
app.secret_key = os.environ.get('SECRET_KEY', 'network-monitor-secure-key-2024')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True if using HTTPS
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

MB = 1024 * 1024


# =====================================================
# Human-readable bytes
# =====================================================

def human(size):
    value = float(size)
    units = ["B", "KB", "MB", "GB", "TB"]

    for unit in units:
        if value < 1024:
            return f"{value:.2f} {unit}"
        value /= 1024

    return f"{value:.2f} PB"


# =====================================================
# Group flows by remote IP + protocol
# =====================================================

def grouped_flows(limit=100):
    flows = top_flows(500)
    grouped = {}

    for flow in flows:
        if flow.download_bytes > flow.upload_bytes:
            remote = flow.src_ip
        else:
            remote = flow.dst_ip

        key = (remote, flow.protocol)

        if key not in grouped:
            grouped[key] = {
                "status":   flow.status,
                "remote":   remote,
                "protocol": flow.protocol,
                "upload":   0,
                "download": 0,
                "packets":  0,
            }

        entry = grouped[key]
        entry["upload"]   += flow.upload_bytes
        entry["download"] += flow.download_bytes
        entry["packets"]  += flow.upload_packets + flow.download_packets

        if flow.status in ("BLACKLIST", "WHITELIST"):
            entry["status"] = flow.status

    return sorted(
        grouped.values(),
        key=lambda e: e["upload"] + e["download"],
        reverse=True
    )[:limit]


# =====================================================
# JSON API
# =====================================================

@app.route("/api/summary")
def api_summary():
    session_obj = get_session()

    # Run threshold checks on every summary poll
    check_thresholds(session_obj)

    runtime = session_obj.runtime
    h = runtime // 3600
    m = (runtime % 3600) // 60
    s = runtime % 60

    upload_limit   = SETTINGS.get("daily_upload_limit_mb",   0)
    download_limit = SETTINGS.get("daily_download_limit_mb", 0)

    daily = get_daily_usage()

    upload_pct   = 0
    download_pct = 0

    if upload_limit > 0:
        upload_pct = min(100, round(
            (daily["upload"] / MB) / upload_limit * 100, 1
        ))

    if download_limit > 0:
        download_pct = min(100, round(
            (daily["download"] / MB) / download_limit * 100, 1
        ))

    return jsonify({
        "runtime":              f"{h:02}:{m:02}:{s:02}",
        "total_upload":         session_obj.total_upload,
        "total_upload_human":   human(session_obj.total_upload),
        "total_download":       session_obj.total_download,
        "total_download_human": human(session_obj.total_download),
        "total_packets":        session_obj.total_packets,
        "total_flows":          session_obj.total_flows,
        "unique_ips":           session_obj.unique_ips,
        "daily": {
            "day":              daily["day"],
            "upload_mb":        round(daily["upload"]   / MB, 2),
            "download_mb":      round(daily["download"] / MB, 2),
            "upload_limit_mb":  upload_limit,
            "download_limit_mb":download_limit,
            "upload_pct":       upload_pct,
            "download_pct":     download_pct,
        }
    })


@app.route("/api/flows")
def api_flows():
    rows = grouped_flows(100)

    for row in rows:
        row["upload_human"]   = human(row["upload"])
        row["download_human"] = human(row["download"])

    return jsonify(rows)


@app.route("/api/alerts")
def api_alerts():
    return jsonify(get_alerts())


@app.route("/api/alerts/clear", methods=["POST"])
def api_clear_alerts():
    clear_alerts()
    return jsonify({"ok": True})


# =====================================================
# HTML Pages
# =====================================================

PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Network Traffic Monitor</title>
    <style>
        * { box-sizing: border-box; }

        body {
            background: #0d1117;
            color: #c9d1d9;
            font-family: "Segoe UI", Consolas, monospace;
            margin: 0;
            padding: 24px;
        }

        .navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid #30363d;
        }

        .navbar h1 {
            color: #58a6ff;
            font-size: 20px;
            letter-spacing: 1px;
            margin: 0;
        }

        .navbar-right {
            display: flex;
            gap: 16px;
            align-items: center;
        }

        h1 {
            color: #58a6ff;
            font-size: 20px;
            letter-spacing: 1px;
            margin-bottom: 20px;
        }

        /* ---- Summary cards ---- */
        .summary {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }

        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 12px 18px;
            min-width: 140px;
        }

        .card .label {
            font-size: 11px;
            color: #8b949e;
            text-transform: uppercase;
        }

        .card .value {
            font-size: 20px;
            color: #58a6ff;
            margin-top: 4px;
        }

        /* ---- Daily usage bars ---- */
        .daily-section {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }

        .daily-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 14px 18px;
            flex: 1;
            min-width: 240px;
        }

        .daily-card .label {
            font-size: 11px;
            color: #8b949e;
            text-transform: uppercase;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
        }

        .daily-card .label span { color: #c9d1d9; }

        .progress-track {
            background: #21262d;
            border-radius: 4px;
            height: 10px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.4s ease;
        }

        .progress-fill.upload   { background: #58a6ff; }
        .progress-fill.download { background: #3fb950; }
        .progress-fill.warn     { background: #d29922; }
        .progress-fill.danger   { background: #f85149; }

        .daily-card .sub {
            font-size: 11px;
            color: #8b949e;
            margin-top: 6px;
        }

        /* ---- Alerts ---- */
        .alerts-section {
            margin-bottom: 20px;
        }

        .alerts-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
        }

        .alerts-header h2 {
            font-size: 13px;
            color: #8b949e;
            text-transform: uppercase;
            margin: 0;
        }

        .btn-clear {
            background: #21262d;
            border: 1px solid #30363d;
            color: #8b949e;
            border-radius: 6px;
            padding: 3px 10px;
            font-size: 11px;
            cursor: pointer;
        }

        .btn-clear:hover { color: #c9d1d9; border-color: #58a6ff; }

        .alert-list { display: flex; flex-direction: column; gap: 6px; }

        .alert-item {
            padding: 8px 14px;
            border-radius: 6px;
            font-size: 13px;
            border-left: 3px solid;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .alert-item.upload_warn, .alert-item.download_warn {
            background: #2a1f00;
            border-color: #d29922;
            color: #e3b341;
        }

        .alert-item.upload_limit, .alert-item.download_limit {
            background: #2a0000;
            border-color: #f85149;
            color: #f85149;
        }

        .alert-item.info {
            background: #161b22;
            border-color: #30363d;
            color: #8b949e;
        }

        .alert-time {
            font-size: 11px;
            opacity: 0.6;
            white-space: nowrap;
            margin-left: 16px;
        }

        .no-alerts {
            font-size: 13px;
            color: #3fb950;
            padding: 8px 0;
        }

        /* ---- Flows table ---- */
        table {
            width: 100%;
            border-collapse: collapse;
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            overflow: hidden;
        }

        th {
            background: #0d1117;
            color: #8b949e;
            text-transform: uppercase;
            font-size: 11px;
            padding: 10px 12px;
            text-align: left;
            cursor: pointer;
            user-select: none;
            white-space: nowrap;
        }

        th:hover { color: #58a6ff; background: #161b22; }

        th.sorted-asc, th.sorted-desc { color: #58a6ff; }

        th .arrow { display: inline-block; margin-left: 5px; opacity: 0.4; font-size: 10px; }
        th.sorted-asc  .arrow::after { content: "▲"; opacity: 1; }
        th.sorted-desc .arrow::after { content: "▼"; opacity: 1; }
        th:not(.sorted-asc):not(.sorted-desc) .arrow::after { content: "⇅"; }

        td {
            padding: 8px 12px;
            border-bottom: 1px solid #21262d;
            font-size: 13px;
        }

        td.num { text-align: right; font-variant-numeric: tabular-nums; }
        tr:hover td { background: #1c2128; }

        .status-BLACKLIST { color: #f85149; font-weight: bold; }
        .status-WHITELIST { color: #3fb950; font-weight: bold; }
        .status-UNKNOWN   { color: #d29922; font-weight: bold; }
    </style>
</head>
<body>
    <div class="navbar">
        <h1>NETWORK TRAFFIC MONITOR</h1>
    </div>

    <!-- Summary cards -->
    <div class="summary" id="summary"></div>

    <!-- Daily usage bars -->
    <div class="daily-section" id="daily"></div>

    <!-- Alerts -->
    <div class="alerts-section">
        <div class="alerts-header">
            <h2>Alerts</h2>
            <button class="btn-clear" onclick="clearAlerts()">Dismiss all</button>
        </div>
        <div class="alert-list" id="alerts">
            <div class="no-alerts">No alerts.</div>
        </div>
    </div>

    <!-- Flows table -->
    <table>
        <thead>
            <tr id="header-row">
                <th data-col="status"   data-type="str">Status   <span class="arrow"></span></th>
                <th data-col="remote"   data-type="str">Remote IP<span class="arrow"></span></th>
                <th data-col="protocol" data-type="str">Protocol <span class="arrow"></span></th>
                <th data-col="upload"   data-type="num" class="sorted-desc">Upload <span class="arrow"></span></th>
                <th data-col="download" data-type="num">Download <span class="arrow"></span></th>
                <th data-col="packets"  data-type="num">Packets  <span class="arrow"></span></th>
            </tr>
        </thead>
        <tbody id="flows"></tbody>
    </table>

    <script>
        // ---- Sort state ----
        let sortCol = "upload";
        let sortDir = "desc";
        let latestRows = [];

        // ---- Summary ----
        function buildSummary(s) {
            const cards = [
                ["Runtime",        s.runtime],
                ["Total Upload",   s.total_upload_human],
                ["Total Download", s.total_download_human],
                ["Packets",        s.total_packets.toLocaleString()],
                ["Flows",          s.total_flows],
                ["Unique IPs",     s.unique_ips],
            ];

            document.getElementById("summary").innerHTML = cards.map(
                ([label, value]) => `
                <div class="card">
                    <div class="label">${label}</div>
                    <div class="value">${value}</div>
                </div>`
            ).join("");
        }

        // ---- Daily usage bars ----
        function buildDaily(d) {

            if (d.upload_limit_mb === 0 && d.download_limit_mb === 0) {
                document.getElementById("daily").innerHTML = "";
                return;
            }

            const bars = [];

            if (d.upload_limit_mb > 0) {

                const pct   = d.upload_pct;
                const cls   = pct >= 100 ? "danger" : pct >= 80 ? "warn" : "upload";

                bars.push(`
                <div class="daily-card">
                    <div class="label">
                        Daily Upload
                        <span>${d.upload_mb} MB / ${d.upload_limit_mb} MB</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill ${cls}" style="width:${pct}%"></div>
                    </div>
                    <div class="sub">${pct}% used</div>
                </div>`);
            }

            if (d.download_limit_mb > 0) {

                const pct = d.download_pct;
                const cls = pct >= 100 ? "danger" : pct >= 80 ? "warn" : "download";

                bars.push(`
                <div class="daily-card">
                    <div class="label">
                        Daily Download
                        <span>${d.download_mb} MB / ${d.download_limit_mb} MB</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill ${cls}" style="width:${pct}%"></div>
                    </div>
                    <div class="sub">${pct}% used</div>
                </div>`);
            }

            document.getElementById("daily").innerHTML = bars.join("");
        }

        // ---- Alerts ----
        function buildAlerts(alerts) {

            const el = document.getElementById("alerts");

            if (!alerts.length) {
                el.innerHTML = '<div class="no-alerts">No alerts.</div>';
                return;
            }

            el.innerHTML = alerts.map(a => {

                const t  = new Date(a.timestamp * 1000);
                const ts = t.toLocaleTimeString();

                return `
                <div class="alert-item ${a.type}">
                    <span>${a.message}</span>
                    <span class="alert-time">${ts}</span>
                </div>`;
            }).join("");
        }

        async function clearAlerts() {
            await fetch("/api/alerts/clear", { method: "POST" });
            document.getElementById("alerts").innerHTML =
                '<div class="no-alerts">No alerts.</div>';
        }

        // ---- Flows table ----
        function sortedRows(rows) {

            const ths   = document.querySelectorAll("th[data-col]");
            let colType = "num";

            ths.forEach(th => {
                if (th.dataset.col === sortCol) colType = th.dataset.type;
            });

            return [...rows].sort((a, b) => {

                let va = a[sortCol];
                let vb = b[sortCol];

                if (colType === "num") {
                    va = Number(va);
                    vb = Number(vb);
                } else {
                    va = String(va).toLowerCase();
                    vb = String(vb).toLowerCase();
                }

                if (va < vb) return sortDir === "asc" ? -1 :  1;
                if (va > vb) return sortDir === "asc" ?  1 : -1;
                return 0;
            });
        }

        function buildFlows(rows) {

            document.getElementById("flows").innerHTML = sortedRows(rows).map(r => `
                <tr>
                    <td class="status-${r.status}">${r.status}</td>
                    <td>${r.remote}</td>
                    <td>${r.protocol}</td>
                    <td class="num">${r.upload_human}</td>
                    <td class="num">${r.download_human}</td>
                    <td class="num">${r.packets}</td>
                </tr>
            `).join("");

            document.querySelectorAll("th[data-col]").forEach(th => {
                th.classList.remove("sorted-asc", "sorted-desc");
                if (th.dataset.col === sortCol) {
                    th.classList.add(sortDir === "asc" ? "sorted-asc" : "sorted-desc");
                }
            });
        }

        document.querySelectorAll("th[data-col]").forEach(th => {
            th.addEventListener("click", () => {
                const col = th.dataset.col;
                if (sortCol === col) {
                    sortDir = sortDir === "asc" ? "desc" : "asc";
                } else {
                    sortCol = col;
                    sortDir = th.dataset.type === "num" ? "desc" : "asc";
                }
                buildFlows(latestRows);
            });
        });

        // ---- Refresh ----
        async function refresh() {
            try {
                const [summaryRes, flowsRes, alertsRes] = await Promise.all([
                    fetch("/api/summary"),
                    fetch("/api/flows"),
                    fetch("/api/alerts"),
                ]);

                const summary = await summaryRes.json();
                buildSummary(summary);
                buildDaily(summary.daily);

                latestRows = await flowsRes.json();
                buildFlows(latestRows);

                buildAlerts(await alertsRes.json());

            } catch (e) {
                console.error("Refresh failed:", e);
            }
        }

        refresh();
        setInterval(refresh, 1000);
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE)


# =====================================================
# Entry point
# =====================================================

def start_web_dashboard(host="0.0.0.0", port=5000):
    print(f"[Network Monitor] Starting web dashboard on {host}:{port}")
    app.run(host=host, port=port, debug=False, use_reloader=False)
