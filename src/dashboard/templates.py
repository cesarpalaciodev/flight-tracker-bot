DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flight Tracker Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #3b82f6;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }
        
        .header {
            background: var(--bg-secondary);
            padding: 1rem 2rem;
            border-bottom: 1px solid var(--bg-card);
        }
        
        .header h1 {
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .status-badge {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--success);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--bg-card);
        }
        
        .stat-card .label {
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }
        
        .stat-card .value {
            font-size: 2rem;
            font-weight: 700;
        }
        
        .routes-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .route-card {
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--bg-card);
        }
        
        .route-card h3 {
            font-size: 1.25rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .route-card .price {
            font-size: 2rem;
            font-weight: 700;
            color: var(--success);
        }
        
        .route-card .airline {
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-top: 0.5rem;
        }
        
        .route-card .last-update {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 0.5rem;
        }
        
        .price-comparison {
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--bg-card);
            overflow-x: auto;
        }
        
        .price-comparison h2 {
            margin-bottom: 1rem;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--bg-card);
        }
        
        th {
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 0.875rem;
        }
        
        .rank-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
        }
        
        .rank-1 { background: #fbbf24; color: #000; }
        .rank-2 { background: #94a3b8; color: #000; }
        .rank-3 { background: #cd7f32; color: #000; }
        
        .controls {
            margin-bottom: 2rem;
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }
        
        .btn {
            background: var(--accent);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            transition: background 0.2s;
        }
        
        .btn:hover { background: #2563eb; }
        
        .btn-danger { background: var(--danger); }
        .btn-danger:hover { background: #dc2626; }
        
        .btn-success { background: var(--success); }
        .btn-success:hover { background: #16a34a; }
        
        .refresh-indicator {
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-left: auto;
        }
        
        .error-msg {
            background: var(--danger);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>
            <span class="status-badge"></span>
            Flight Tracker Dashboard
        </h1>
    </div>
    
    <div class="container">
        <div id="error-container"></div>
        
        <div class="stats-grid" id="stats-grid">
            <div class="stat-card">
                <div class="label">Flights Searched</div>
                <div class="value" id="flights-searched">-</div>
            </div>
            <div class="stat-card">
                <div class="label">Price Checks</div>
                <div class="value" id="price-checks">-</div>
            </div>
            <div class="stat-card">
                <div class="label">Alerts Sent</div>
                <div class="value" id="alerts-sent">-</div>
            </div>
            <div class="stat-card">
                <div class="label">Rate Limit Hits</div>
                <div class="value" id="rate-limits">-</div>
            </div>
        </div>
        
        <div class="routes-section" id="routes-section">
            <div class="route-card">
                <h3>Loading routes...</h3>
            </div>
        </div>
        
        <div class="price-comparison">
            <h2>Price Comparison</h2>
            <div class="controls">
                <button class="btn btn-success" onclick="simulateCheck('MDE')">Simulate MDE Check</button>
                <button class="btn btn-success" onclick="simulateCheck('PEI')">Simulate PEI Check</button>
                <span class="refresh-indicator" id="refresh-indicator"></span>
            </div>
            <table id="comparison-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Route</th>
                        <th>Current Price</th>
                        <th>Airline</th>
                        <th>Last Update</th>
                    </tr>
                </thead>
                <tbody id="comparison-body">
                    <tr><td colspan="5">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        const API_BASE = '/api';
        
        async function fetchMetrics() {
            try {
                const res = await fetch(`${API_BASE}/metrics`);
                const data = await res.json();
                
                document.getElementById('flights-searched').textContent = data.flights_searched_total || 0;
                document.getElementById('price-checks').textContent = data.price_checks_total || 0;
                document.getElementById('alerts-sent').textContent = data.price_alerts_sent_total || 0;
                document.getElementById('rate-limits').textContent = data.rate_limit_hits_total || 0;
            } catch (e) {
                console.error('Failed to fetch metrics:', e);
            }
        }
        
        async function fetchPrices() {
            try {
                const res = await fetch(`${API_BASE}/prices`);
                const data = await res.json();
                
                const routesSection = document.getElementById('routes-section');
                routesSection.innerHTML = '';
                
                const routes = Object.values(data.routes || {});
                routes.forEach(route => {
                    const card = document.createElement('div');
                    card.className = 'route-card';
                    card.innerHTML = `
                        <h3>${route.origin} → ${route.destination}</h3>
                        <div class="price">$${Number(route.price).toLocaleString('es-CO')} ${route.currency}</div>
                        <div class="airline">${route.airline || 'N/A'}</div>
                        <div class="last-update">${data.timestamp}</div>
                    `;
                    routesSection.appendChild(card);
                });
                
                if (routes.length === 0) {
                    routesSection.innerHTML = '<p style="color: var(--text-secondary)">No price data yet. Run a check to populate.</p>';
                }
            } catch (e) {
                console.error('Failed to fetch prices:', e);
            }
        }
        
        async function fetchComparison() {
            try {
                const res = await fetch(`${API_BASE}/price-comparison`);
                const data = await res.json();
                
                const tbody = document.getElementById('comparison-body');
                tbody.innerHTML = '';
                
                const routes = data.routes || [];
                routes.forEach((route, index) => {
                    const rankClass = index === 0 ? 'rank-1' : index === 1 ? 'rank-2' : index === 2 ? 'rank-3' : '';
                    const rankBadge = index < 3 ? `<span class="rank-badge ${rankClass}">${index + 1}</span>` : index + 1;
                    
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${rankBadge}</td>
                        <td>${route.origin} → ${route.destination}</td>
                        <td>$${Number(route.current_price).toLocaleString('es-CO') || 'N/A'}</td>
                        <td>${route.airline || 'N/A'}</td>
                        <td>${route.last_update || 'Never'}</td>
                    `;
                    tbody.appendChild(row);
                });
                
                if (routes.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-secondary)">No data available</td></tr>';
                }
            } catch (e) {
                console.error('Failed to fetch comparison:', e);
            }
        }
        
        async function simulateCheck(origin) {
            const prices = [150000, 200000, 180000, 220000, 170000];
            const airlines = ['Avianca', 'LATAM', 'Wingo', 'Viva Air', 'JetSMART'];
            
            const price = prices[Math.floor(Math.random() * prices.length)];
            const airline = airlines[Math.floor(Math.random() * airlines.length)];
            
            try {
                const res = await fetch(`${API_BASE}/simulate-check?origin=${origin}&price=${price}&airline=${airline}`, {
                    method: 'POST'
                });
                const data = await res.json();
                
                if (data.price_drop_from_previous) {
                    alert(`Price drop detected! Save $${data.price_drop_from_previous.toLocaleString('es-CO')}`);
                }
                
                await refreshAll();
            } catch (e) {
                showError('Failed to simulate check');
            }
        }
        
        function showError(msg) {
            const container = document.getElementById('error-container');
            container.innerHTML = `<div class="error-msg">${msg}</div>`;
            setTimeout(() => container.innerHTML = '', 5000);
        }
        
        async function refreshAll() {
            await Promise.all([fetchMetrics(), fetchPrices(), fetchComparison()]);
            document.getElementById('refresh-indicator').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
        }
        
        refreshAll();
        setInterval(refreshAll, 30000);
    </script>
</body>
</html>
"""