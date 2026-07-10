"""
webapp.py

Flask-based web dashboard for the network monitor.
"""

from flask import Flask, jsonify, render_template_string

from core.flows import get_session, top_flows

app = Flask(__name__)


# -----------------------------------------------------
# Human-readable bytes
# -----------------------------------------------------

def human(size):

    value = float(size)

    units = ["B", "KB", "MB", "GB", "TB"]

    for unit in units:

        if value < 1024:
            return f"{value:.2f} {unit}"

        value /= 1024

    return f"{value:.2f} PB"


# -----------------------------------------------------
# Group flows by remote IP + protocol
# -----------------------------------------------------

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
                "status": flow.status,
                "remote": remote,
                "protocol": flow.protocol,
                "upload": 0,
                "download": 0,
                "packets": 0,
            }

        entry = grouped[key]

        entry["upload"] += flow.upload_bytes
        entry["download"] += flow.download_bytes
        entry["packets"] += flow.upload_packets + flow.download_packets

        if flow.status in ("BLACKLIST", "WHITELIST"):
            entry["status"] = flow.status

    rows = sorted(
        grouped.values(),
        key=lambda e: e["upload"] + e["download"],
        reverse=True
    )[:limit]

    return rows


# -----------------------------------------------------
# JSON API
# -----------------------------------------------------

@app.route("/api/summary")
def api_summary():

    session = get_session()

    runtime = session.runtime

    h = runtime // 3600
    m = (runtime % 3600) // 60
    s = runtime % 60

    return jsonify({
        "runtime": f"{h:02}:{m:02}:{s:02}",
        "total_upload": session.total_upload,
        "total_upload_human": human(session.total_upload),
        "total_download": session.total_download,
        "total_download_human": human(session.total_download),
        "total_packets": session.total_packets,
        "total_flows": session.total_flows,
        "unique_ips": session.unique_ips,
    })


@app.route("/api/flows")
def api_flows():

    rows = grouped_flows(100)

    for row in rows:
        row["upload_human"] = human(row["upload"])
        row["download_human"] = human(row["download"])

    return jsonify(rows)


# -----------------------------------------------------
# HTML Page
# -----------------------------------------------------

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

        h1 {
            color: #58a6ff;
            font-size: 20px;
            letter-spacing: 1px;
            margin-bottom: 20px;
        }

        .summary {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            margin-bottom: 24px;
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

        th:hover {
            color: #58a6ff;
            background: #161b22;
        }

        th.sorted-asc,
        th.sorted-desc {
            color: #58a6ff;
        }

        th .arrow {
            display: inline-block;
            margin-left: 5px;
            opacity: 0.4;
            font-size: 10px;
        }

        th.sorted-asc .arrow::after  { content: "▲"; opacity: 1; }
        th.sorted-desc .arrow::after { content: "▼"; opacity: 1; }
        th:not(.sorted-asc):not(.sorted-desc) .arrow::after { content: "⇅"; }

        td {
            padding: 8px 12px;
            border-bottom: 1px solid #21262d;
            font-size: 13px;
        }

        td.num {
            text-align: right;
            font-variant-numeric: tabular-nums;
        }

        tr:hover td {
            background: #1c2128;
        }

        .status-BLACKLIST { color: #f85149; font-weight: bold; }
        .status-WHITELIST { color: #3fb950; font-weight: bold; }
        .status-UNKNOWN   { color: #d29922; font-weight: bold; }
    </style>
</head>
<body>
    <h1>NETWORK TRAFFIC MONITOR</h1>

    <div class="summary" id="summary"></div>

    <table>
        <thead>
            <tr id="header-row">
                <th data-col="status"    data-type="str">Status    <span class="arrow"></span></th>
                <th data-col="remote"    data-type="str">Remote IP <span class="arrow"></span></th>
                <th data-col="protocol"  data-type="str">Protocol  <span class="arrow"></span></th>
                <th data-col="upload"    data-type="num" class="sorted-desc">Upload <span class="arrow"></span></th>
                <th data-col="download"  data-type="num">Download  <span class="arrow"></span></th>
                <th data-col="packets"   data-type="num">Packets   <span class="arrow"></span></th>
            </tr>
        </thead>
        <tbody id="flows"></tbody>
    </table>

    <script>
        // -----------------------------------------------
        // Sort state
        // -----------------------------------------------
        let sortCol = "upload";
        let sortDir = "desc";   // "asc" or "desc"

        // Latest data from the API, unsorted
        let latestRows = [];

        // -----------------------------------------------
        // Summary cards
        // -----------------------------------------------
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

        // -----------------------------------------------
        // Sort rows by current sortCol / sortDir
        // -----------------------------------------------
        function sortedRows(rows) {

            const ths = document.querySelectorAll("th[data-col]");
            let colType = "num";

            ths.forEach(th => {
                if (th.dataset.col === sortCol) {
                    colType = th.dataset.type;
                }
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

                if (va < vb) return sortDir === "asc" ? -1 : 1;
                if (va > vb) return sortDir === "asc" ?  1 : -1;
                return 0;
            });
        }

        // -----------------------------------------------
        // Render flows table
        // -----------------------------------------------
        function buildFlows(rows) {

            const sorted = sortedRows(rows);

            document.getElementById("flows").innerHTML = sorted.map(r => `
                <tr>
                    <td class="status-${r.status}">${r.status}</td>
                    <td>${r.remote}</td>
                    <td>${r.protocol}</td>
                    <td class="num">${r.upload_human}</td>
                    <td class="num">${r.download_human}</td>
                    <td class="num">${r.packets}</td>
                </tr>
            `).join("");

            // Update header arrows
            document.querySelectorAll("th[data-col]").forEach(th => {
                th.classList.remove("sorted-asc", "sorted-desc");
                if (th.dataset.col === sortCol) {
                    th.classList.add(sortDir === "asc" ? "sorted-asc" : "sorted-desc");
                }
            });
        }

        // -----------------------------------------------
        // Column header click → sort
        // -----------------------------------------------
        document.querySelectorAll("th[data-col]").forEach(th => {

            th.addEventListener("click", () => {

                const col = th.dataset.col;

                if (sortCol === col) {
                    // Same column: flip direction
                    sortDir = sortDir === "asc" ? "desc" : "asc";
                } else {
                    // New column: default to descending for numbers, ascending for strings
                    sortCol = col;
                    sortDir = th.dataset.type === "num" ? "desc" : "asc";
                }

                buildFlows(latestRows);
            });
        });

        // -----------------------------------------------
        // Refresh from API
        // -----------------------------------------------
        async function refresh() {
            try {
                const [summaryRes, flowsRes] = await Promise.all([
                    fetch("/api/summary"),
                    fetch("/api/flows"),
                ]);

                buildSummary(await summaryRes.json());

                latestRows = await flowsRes.json();
                buildFlows(latestRows);

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


# -----------------------------------------------------
# Entry point
# -----------------------------------------------------

def start_web_dashboard(host="0.0.0.0", port=5000):
    app.run(host=host, port=port, debug=False, use_reloader=False)