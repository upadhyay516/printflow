import os
import random
import webbrowser
import threading
import time
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, send_from_directory

# --- 1. SETUP ---
app = Flask(__name__)
PORT = 5050  # Changed port to avoid conflicts
UPLOAD_FOLDER = 'uploaded_docs'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
job_queue = []

# --- 2. HTML TEMPLATES ---

HTML_STUDENT = """
<!DOCTYPE html>
<html>
<head>
    <title>PrintFlow Student</title>
    <style>
        body { font-family: sans-serif; background: #f4f6f7; padding: 20px; }
        .box { background: white; max-width: 500px; margin: auto; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; }
        input, select { width: 100%; padding: 10px; margin: 5px 0 15px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box;}
        button { background: #e67e22; color: white; padding: 12px; width: 100%; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        button:hover { background: #d35400; }
        .link { display: block; text-align: center; margin-top: 15px; color: #7f8c8d; text-decoration: none; }
    </style>
</head>
<body>
    <div class="box">
        <h1>PrintFlow Student</h1>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <label><b>Student Name / ID:</b></label>
            <input type="text" name="student_id" placeholder="Enter Name" required>

            <label><b>Select File:</b></label>
            <input type="file" name="file" required>

            <div style="display:flex; gap:10px;">
                <div style="flex:1;">
                    <label><b>Paper Size:</b></label>
                    <select name="paper_size"><option>A4</option><option>A3</option><option>Letter</option></select>
                </div>
                <div style="flex:1;">
                    <label><b>Color:</b></label>
                    <select name="color_mode"><option>Black & White</option><option>Color</option></select>
                </div>
            </div>

            <label><b>Resolution:</b></label>
            <select name="resolution"><option>Standard</option><option>High Quality</option></select>

            <button type="submit">Submit Print Job</button>
        </form>
        <a href="/staff" class="link" target="_blank">➜ Open Staff Dashboard</a>
    </div>
</body>
</html>
"""

HTML_STAFF = """
<!DOCTYPE html>
<html>
<head>
    <title>Staff Dashboard</title>
    <style>
        body { font-family: sans-serif; background: #2c3e50; color: white; padding: 20px; }
        table { width: 100%; background: white; color: #333; border-collapse: collapse; border-radius: 5px; overflow: hidden; }
        th, td { padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }
        th { background: #34495e; color: white; }
        
        /* The Hyperlink Style */
        a.doc-link { color: #2980b9; font-weight: bold; text-decoration: none; }
        a.doc-link:hover { text-decoration: underline; color: #c0392b; }

        .btn { padding: 5px 10px; color: white; border: none; border-radius: 3px; cursor: pointer; }
        .btn-rename { background: #3498db; }
        .btn-reject { background: #e74c3c; }
        input.rename { width: 120px; padding: 3px; }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <h1>Staff Dashboard</h1>
        <a href="/" style="color:white;">Back to Student View</a>
    </div>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Student / Document Link</th>
                <th>Specs</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for job in jobs %}
            <tr>
                <td>#{{ job.id }}</td>
                <td>
                    <b>{{ job.student }}</b><br>
                    {% if job.status != 'Rejected' %}
                        <a href="/files/{{ job.filename }}" class="doc-link" target="_blank">📄 {{ job.filename }}</a>
                    {% else %}
                        <span style="color:#999; text-decoration:line-through;">{{ job.filename }}</span>
                    {% endif %}
                </td>
                <td>{{ job.paper }} | {{ job.color }}</td>
                <td>{{ job.status }}</td>
                <td>
                    {% if job.status == 'Queued' %}
                    <form action="/rename/{{ job.id }}" method="post" style="display:inline;">
                        <input type="text" name="new_name" class="rename" placeholder="New Name">
                        <button class="btn btn-rename">Rename</button>
                    </form>
                    <form action="/reject/{{ job.id }}" method="post" style="display:inline;">
                        <button class="btn btn-reject">Reject</button>
                    </form>
                    {% endif %}
                </td>
            </tr>
            {% else %}
            <tr><td colspan="5" style="text-align:center;">No active jobs.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""

HTML_SUCCESS = """
<div style="text-align:center; font-family:sans-serif; margin-top:50px;">
    <h1 style="color:green;">✅ Sent to Queue!</h1>
    <p>Your Ticket ID: <b>#{{ queue_id }}</b></p>
    <a href="/">Submit Another</a>
</div>
"""

# --- 3. ROUTES ---

@app.route('/')
def home(): return render_template_string(HTML_STUDENT)

@app.route('/staff')
def staff(): return render_template_string(HTML_STAFF, jobs=job_queue)

# Route that actually opens the file
@app.route('/files/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file.filename == '': return "No file selected"
    
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    
    job_id = random.randint(1000, 9999)
    job_queue.insert(0, {
        'id': job_id,
        'student': request.form['student_id'],
        'filename': file.filename,
        'paper': request.form['paper_size'],
        'color': request.form['color_mode'],
        'status': 'Queued'
    })
    return render_template_string(HTML_SUCCESS, queue_id=job_id)

@app.route('/rename/<int:jid>', methods=['POST'])
def rename_file(jid):
    new_name = request.form['new_name']
    for job in job_queue:
        if job['id'] == jid:
            old_path = os.path.join(app.config['UPLOAD_FOLDER'], job['filename'])
            
            # Keep the file extension (e.g., .pdf)
            ext = os.path.splitext(job['filename'])[1]
            if not new_name.endswith(ext): new_name += ext
            
            new_path = os.path.join(app.config['UPLOAD_FOLDER'], new_name)
            
            try:
                os.rename(old_path, new_path)
                job['filename'] = new_name
            except: pass
            break
    return redirect('/staff')

@app.route('/reject/<int:jid>', methods=['POST'])
def reject_job(jid):
    for job in job_queue:
        if job['id'] == jid: job['status'] = 'Rejected'
    return redirect('/staff')

# --- 4. STARTUP SCRIPT ---

def launch_browser():
    # Wait 1.5 seconds to ensure server is ready, then open
    time.sleep(1.5)
    url = f"http://127.0.0.1:{PORT}"
    print(f"\n[SYSTEM] Opening Browser to: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    print("="*40)
    print(f"PRINTFLOW SERVER STARTING ON PORT {PORT}")
    print(f"ACCESS MANUALLY AT: http://127.0.0.1:{PORT}")
    print("="*40)
    
    # Start browser in a background thread
    threading.Thread(target=launch_browser).start()
    
    # use_reloader=False is CRITICAL for IDLE to show output
    app.run(port=PORT, debug=True, use_reloader=False)
