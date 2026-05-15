DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>Flight Tracker Dashboard v2</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --bg: #0f172a; --bg2: #1e293b; --bg3: #334155;
            --text: #f8fafc; --text2: #94a3b8;
            --blue: #3b82f6; --green: #22c55e; --yellow: #f59e0b; --red: #ef4444;
        }
        body { font-family: -apple-system, system-ui, sans-serif; background: var(--bg); color: var(--text); }
        .header { background: var(--bg2); padding: 1rem 2rem; border-bottom: 1px solid var(--bg3); display: flex; align-items: center; gap: 1rem; }
        .dot { width: 10px; height: 10px; border-radius: 50%; background: var(--green); animation: pulse 2s infinite; }
        @keyframes pulse { 50% { opacity: .5; } }
        .container { max-width: 1400px; margin: 0 auto; padding: 2rem; }
        .grid { display: grid; gap: 1rem; }
        .grid-4 { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
        .card { background: var(--bg2); border-radius: 12px; padding: 1.5rem; border: 1px solid var(--bg3); }
        .card .lbl { font-size: .875rem; color: var(--text2); margin-bottom: .5rem; }
        .card .val { font-size: 2rem; font-weight: 700; }
        .flex { display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; }
        .btn { background: var(--blue); color: #fff; border: 0; padding: .75rem 1.5rem; border-radius: 8px; cursor: pointer; font-weight: 500; }
        .btn:hover { opacity: .9; }
        .btn-g { background: var(--green); }
        .btn-y { background: var(--yellow); color: #000; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: .75rem; text-align: left; border-bottom: 1px solid var(--bg3); }
        th { color: var(--text2); font-weight: 500; }
        .rk { display: inline-flex; width: 24px; height: 24px; border-radius: 6px; align-items: center; justify-content: center; font-size: .75rem; font-weight: 700; }
        .r1 { background: #fbbf24; color: #000; } .r2 { background: #94a3b8; color: #000; } .r3 { background: #cd7f32; color: #fff; }
        .err { background: var(--red); color: #fff; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
        .chart { width: 100%; height: 300px; margin: 1rem 0; }
        .mb2 { margin-bottom: 2rem; }
        .mt1 { margin-top: 1rem; }
        .tabs { display: flex; gap: 0; margin-bottom: 1rem; }
        .tab { padding: .75rem 1.5rem; background: var(--bg3); cursor: pointer; border: 0; color: var(--text2); }
        .tab.active { background: var(--blue); color: #fff; }
        .tab:first-child { border-radius: 8px 0 0 8px; }
        .tab:last-child { border-radius: 0 8px 8px 0; }
        .max-h-400 { max-height: 400px; overflow-y: auto; }
        .text-success { color: var(--green); }
        .text-danger { color: var(--red); }
    </style>
</head>
<body>
    <div class="header">
        <span class="dot"></span>
        <h1>Flight Tracker v2</h1>
        <span style="color:var(--text2);font-size:.875rem;margin-left:auto">
            <span id="refresh-indicator"></span>
            <span id="last-api-check" style="margin-left:1rem;color:var(--yellow)"></span>
        </span>
    </div>
    <div class="container">
        <div id="err"></div>

        <div class="grid grid-4 mb2">
            <div class="card"><div class="lbl">Flights Searched</div><div class="val" id="m-flights">-</div></div>
            <div class="card"><div class="lbl">Price Checks</div><div class="val" id="m-checks">-</div></div>
            <div class="card"><div class="lbl">Alerts Sent</div><div class="val" id="m-alerts">-</div></div>
            <div class="card"><div class="lbl">Rate Limits</div><div class="val" id="m-rl">-</div></div>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="switchTab('routes')">Routes</button>
            <button class="tab" onclick="switchTab('stats')">Statistics</button>
            <button class="tab" onclick="switchTab('alerts')">Alert History</button>
        </div>

        <div id="tab-routes">
            <div class="flex mb2">
                <button class="btn btn-g" onclick="sim('MDE','ADZ')">Sim MDE→ADZ</button>
                <button class="btn btn-g" onclick="sim('PEI','ADZ')">Sim PEI→ADZ</button>
                <button class="btn btn-y" onclick="exportCSV()">Export CSV</button>
                <span style="color:var(--text2);font-size:.875rem">Auto-refresh every 30s</span>
            </div>
            <div class="grid" id="route-cards" style="grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem;margin-bottom:2rem"></div>
            <div class="card"><h3 style="margin-bottom:1rem">Price Comparison</h3>
                <div class="max-h-400"><table><thead><tr><th>#</th><th>Route</th><th>Price</th><th>Airline</th><th>Change</th><th>Updated</th></tr></thead>
                <tbody id="comparison-body"><tr><td colspan="6">Loading...</td></tr></tbody></table></div>
            </div>
        </div>

        <div id="tab-stats" style="display:none">
            <div class="card"><h3 style="margin-bottom:1rem">Price Statistics</h3>
                <table><tbody id="stats-body"></tbody></table>
            </div>
            <div class="card mt1"><h3 style="margin-bottom:1rem">Price History Chart</h3>
                <canvas id="priceChart" class="chart"></canvas>
            </div>
        </div>

        <div id="tab-alerts" style="display:none">
            <div class="card"><h3 style="margin-bottom:1rem">Recent Alerts</h3>
                <table><thead><tr><th>Type</th><th>Route</th><th>Difference</th><th>Time</th></tr></thead>
                <tbody id="alerts-body"><tr><td colspan="4">Loading...</td></tr></tbody></table>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script>
        const API = '/api'; let priceChart = null;

        async function get(path) { try { const r = await fetch(path); return await r.json(); } catch(e) { return null; } }

        async function fetchAll() {
            const [metrics, prices, comp, stats, chartData] = await Promise.all([
                get(API+'/metrics'), get(API+'/prices'), get(API+'/price-comparison'),
                get(API+'/statistics'), get(API+'/price-chart?route=MDE:ADZ&chat_id=8116692870')
            ]);
            if (metrics) {
                document.getElementById('m-flights').textContent = metrics.flights_searched_total||0;
                document.getElementById('m-checks').textContent = metrics.price_checks_total||0;
                document.getElementById('m-alerts').textContent = metrics.price_alerts_sent_total||0;
                document.getElementById('m-rl').textContent = metrics.rate_limit_hits_total||0;
            }
            const rc = document.getElementById('route-cards'); rc.innerHTML = '';
            if (prices && prices.routes) {
                const allUpdates = Object.values(prices.routes).map(r => r.last_update).filter(Boolean).sort().reverse();
                const latest = allUpdates[0] || prices.timestamp;
                document.getElementById('last-api-check').textContent = 'Bot last check: ' + new Date(latest).toLocaleString();
                Object.values(prices.routes).forEach(r => {
                    const lastUpdate = r.last_update ? new Date(r.last_update).toLocaleString() : 'Never';
                    const airline = r.airline || 'N/A';
                    const d = document.createElement('div'); d.className = 'card';
                    d.innerHTML = `<div style="font-size:1.25rem;font-weight:600">${r.origin} &rarr; ${r.destination}</div>
                        <div class="val" style="font-size:2rem;font-weight:700;color:var(--green);margin:.5rem 0">
                        $${Number(r.price).toLocaleString('es-CO')}</div>
                        <div style="color:var(--text2);font-size:.875rem">${airline}</div>
                        <div style="color:var(--text2);font-size:.75rem;margin-top:.5rem">Last update: ${lastUpdate}</div>`;
                    rc.appendChild(d);
                });
                if (Object.values(prices.routes).length === 0) rc.innerHTML = '<p style="color:var(--text2)">No data yet</p>';
            }
            const tb = document.getElementById('comparison-body'); tb.innerHTML = '';
            if (comp && comp.routes) {
                comp.routes.forEach((r, i) => {
                    const cls = i===0?'r1':i===1?'r2':i===2?'r3':'';
                    const badge = i<3 ? `<span class="rk ${cls}">${i+1}</span>` : i+1;
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td>${badge}</td><td>${r.origin}&rarr;${r.destination}</td>
                        <td style="font-weight:600">$${r.current_price?Number(r.current_price).toLocaleString('es-CO'):'N/A'}</td>
                        <td>${r.airline||'N/A'}</td>
                        <td><span class="text-success">-</span></td>
                        <td style="color:var(--text2);font-size:.875rem">${r.last_update?new Date(r.last_update).toLocaleString():'Never'}</td>`;
                    tb.appendChild(tr);
                });
            }
            if (stats) renderStats(stats);
            if (chartData) renderChart(chartData);
        }

        function renderChart(data) {
            const points = (data.points||[]).sort((a,b) => new Date(a.date) - new Date(b.date));
            if (points.length === 0) return;
            const labels = points.map(p => new Date(p.date).toLocaleDateString());
            const values = points.map(p => p.price);
            const airlines = [...new Set(points.map(p => p.airline))].join(', ');
            const canvas = document.getElementById('priceChart');
            if (!canvas) return;
            if (priceChart) { priceChart.destroy(); }
            priceChart = new Chart(canvas, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: data.route + ' (' + airlines + ')',
                        data: values,
                        borderColor: '#22c55e',
                        backgroundColor: 'rgba(34,197,94,0.1)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 4,
                        pointBackgroundColor: '#22c55e',
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#94a3b8' } } },
                    scales: {
                        x: { ticks: { color: '#94a3b8', maxRotation: 45 }, grid: { color: '#334155' } },
                        y: { ticks: { color: '#94a3b8', callback: v => '$' + v.toLocaleString('es-CO') }, grid: { color: '#334155' } }
                    }
                }
            });
        }

        function renderStats(stats) {
            const b = document.getElementById('stats-body');
            b.innerHTML = `
                <tr><td>Routes Tracked</td><td>${stats.total_routes||0}</td></tr>
                <tr><td>Lowest Price</td><td>$${(stats.lowest_price||0).toLocaleString('es-CO')}</td></tr>
                <tr><td>Highest Price</td><td>$${(stats.highest_price||0).toLocaleString('es-CO')}</td></tr>
                <tr><td>Avg Price</td><td>$${(stats.average_price||0).toLocaleString('es-CO')}</td></tr>
                <tr><td>Airlines</td><td>${(stats.airlines&&stats.airlines.join(', '))||'N/A'}</td></tr>
                <tr><td>Flights Searched</td><td>${((stats.metrics_captured||{}).flights_searched)||0}</td></tr>
                <tr><td>Alerts Sent</td><td>${((stats.metrics_captured||{}).alerts_sent)||0}</td></tr>
                <tr><td>DB Records</td><td>${((stats.database||{}).total_price_records)||'N/A'}</td></tr>
            `;

            const ab = document.getElementById('alerts-body');
            ab.innerHTML = '';
            const alerts = (stats.database && stats.database.recent_alerts) || [];
            if (alerts.length === 0) {
                ab.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--text2)">No alerts yet</td></tr>';
            } else {
                alerts.forEach(a => {
                    const tr = document.createElement('tr');
                    const typeClass = a.type === 'price_drop' ? 'text-success' : 'text-danger';
                    const typeLabel = a.type === 'price_drop' ? 'Price Drop' : 'Price Increase';
                    const diffStr = a.diff ? '$' + Number(a.diff).toLocaleString('es-CO') : '-';
                    const timeStr = a.at ? new Date(a.at).toLocaleString() : '-';
                    tr.innerHTML = `<td class="${typeClass}">${typeLabel}</td><td>${a.route}</td><td>${diffStr}</td><td>${timeStr}</td>`;
                    ab.appendChild(tr);
                });
            }
        }

        async function sim(origin, dest) {
            const prices = [120000,150000,180000,200000,250000];
            const airlines = ['Avianca','LATAM','Wingo','JetSMART'];
            const price = prices[Math.floor(Math.random()*prices.length)];
            const airline = airlines[Math.floor(Math.random()*airlines.length)];
            try {
                const r = await fetch(`${API}/simulate-check?origin=${origin}&destination=${dest}&price=${price}&airline=${airline}`,{method:'POST'});
                const d = await r.json();
                if (d.price_drop) alert(`Price drop! Save $${d.price_drop.toLocaleString('es-CO')}`);
                fetchAll();
            } catch(e) { showErr('Simulation failed'); }
        }

        async function exportCSV() { window.open(`${API}/export/csv`, '_blank'); }

        function showErr(m) {
            document.getElementById('err').innerHTML = `<div class="err">${m}</div>`;
            setTimeout(()=>document.getElementById('err').innerHTML='', 5000);
        }

        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('tab-routes').style.display = tab==='routes'?'':'none';
            document.getElementById('tab-stats').style.display = tab==='stats'?'':'none';
            document.getElementById('tab-alerts').style.display = tab==='alerts'?'':'none';
        }

        fetchAll();
        setInterval(fetchAll, 30000);
    </script>
</body>
</html>
"""
