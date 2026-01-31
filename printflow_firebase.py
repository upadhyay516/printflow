import os
import webbrowser
import threading
import time
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, send_from_directory

# ==========================================
# CONFIGURATION
# ==========================================
app = Flask(__name__)
PORT = 5050
UPLOAD_FOLDER = 'uploaded_docs'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
job_queue = []
NEXT_TICKET_ID = 1001

# ==========================================
# FIREBASE PLACEHOLDER
# ==========================================
def sync_to_firebase(job_id, status, student_name):
    # This uses .format() so it works on older Python versions too
    msg = "--- [FIREBASE SYNC] Job #{0} for {1} is now '{2}' ---".format(job_id, student_name, status)
    print(msg)

# ==========================================
# HTML TEMPLATES
# ==========================================

HTML_STUDENT = """
<!DOCTYPE html>
<html>
<head>
    <title>PrintFlow Student</title>
    <meta http-equiv="refresh" content="10"> 
    <style>
        body { font-family: sans-serif; background: #f4f6f7; padding: 20px; }
        .box { background: white; max-width: 500px; margin: auto; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; }
        .status-tracker { background: #ecf0f1; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .status-step { display: flex; align-items: center; margin-bottom: 5px; }
        .dot { height: 10px; width: 10px; background-color: #bdc3c7; border-radius: 50%; display: inline-block; margin-right: 10px; }
        .active-dot { background-color: #27ae60; box-shadow: 0 0 5px #27ae60; }
        input, select { width: 100%; padding: 10px; margin: 5px 0 15px 0; border: 1px solid #bdc3c7; border-radius: 5px; }
        button { background: #e67e22; color: white; padding: 12px; width: 100%; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; }
        button:hover { background: #d35400; }
    </style>
</head>
<body>
    <div class="box">
        <h1>PrintFlow Student</h1>
        
        {% if my_job %}
        <div class="status-tracker">
            <h3>Ticket #{{ my_job.id }} Status:</h3>
            <div class="status-step">
                <span class="dot {% if my_job.status == 'Queued' or my_job.status == 'Printing' or my_job.status == 'Ready' %}active-dot{% endif %}"></span> Queued
            </div>
            <div class="status-step">
                <span class="dot {% if my_job.status == 'Printing' or my_job.status == 'Ready' %}active-dot{% endif %}"></span> Printing
            </div>
            <div class="status-step">
                <span class="dot {% if my_job.status == 'Ready' %}active-dot{% endif %}"></span> Ready for Pickup
            </div>
            <p><b>Current State:</b> <span style="color:#2980b9;">{{ my_job.status }}</span></p>
        </div>
        {% endif %}

        <form action="/upload" method="post" enctype="multipart/form-data">
            <label>Student Name / ID</label>
            <input type="text" name="student_id" placeholder="e.g. Yash (9921103)" required>

            <label>Upload Document</label>
            <input type="file" name="file" required>

            <div style="display:flex; gap:10px;">
                <div style="flex:1;">
                    <label>Paper Size</label>
                    <select name="paper_size"><option>A4</option><option>A3</option><option>Letter</option></select>
                </div>
                <div style="flex:1;">
                    <label>Color Mode</label>
                    <select name="color_mode"><option>Black & White</option><option>Color</option></select>
                </div>
            </div>

            <button type="submit">Upload & Get Queue ID</button>
        </form>
        <br>
        <a href="/staff" target="_blank" style="display:block; text-align:center; color:#7f8c8d;">Open Staff Dashboard</a>
    </div>
</body>
</html>
"""

HTML_STAFF = """
<!DOCTYPE html>
<html>
<head>
    <title>Staff Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: sans-serif; background: #2c3e50; color: white; padding: 20px; }
        table { width: 100%; background: white; color: #333; border-collapse: collapse; border-radius: 8px; overflow: hidden; }
        th, td { padding: 15px; border-bottom: 1px solid #eee; text-align: left; }
        th { background: #34495e; color: white; }
        a.doc-link { color: #2980b9; font-weight: bold; text-decoration: none; }
        .btn { padding: 8px 15px; color: white; border: none; border-radius: 4px; cursor: pointer; margin-right: 5px; font-weight: bold; }
        .btn-accept { background: #3498db; }
        .btn-done { background: #27ae60; } 
        .btn-reject { background: #e74c3c; }
        .badge { padding: 4px 8px; border-radius: 12px; font-size: 11px; text-transform: uppercase; color: white; background: #7f8c8d; }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <h1>Staff Dashboard</h1>
        <a href="/" style="color:white; border:1px solid white; padding:5px 10px; text-decoration:none; border-radius:4px;">Switch to Student View</a>
    </div>

    <table>
        <thead>
            <tr>
                <th>Ticket</th>
                <th>Student / File</th>
                <th>Details</th>
                <th>Status</th>
                <th>Action Flow</th>
            </tr>
        </thead>
        <tbody>
            {% for job in jobs %}
            <tr>
                <td>#{{ job.id }}</td>
                <td>
                    <b>{{ job.student }}</b><br>
                    {% if job.status != 'Rejected' %}
                        <a href="/files/{{ job.filename }}" class="doc-link" target="_blank">File: {{ job.filename }}</a>
                    {% else %}
                        <strike>{{ job.filename }}</strike>
                    {% endif %}
                </td>
                <td>{{ job.paper }} | {{ job.color }}</td>
                <td><span class="badge">{{ job.status }}</span></td>
                <td>
                    {% if job.status == 'Queued' %}
                        <form action="/accept/{{ job.id }}" method="post" style="display:inline;">
                            <button class="btn btn-accept">Accept & Print</button>
                        </form>
                        <form action="/reject/{{ job.id }}" method="post" style="display:inline;">
                            <button class="btn btn-reject">X</button>
                        </form>
                    {% elif job.status == 'Printing' %}
                        <form action="/complete/{{ job.id }}" method="post" style="display:inline;">
                            <button class="btn btn-done">Mark Ready</button>
                        </form>
                    {% elif job.status == 'Ready for Pickup' %}
                        <span style="color: green;">Notification Sent</span>
                    {% endif %}
                </td>
            </tr>
            {% else %}
            <tr><td colspan="5" style="text-align:center; padding:20px;">No jobs yet.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""

# ==========================================
# SERVER ROUTES
# ==========================================

@app.route('/')
def home():
    latest_job = job_queue[0] if job_queue else None
    return render_template_string(HTML_STUDENT, my_job=latest_job)

@app.route('/staff')
def staff():
    return render_template_string(HTML_STAFF, jobs=job_queue)

@app.route('/files/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload', methods=['POST'])
def upload():
    global NEXT_TICKET_ID
    file = request.files['file']
    if file.filename == '': return "No file"
    
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    
    job = {
        'id': NEXT_TICKET_ID,
        'student': request.form['student_id'],
        'filename': file.filename,
        'paper': request.form['paper_size'],
        'color': request.form['color_mode'],
        'status': 'Queued'
    }
    job_queue.insert(0, job)
    NEXT_TICKET_ID += 1
    
    sync_to_firebase(job['id'], 'Queued', job['student'])
    return redirect('/')

@app.route('/accept/<int:jid>', methods=['POST'])
def accept_job(jid):
    for job in job_queue:
        if job['id'] == jid:
            job['status'] = 'Printing'
            sync_to_firebase(jid, 'Printing', job['student'])
            break
    return redirect('/staff')

@app.route('/complete/<int:jid>', methods=['POST'])
def complete_job(jid):
    for job in job_queue:
        if job['id'] == jid:
            job['status'] = 'Ready for Pickup' # This replaces the 'Ready' string
            sync_to_firebase(jid, 'Ready', job['student'])
            break
    return redirect('/staff')

@app.route('/reject/<int:jid>', methods=['POST'])
def reject_job(jid):
    for job in job_queue:
        if job['id'] == jid:
            job['status'] = 'Rejected'
            sync_to_firebase(jid, 'Rejected', job['student'])
            break
    return redirect('/staff')

# ==========================================
# LAUNCHER
# ==========================================
def launch_browser():
    time.sleep(1.5)
    url = "http://127.0.0.1:{0}".format(PORT)
    webbrowser.open(url)

if __name__ == "__main__":
    print("PRINTFLOW SERVER RUNNING ON PORT {0}".format(PORT))
    threading.Thread(target=launch_browser).start()
    app.run(port=PORT, debug=True, use_reloader=False)
