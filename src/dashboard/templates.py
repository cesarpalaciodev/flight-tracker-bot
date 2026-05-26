DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <title>Flight Tracker</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        :root{--bg:#f8fafc;--surface:#fff;--border:#e2e8f0;--text:#0f172a;--text2:#475569;--text3:#94a3b8;--primary:#6366f1;--primary-bg:rgba(99,102,241,.06);--success:#10b981;--success-bg:rgba(16,185,129,.06);--warning:#f59e0b;--danger:#ef4444;--danger-bg:rgba(239,68,68,.06);--shadow:0 1px 3px rgba(0,0,0,.06);--shadow-lg:0 8px 30px rgba(0,0,0,.08);--radius:18px}
        [data-theme=dark]{--bg:#0f1117;--surface:#1a1d27;--border:#2a2e3d;--text:#e8edf5;--text2:#94a3b8;--text3:#5a6378;--primary:#818cf8;--primary-bg:rgba(129,140,248,.08);--success:#34d399;--success-bg:rgba(52,211,153,.08);--warning:#fbbf24;--danger:#f87171;--danger-bg:rgba(248,113,113,.08);--shadow:0 1px 3px rgba(0,0,0,.2);--shadow-lg:0 8px 30px rgba(0,0,0,.3)}
        body{font-family:'Plus Jakarta Sans',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;transition:background .4s,color .4s}

        .bg-grad{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;
            background:radial-gradient(circle at 20% 80%,rgba(99,102,241,.1) 0%,transparent 50%),radial-gradient(circle at 80% 20%,rgba(16,185,129,.06) 0%,transparent 50%),radial-gradient(circle at 50% 50%,rgba(245,158,11,.04) 0%,transparent 50%);
            animation:bgShift 20s ease-in-out infinite alternate}
        @keyframes bgShift{0%{background-position:0 0}100%{background-position:100% 100%}}
        [data-theme=dark] .bg-grad{background:radial-gradient(circle at 20% 80%,rgba(129,140,248,.06) 0%,transparent 50%),radial-gradient(circle at 80% 20%,rgba(52,211,153,.04) 0%,transparent 50%)}

        .content{position:relative;z-index:1}
        .header{background:rgba(255,255,255,.85);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);padding:.875rem 2rem;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:1rem;position:sticky;top:0;z-index:100;transition:background .4s}
        [data-theme=dark] .header{background:rgba(26,29,39,.9)}
        .logo{font-size:1.25rem;font-weight:800;background:linear-gradient(135deg,var(--primary),#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
        .status{display:flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;font-size:.7rem;font-weight:700;background:var(--success-bg);color:var(--success)}
        .status-dot{width:6px;height:6px;border-radius:50%;background:var(--success);box-shadow:0 0 8px rgba(16,185,129,.5);animation:pulse 3s infinite}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
        .theme-btn{cursor:pointer;font-size:.85rem;user-select:none;width:44px;height:24px;border-radius:12px;background:var(--border);position:relative;border:0}
        .theme-btn::after{content:'';position:absolute;top:2px;left:2px;width:18px;height:18px;border-radius:50%;background:var(--primary);transition:transform .3s}
        [data-theme=dark] .theme-btn::after{transform:translateX(20px);background:var(--warning)}
        .logout{cursor:pointer;color:var(--text3);font-weight:600;padding:6px 14px;border-radius:8px;transition:all .2s;font-size:.8rem}
        .logout:hover{background:var(--danger-bg);color:var(--danger)}

        .container{max-width:1300px;margin:0 auto;padding:2rem}
        .stats{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:2rem}
        .stat-card{background:var(--surface);border-radius:var(--radius);padding:1.5rem;border:1px solid var(--border);box-shadow:var(--shadow);transition:transform .3s,box-shadow .3s}
        .stat-card:hover{transform:translateY(-4px);box-shadow:var(--shadow-lg)}
        .stat-label{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--text3);margin-bottom:.5rem}
        .stat-value{font-size:2rem;font-weight:800;font-family:'JetBrains Mono',monospace}
        .stat-card:nth-child(1) .stat-value{color:var(--primary)}
        .stat-card:nth-child(2) .stat-value{color:var(--warning)}
        .stat-card:nth-child(3) .stat-value{color:var(--success)}
        .stat-card:nth-child(4) .stat-value{color:var(--danger)}

        .tabs{display:flex;gap:0;margin-bottom:1.5rem;background:var(--surface);border-radius:14px;padding:4px;box-shadow:var(--shadow);border:1px solid var(--border);width:fit-content}
        .tab{padding:.55rem 1.5rem;border:0;background:none;color:var(--text3);font-family:'Plus Jakarta Sans',sans-serif;font-size:.78rem;font-weight:600;border-radius:11px;cursor:pointer;transition:all .2s}
        .tab:hover{color:var(--text)}
        .tab.active{background:var(--surface);color:var(--primary);box-shadow:var(--shadow)}

        .route-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem;margin-bottom:2rem}
        .route-card{background:var(--surface);border-radius:var(--radius);padding:1.5rem;border:1px solid var(--border);box-shadow:var(--shadow);transition:all .3s}
        .route-card:hover{transform:translateY(-3px);box-shadow:var(--shadow-lg)}
        .route-hdr{display:flex;align-items:center;gap:8px;margin-bottom:.75rem}
        .route-org,.route-dst{font-weight:700;font-size:1rem}
        .route-arr{width:26px;height:26px;border-radius:50%;background:var(--primary-bg);color:var(--primary);display:flex;align-items:center;justify-content:center;font-size:.7rem}
        .route-price{font-size:2rem;font-weight:800;font-family:'JetBrains Mono',monospace;margin:.5rem 0}
        .route-airline{font-size:.75rem;font-weight:600;color:var(--text2);padding:2px 10px;background:var(--primary-bg);border-radius:20px;display:inline-block}

        .panel{background:var(--surface);border-radius:var(--radius);box-shadow:var(--shadow);border:1px solid var(--border);overflow:hidden;margin-bottom:1.5rem}
        .panel-hdr{padding:1rem 1.5rem;font-weight:700;font-size:.83rem;border-bottom:1px solid var(--border)}
        .dot{width:8px;height:8px;border-radius:50%;background:var(--primary);display:inline-block;margin-right:8px}

        table{width:100%;border-collapse:collapse}
        th{padding:.75rem 1.5rem;text-align:left;font-size:.63rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--text3);border-bottom:1px solid var(--border)}
        td{padding:.75rem 1.5rem;border-bottom:1px solid var(--border);font-size:.82rem}
        tr:last-child td{border-bottom:0}

        .btn{background:var(--primary);color:#fff;border:0;padding:.6rem 1.5rem;border-radius:11px;font-family:'Plus Jakarta Sans',sans-serif;font-size:.78rem;font-weight:700;cursor:pointer;transition:all .2s}
        .btn:hover{opacity:.9;transform:translateY(-1px)}
        .btn-outline{background:none;color:var(--text);border:1.5px solid var(--border)}
        .btn-outline:hover{border-color:var(--primary);color:var(--primary);background:var(--primary-bg)}

        .badge{display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:20px;font-size:.68rem;font-weight:700}
        .badge-drop{background:var(--success-bg);color:var(--success)}
        .badge-rise{background:rgba(245,158,11,.1);color:var(--warning)}

        .flex{display:flex;gap:.75rem;flex-wrap:wrap;align-items:center;margin-bottom:1.5rem}
        .chart-wrap{height:350px;padding:1.5rem}
        .max-h-400{max-height:400px;overflow-y:auto}
        .mono{font-family:'JetBrains Mono',monospace}

        #login{display:flex;align-items:center;justify-content:center;min-height:100vh}
        #login .box{width:400px;background:var(--surface);border-radius:24px;padding:2.5rem;box-shadow:var(--shadow-lg);border:1px solid var(--border);text-align:center}
        #login h1{font-size:1.75rem;font-weight:800;background:linear-gradient(135deg,var(--primary),#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.5rem}
        #login p{font-size:.82rem;color:var(--text3);margin-bottom:1.5rem}
        #login input{width:100%;padding:.85rem 1.2rem;border:1.5px solid var(--border);border-radius:12px;font-family:'JetBrains Mono',monospace;font-size:.92rem;outline:0;background:var(--bg);color:var(--text);transition:.2s}
        #login input:focus{border-color:var(--primary);box-shadow:0 0 0 4px var(--primary-bg)}
        #login .btn{width:100%;padding:.85rem;margin-top:1rem;font-size:.83rem}
        #login .hint{margin-top:1.2rem;font-size:.72rem;color:var(--text3)}
        #login .hint code{background:var(--primary-bg);color:var(--primary);padding:2px 8px;border-radius:5px;font-size:.68rem}

        .err{background:var(--danger-bg);border:1px solid var(--danger);color:var(--danger);padding:.7rem 1.2rem;border-radius:10px;font-size:.78rem;font-weight:600;margin-bottom:1rem}
        .err:empty{display:none}

        @media(max-width:768px){.stats{grid-template-columns:repeat(2,1fr)}.route-grid{grid-template-columns:1fr}.container{padding:1rem}}
    </style>
</head>
<body>
    <div class="bg-grad"></div>

    <div id="login" class="content">
        <div class="box">
            <h1>Flight Tracker</h1>
            <p>Enter your Telegram Chat ID to continue</p>
            <input type="text" id="chat-input" placeholder="Chat ID" autocomplete="off" />
            <button class="btn" onclick="doLogin()">Sign In</button>
            <p class="hint">Get your Chat ID from <code>@userinfobot</code> on Telegram</p>
        </div>
    </div>

    <div id="dashboard" class="content" style="display:none">
        <div class="header">
            <div class="logo">FlightTracker</div>
            <div class="status"><span class="status-dot"></span>Live</div>
            <span id="user-label" style="font-size:.75rem;color:var(--text3);font-weight:600"></span>
            <span id="refresh-label" style="font-size:.7rem;color:var(--text3);margin-left:auto;font-family:monospace"></span>
            <button class="theme-btn" onclick="toggleTheme()" title="Toggle theme"></button>
            <span class="logout" onclick="doLogout()">Sign Out</span>
        </div>
        <div class="container">
            <div class="err" id="err-box"></div>
            <div class="stats">
                <div class="stat-card"><div class="stat-label">Flights Scanned</div><div class="stat-value" id="m-flights">0</div></div>
                <div class="stat-card"><div class="stat-label">Price Checks</div><div class="stat-value" id="m-checks">0</div></div>
                <div class="stat-card"><div class="stat-label">Alerts Sent</div><div class="stat-value" id="m-alerts">0</div></div>
                <div class="stat-card"><div class="stat-label">Rate Limits</div><div class="stat-value" id="m-rl">0</div></div>
            </div>
            <div class="tabs">
                <button class="tab active" onclick="switchTab('routes')">Routes</button>
                <button class="tab" onclick="switchTab('stats')">Analytics</button>
                <button class="tab" onclick="switchTab('alerts')">Alert Log</button>
            </div>
            <div id="tab-routes">
                <div class="flex"><button class="btn btn-outline" onclick="doExportCSV()">Export CSV</button><span style="font-size:.75rem;color:var(--text3)">Auto-refresh 30s</span></div>
                <div class="route-grid" id="route-cards"></div>
                <div class="panel"><div class="panel-hdr"><span class="dot"></span>Price Comparison</div><div class="max-h-400"><table><thead><tr><th>Rank</th><th>Route</th><th>Price</th><th>Airline</th><th>Updated</th></tr></thead><tbody id="comparison-body"></tbody></table></div></div>
            </div>
            <div id="tab-stats" style="display:none">
                <div class="panel"><div class="panel-hdr"><span class="dot"></span>Account Details</div><table><tbody id="stats-body"></tbody></table></div>
                <div class="panel"><div class="panel-hdr"><span class="dot"></span>Price History</div><div class="chart-wrap"><canvas id="priceChart"></canvas></div></div>
            </div>
            <div id="tab-alerts" style="display:none">
                <div class="panel"><div class="panel-hdr"><span class="dot"></span>Alert Log</div><table><thead><tr><th>Type</th><th>Route</th><th>Difference</th><th>Time</th></tr></thead><tbody id="alerts-body"></tbody></table></div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script>
        // Theme
        (function(){var t=localStorage.getItem('ft-theme');if(t==='dark')document.documentElement.setAttribute('data-theme','dark')})();
        function toggleTheme(){var c=document.documentElement.getAttribute('data-theme'),n=c==='dark'?'':'dark';document.documentElement.setAttribute('data-theme',n);localStorage.setItem('ft-theme',n)}

        // State
        var API='/api',token='',myChatId='',chart=null;

        function msg(m){var e=document.getElementById('err-box');e.textContent=m||'';setTimeout(function(){e.textContent=''},5000)}

        async function doLogin(){
            var c=document.getElementById('chat-input').value.trim();
            if(!c){msg('Please enter your Chat ID');return}
            try{
                var r=await fetch(API+'/login?chat_id='+c,{method:'POST'}),d=await r.json();
                if(d.error){msg(d.error);return}
                token=d.token;myChatId=c;
                document.getElementById('login').style.display='none';
                document.getElementById('dashboard').style.display='block';
                document.getElementById('user-label').textContent='ID: '+c.slice(-4);
                loadAll();setInterval(loadAll,30000);
            }catch(e){msg('Connection error. Is the server running?')}
        }

        function doLogout(){token='';myChatId='';document.getElementById('login').style.display='flex';document.getElementById('dashboard').style.display='none'}

        async function get(url){
            try{var h={};if(token)h['Authorization']='Bearer '+token;var r=await fetch(url,{headers:h});if(r.status===401){doLogout();return null}return await r.json()}catch(e){return null}
        }

        async function loadAll(){
            if(!myChatId)return;
            var m=get(API+'/metrics'),u=get(API+'/user/'+myChatId),c=get(API+'/price-chart?route=MDE:ADZ&chat_id='+myChatId);
            m=await m;u=await u;c=await c;
            if(m){
                document.getElementById('m-flights').textContent=(m.flights_searched_total||0).toLocaleString();
                document.getElementById('m-checks').textContent=(m.price_checks_total||0).toLocaleString();
                document.getElementById('m-alerts').textContent=(m.price_alerts_sent_total||0).toLocaleString();
                document.getElementById('m-rl').textContent=(m.rate_limit_hits_total||0).toLocaleString();
            }
            if(u){
                var s=u.subscription||{};
                document.getElementById('refresh-label').textContent=(s.plan||'trial').toUpperCase()+' | '+new Date().toLocaleTimeString();
                showRoutes(u);showAlerts(u);showStats(u);
            }
            if(c)showChart(c);
        }

        function showRoutes(d){
            var rc=document.getElementById('route-cards');rc.innerHTML='';
            var cfg=d.config||{};
            var origins=(cfg.origins||'MDE').split(',').map(function(x){return x.trim()});
            var dests=(cfg.destinations||'ADZ').split(',').map(function(x){return x.trim()});
            var prices=d.prices||[];
            origins.forEach(function(o){dests.forEach(function(dest){
                var m=prices.find(function(p){return p.origin===o&&p.destination===dest});
                var price=m?'$'+Number(m.price).toLocaleString('es-CO'):'---';
                var el=document.createElement('div');el.className='route-card';
                el.innerHTML='<div class="route-hdr"><span class="route-org">'+o+'</span><span class="route-arr">&#8594;</span><span class="route-dst">'+dest+'</span></div><div class="route-price">'+price+'</div><div class="route-airline">'+(m?(m.airline||'---'):'---')+'</div>';
                rc.appendChild(el);
            })});
        }

        function showAlerts(d){
            var ab=document.getElementById('alerts-body');ab.innerHTML='';
            var a=d.recent_alerts||[];
            if(a.length===0){ab.innerHTML='<tr><td colspan="4" style="text-align:center;padding:3rem;color:var(--text3)">No alerts yet</td></tr>';return}
            a.forEach(function(x){
                var tr=document.createElement('tr');
                var cls=x.type==='price_drop'?'badge-drop':'badge-rise';
                var lbl=x.type==='price_drop'?'DROP':'RISE';
                tr.innerHTML='<td><span class="badge '+cls+'">'+lbl+'</span></td><td style="font-weight:600">'+x.route+'</td><td class="mono" style="font-weight:700">$'+Number(x.diff||0).toLocaleString('es-CO')+'</td><td style="font-size:.78rem;color:var(--text3)">'+new Date(x.time).toLocaleString()+'</td>';
                ab.appendChild(tr);
            });
        }

        function showStats(d){
            var b=document.getElementById('stats-body'),s=d.subscription||{},c=d.config||{};
            var rows=[['Plan',(s.plan||'trial').toUpperCase()],['Status',(s.status||'active').toUpperCase()],['API Usage',(s.api_used||0)+' / '+(s.api_limit||10)],['Origins',c.origins||'N/A'],['Destinations',c.destinations||'N/A'],['Passengers',c.adults||'N/A'],['Luggage',c.luggage||'N/A'],['Budget',c.max_budget?'$'+Number(c.max_budget).toLocaleString('es-CO'):'No limit']];
            b.innerHTML=rows.map(function(r){return '<tr><td style="font-weight:600;color:var(--text2)">'+r[0]+'</td><td>'+r[1]+'</td></tr>'}).join('');
        }

        function showChart(d){
            var pts=(d.points||[]).sort(function(a,b){return new Date(a.date)-new Date(b.date)});
            if(!pts.length)return;
            var canvas=document.getElementById('priceChart');if(!canvas)return;
            if(chart)chart.destroy();
            var ctx=canvas.getContext('2d'),grad=ctx.createLinearGradient(0,0,0,350);
            grad.addColorStop(0,'rgba(99,102,241,.18)');grad.addColorStop(1,'rgba(99,102,241,0)');
            chart=new Chart(canvas,{type:'line',data:{labels:pts.map(function(p){return new Date(p.date).toLocaleDateString()}),datasets:[{label:d.route,data:pts.map(function(p){return p.price}),borderColor:'#6366f1',backgroundColor:grad,borderWidth:2.5,fill:true,tension:.3,pointRadius:5,pointBackgroundColor:'#fff',pointBorderColor:'#6366f1',pointBorderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,animation:{duration:1200},plugins:{legend:{labels:{usePointStyle:true,padding:20,font:{family:'Plus Jakarta Sans',size:12,weight:'bold'},color:'#64748b'}}},scales:{x:{ticks:{font:{family:'JetBrains Mono',size:10},color:'#94a3b8'},grid:{color:getComputedStyle(document.documentElement).getPropertyValue('--border').trim()||'#e2e8f0'}},y:{ticks:{font:{family:'JetBrains Mono',size:10},color:'#94a3b8',callback:function(v){return'$'+v.toLocaleString('es-CO')}},grid:{color:getComputedStyle(document.documentElement).getPropertyValue('--border').trim()||'#e2e8f0'}}},interaction:{intersect:false,mode:'index'}}});
        }

        function doExportCSV(){window.open(API+'/export/csv','_blank')}

        function switchTab(tab){
            document.querySelectorAll('.tab').forEach(function(t){t.classList.remove('active')});
            var btns=document.querySelectorAll('.tab');for(var i=0;i<btns.length;i++){if(btns[i].textContent.toLowerCase().indexOf(tab)!==-1||(btns[i].getAttribute('onclick')||'').indexOf(tab)!==-1)btns[i].classList.add('active')}
            document.getElementById('tab-routes').style.display=tab==='routes'?'':'none';
            document.getElementById('tab-stats').style.display=tab==='stats'?'':'none';
            document.getElementById('tab-alerts').style.display=tab==='alerts'?'':'none';
        }
    </script>
</body>
</html>
"""