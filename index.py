import os, time, PyPDF2
from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify
from supabase import create_client

app = Flask(__name__)
app.secret_key = "JIIT_FINAL_ULTIMATE_2026"

# --- CONFIGURATION ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lxbqnmovxirkfcsdaaan.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4YnFubW92eGlya2Zjc2RhYWFuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5NjQ2OTIsImV4cCI6MjA4NTU0MDY5Mn0.5znjA4dhlhn7b65sJLKAfujNdnS_STPT_AS4pTNEGts")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- PDF PROCESSING ---
def process_pdf_and_count(input_path, output_path, range_str):
    try:
        reader = PyPDF2.PdfReader(input_path)
        total_pages = len(reader.pages)
        if not range_str or range_str.lower() == 'all' or range_str.strip() == "":
            return total_pages, input_path
        writer = PyPDF2.PdfWriter()
        selected_indices = []
        parts = range_str.replace(" ", "").split(',')
        for part in parts:
            if '-' in part:
                start, end = map(int, part.split('-'))
                selected_indices.extend(range(start - 1, end))
            else:
                selected_indices.append(int(part) - 1)
        for idx in sorted(list(set(selected_indices))):
            if 0 <= idx < total_pages: writer.add_page(reader.pages[idx])
        if len(writer.pages) == 0: return total_pages, input_path
        with open(output_path, "wb") as f: writer.write(f)
        return len(writer.pages), output_path
    except: return 0, input_path

# --- FULL UI TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PrintFlow Pro | JIIT</title>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root { --sidebar: #0f172a; --primary: #2563eb; --accent: #f59e0b; --bg: #f8fafc; --sidebar-width: 260px; }
        body { font-family: 'Plus Jakarta Sans', sans-serif; background: var(--bg); margin: 0; display: flex; min-height: 100vh; }
        
        .sidebar { width: var(--sidebar-width); background: var(--sidebar); height: 100vh; color: white; padding: 2rem 1.5rem; position: fixed; left: 0; top: 0; z-index: 1000; box-sizing: border-box; }
        .logo { font-weight: 800; font-size: 1.5rem; margin-bottom: 2.5rem; display: flex; align-items: center; gap: 10px; }
        .logo span { color: var(--primary); }
        .nav-item { display: flex; align-items: center; gap: 12px; padding: 12px; color: #94a3b8; text-decoration: none; border-radius: 8px; transition: 0.3s; margin-bottom: 10px; }
        .nav-item:hover, .nav-item.active { background: #1e293b; color: white; }

        .main { margin-left: var(--sidebar-width); padding: 2.5rem; width: calc(100% - var(--sidebar-width)); box-sizing: border-box; min-height: 100vh; }
        .card { background: white; border-radius: 16px; border: 1px solid #e2e8f0; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 1.5rem; }
        .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem; }
        
        input, select, button { width: 100%; padding: 12px; margin: 8px 0; border-radius: 8px; border: 1px solid #e2e8f0; box-sizing: border-box; font-family: inherit; }
        .btn-primary { background: var(--primary); color: white; border: none; font-weight: 700; cursor: pointer; transition: 0.2s; }
        .btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }
        
        .badge { padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; }
        .Queued { background: #f1f5f9; color: #475569; }
        .Printing { background: #fef3c7; color: #92400e; }
        .Ready { background: #dcfce7; color: #166534; }

        #pay-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(5px); z-index: 2000; align-items: center; justify-content: center; }
        .modal-card { background: white; padding: 2rem; border-radius: 24px; width: 350px; text-align: center; }
        table { width: 100%; border-collapse: collapse; }
        th { text-align: left; padding: 12px 0; color: #64748b; font-size: 0.85rem; }
        td { padding: 12px 0; border-top: 1px solid #f1f5f9; }
    </style>
</head>
<body>
    {% if not session.get('user_id') %}
    <div style="width:100%; height:100vh; display:flex; align-items:center; justify-content:center; background:var(--sidebar);">
        <div class="card" style="width:380px; text-align:center; padding: 3rem;">
            <div class="logo" style="justify-content:center; color:black;">PRINT<span>FLOW</span></div>
            <form action="/auth" method="POST">
                <input type="email" name="email" placeholder="JIIT Email" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit" name="action" value="login" class="btn-primary">Sign In</button>
                <button type="submit" name="action" value="signup" style="background:none; border:none; color:#2563eb; cursor:pointer; font-weight:600; margin-top:10px;">Create Account</button>
            </form>
        </div>
    </div>
    {% else %}
    <div class="sidebar">
        <div class="logo">PRINT<span>FLOW</span></div>
        <a href="/" class="nav-item {{ 'active' if active_page == 'dashboard' else '' }}"><i data-lucide="layout-dashboard"></i> Dashboard</a>
        <a href="/my-orders" class="nav-item {{ 'active' if active_page == 'orders' else '' }}"><i data-lucide="printer"></i> My Orders</a>
        <a href="/logout" class="nav-item" style="position:absolute; bottom:2rem; width:210px; color: #f87171;"><i data-lucide="log-out"></i> Logout</a>
    </div>

    <div class="main">
        <div style="margin-bottom:2.5rem;">
            <h1 style="margin:0; font-size:1.75rem;">JIIT Smart Printing</h1>
            <p style="margin: 4px 0 0 0; color: #64748b;">Logged in as: <strong>{{ session['email'] }}</strong></p>
        </div>

        {% if session['role'] == 'student' %}
            {% if active_page == 'dashboard' %}
            <div class="stats">
                <div class="card"><small style="color:#64748b; font-weight:700;">QUEUE POSITION</small><div id="q-pos" style="font-size:1.8rem; font-weight:800; margin-top:5px;">#--</div></div>
                <div class="card"><small style="color:#64748b; font-weight:700;">EST. WAIT TIME</small><div style="font-size:1.8rem; font-weight:800; margin-top:5px; color: var(--accent);">~5 Mins</div></div>
            </div>
            <div class="card">
                <h3 style="margin-top:0;"><i data-lucide="upload-cloud"></i> Upload New Document</h3>
                <form id="print-form" action="/upload" method="POST" enctype="multipart/form-data">
                    <label style="font-size:0.85rem; font-weight:700; color:#475569;">SELECT PDF FILE</label>
                    <input type="file" name="file" accept=".pdf" required id="f-pdf">
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px;">
                        <div><label style="font-size:0.85rem; font-weight:700;">PAGE RANGE</label><input type="text" name="range" placeholder="e.g. 1-5"></div>
                        <div><label style="font-size:0.85rem; font-weight:700;">COLOR MODE</label><select name="color_mode" id="c-mode"><option value="B/W">B&W (₹2/pg)</option><option value="Color">Color (₹10/pg)</option></select></div>
                    </div>
                    <button type="button" onclick="openPayment()" class="btn-primary" style="margin-top:1rem; padding: 15px;">Continue to Payment</button>
                </form>
            </div>
            {% elif active_page == 'orders' %}
            <div class="card">
                <h3 style="margin-top:0;"><i data-lucide="history"></i> My Order Status</h3>
                <div id="queue-list"><p style="color:gray;">Syncing with server...</p></div>
            </div>
            {% endif %}
        {% else %}
        <div class="card">
            <h3>Admin Print Queue</h3>
            <table>
                <thead><tr><th>STUDENT</th><th>CONFIG</th><th>PAGES</th><th>STATUS</th><th>ACTIONS</th></tr></thead>
                <tbody>
                    {% for j in jobs %}
                    <tr>
                        <td><strong>{{ j.student_email.split('@')[0] }}</strong></td>
                        <td>{{ j.color_mode }} <small>({{ j.selected_range }})</small></td>
                        <td>{{ j.page_count }}</td>
                        <td><span class="badge {{j.status}}">{{ j.status }}</span></td>
                        <td><a href="{{ j.file_url }}" target="_blank">VIEW</a> | <a href="/update/{{ j.id }}/Printing">PRINT</a> | <a href="/update/{{ j.id }}/Ready">DONE</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
    </div>

    <div id="pay-overlay"><div class="modal-card">
        <h3>Mock Payment</h3>
        <img src="https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=upi://pay?pa=jiit@upi" style="margin:1rem 0;">
        <div style="background:#f8fafc; padding:15px; border-radius:12px; margin-bottom:1.5rem;">
            <span style="font-size:1.75rem; font-weight:800; color:var(--primary);" id="m-price">₹0.00</span>
        </div>
        <button onclick="mockSuccess()" id="m-btn" class="btn-primary" style="padding:15px;">Verify Payment</button>
    </div></div>

    <script>
        lucide.createIcons();
        function openPayment() {
            if(!document.getElementById('f-pdf').files[0]) return alert("Select a PDF!");
            document.getElementById('m-price').innerText = (document.getElementById('c-mode').value === 'Color' ? '₹20.00' : '₹4.00');
            document.getElementById('pay-overlay').style.display = 'flex';
        }
        function mockSuccess() {
            document.getElementById('m-btn').innerText = "Verifying...";
            setTimeout(() => { document.getElementById('print-form').submit(); }, 1200);
        }
        async function sync() {
            try {
                const r = await fetch('/api/queue'); const jobs = await r.json();
                let html = ''; let pos = 0; let myPos = '--'; const email = "{{ session['email'] }}";
                jobs.forEach(j => {
                    if(j.status === 'Queued') pos++;
                    if(j.student_email === email) {
                        if(j.status === 'Queued') myPos = '#'+pos;
                        html += `<div style="padding:15px 0; border-bottom:1px solid #f1f5f9; display:flex; justify-content:space-between; align-items:center;">
                            <div><strong>#${j.id}</strong><div style="font-size:0.75rem; color:gray;">${j.color_mode} • ${j.page_count} Pages</div></div>
                            <span class="badge ${j.status}">${j.status}</span>
                        </div>`;
                    }
                });
                if(document.getElementById('queue-list')) document.getElementById('queue-list').innerHTML = html || 'No orders yet.';
                if(document.getElementById('q-pos')) document.getElementById('q-pos').innerText = myPos;
            } catch(e) {}
        }
        setInterval(sync, 4000); sync();
    </script>
    {% endif %}
</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
def index():
    jobs = []
    if session.get('role') == 'staff':
        jobs = supabase.table('print_jobs').select("*").neq("status", "Completed").order('created_at', desc=True).execute().data
    return render_template_string(HTML_TEMPLATE, jobs=jobs, active_page="dashboard")

@app.route('/my-orders')
def my_orders():
    if not session.get('user_id'): return redirect('/')
    return render_template_string(HTML_TEMPLATE, active_page="orders")

@app.route('/auth', methods=['POST'])
def auth():
    email, pwd, action = request.form['email'], request.form['password'], request.form['action']
    try:
        res = supabase.auth.sign_up({"email": email, "password": pwd}) if action == "signup" else supabase.auth.sign_in_with_password({"email": email, "password": pwd})
        role = 'staff' if email == 'staff@jiit.ac.in' else 'student'
        session.update({'user_id': str(res.user.id), 'email': email, 'role': role})
        return redirect('/')
    except Exception as e: return f"Auth Error: {e}"

@app.route('/upload', methods=['POST'])
def upload():
    temp_dir = "/tmp" if os.name != 'nt' else "temp"
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)
    file = request.files['file']
    t_stamp = int(time.time())
    local_raw = os.path.join(temp_dir, f"raw_{t_stamp}.pdf")
    local_final = os.path.join(temp_dir, f"final_{t_stamp}.pdf")
    file.save(local_raw)
    count, final_path = process_pdf_and_count(local_raw, local_final, request.form.get('range', 'All'))
    storage_name = f"{t_stamp}_{file.filename}"
    with open(final_path, 'rb') as f:
        supabase.storage.from_('print-files').upload(storage_name, f)
    url = supabase.storage.from_('print-files').get_public_url(storage_name)
    supabase.table('print_jobs').insert({
        "student_email": session['email'], "file_url": url, "page_count": count,
        "selected_range": request.form.get('range', 'All'), "color_mode": request.form.get('color_mode'), "status": "Queued"
    }).execute()
    os.remove(local_raw)
    if os.path.exists(local_final) and local_final != local_raw: os.remove(local_final)
    return redirect('/my-orders')

@app.route('/api/queue')
def get_queue():
    res = supabase.table('print_jobs').select("*").order('created_at', desc=False).execute()
    return jsonify(res.data)

@app.route('/update/<int:job_id>/<status>')
def update_status(job_id, status):
    if session.get('role') == 'staff': supabase.table('print_jobs').update({"status": status}).eq("id", job_id).execute()
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear(); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)