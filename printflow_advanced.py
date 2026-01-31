from flask import Flask, request, render_template_string, redirect, url_for
import random
import os
import webbrowser
from threading import Timer
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURATION ---
PORT = 9999
UPLOAD_FOLDER = 'uploaded_docs'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- IN-MEMORY DATABASE ---
# Stores all jobs with their settings
job_queue = []

# --- FRONTEND: STUDENT INTERFACE (HTML) ---
HTML_STUDENT = """
<!DOCTYPE html>
<html>
<head>
    <title>PrintFlow - Student</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #f4f6f7; padding: 20px; }
        .container { background: white; max-width: 500px; margin: auto; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; }
        label { font-weight: bold; display: block; margin-top: 15px; color: #34495e; }
        input, select { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #bdc3c7; border-radius: 6px; box-sizing: border-box; }
        .radio-group { display: flex; gap: 15px; margin-top: 5px; }
        .radio-group label { font-weight: normal; margin-top: 0; }
        button { background-color: #e67e22; color: white; border: none; padding: 12px; width: 100%; margin-top: 25px; border-radius: 6px; font-size: 16px; cursor: pointer; transition: 0.3s; }
        button:hover { background-color: #d35400; }
        .link { text-align: center; display: block; margin-top: 20px; color: #7f8c8d; text-decoration: none; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>PrintFlow Student</h1>
        <p style="text-align: center; color: #7f8c8d;">Upload your file and customize settings.</p>
        
        <form action="/upload" method="post" enctype="multipart/form-data">
            
            <label>Student Name / ID:</label>
            <input type="text" name="student_id" placeholder="e.g. John Doe (9921103)" required>

            <label>Select Document:</label>
            <input type="file" name="file" required>

            <div style="display: flex; gap: 20px;">
                <div style="flex: 1;">
                    <label>Paper Size:</label>
                    <select name="paper_size">
                        <option value="A4">A4 (Standard)</option>
                        <option value="A3">A3 (Large)</option>
                        <option value="Letter">Letter</option>
                    </select>
                </div>
                <div style="flex: 1;">
                    <label>Orientation:</label>
                    <select name="orientation">
                        <option value="Portrait">Portrait</option>
                        <option value="Landscape">Landscape</option>
                    </select>
                </div>
            </div>

            <label>Color Mode:</label>
            <div class="radio-group">
                <label><input type="radio" name="color_mode" value="Black & White" checked> Black & White</label>
                <label><input type="radio" name="color_mode" value="  Color"> Color</label>
            </div>

            <label>Print Quality (Resolution):</label>
            <select name="resolution">
                <option value="Standard">Standard (300 DPI) - Fast</option>
                <option value="High">High (600 DPI) - Slower</option>
                <option value="Draft">Draft (150 DPI) - Cheapest</option>
            </select>

            <button type="submit">Submit Print Job</button>
        </form>
        <a href="/staff" class="link">Go to Staff Dashboard (Demo Link)</a>
    </div>
</body>
</html>
"""

# --- FRONTEND: STAFF INTERFACE (HTML) ---
HTML_STAFF = """
<!DOCTYPE html>
<html>
<head>
    <title>PrintFlow - Staff Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #2c3e50; padding: 20px; color: white; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; background: white; color: #333; border-radius: 8px; overflow: hidden; }
        th, td { padding: 15px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #34495e; color: white; }
        tr:hover { background-color: #f1f1f1; }
        
        .badge { padding: 5px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .badge-queued { background: #f1c40f; color: #fff; }
        .badge-rejected { background: #e74c3c; color: white; }
        .badge-ready { background: #27ae60; color: white; }

        .action-btn { padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; color: white; font-size: 12px; margin-right: 5px; }
        .btn-reject { background-color: #c0392b; }
        .btn-rename { background-color: #2980b9; }
        
        input.rename-box { padding: 5px; border: 1px solid #ccc; border-radius: 3px; width: 150px; }
        .nav-link { color: #ecf0f1; text-decoration: none; border: 1px solid #ecf0f1; padding: 8px 15px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🖨️ Staff Dashboard</h1>
        <a href="/" class="nav-link">Switch to Student View</a>
    </div>

    <table>
        <thead>
            <tr>
                <th>Queue ID</th>
                <th>Student / File</th>
                <th>Settings</th>
                <th>Status</th>
                <th>Actions (Rename / Reject)</th>
            </tr>
        </thead>
        <tbody>
            {% for job in jobs %}
            <tr>
                <td><strong>#{{ job.id }}</strong></td>
                <td>
                    <div style="font-weight:bold;">{{ job.student }}</div>
                    <div style="color: #7f8c8d; font-size: 13px;">{{ job.filename }}</div>
                </td>
                <td style="font-size: 13px;">
                    {{ job.paper }} | {{ job.orientation }}<br>
                    {{ job.color }} | {{ job.resolution }}
                </td>
                <td>
                    <span class="badge badge-{{ job.status|lower }}">{{ job.status }}</span>
                </td>
                <td>
                    {% if job.status == 'Queued' %}
                    <form action="/staff/rename/{{ job.id }}" method="post" style="display:inline-block; margin-bottom: 5px;">
                        <input type="text" name="new_name" class="rename-box" placeholder="Rename (e.g. ID_Name)" required>
                        <button type="submit" class="action-btn btn-rename">Rename</button>
                    </form>
                    
                    <form action="/staff/reject/{{ job.id }}" method="post" style="display:inline-block;">
                        <button type="submit" class="action-btn btn-reject">Reject</button>
                    </form>
                    {% else %}
                        No actions available
                    {% endif %}
                </td>
            </tr>
            {% else %}
            <tr><td colspan="5" style="text-align:center; padding: 20px;">No active print jobs.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""

HTML_SUCCESS = """
<!DOCTYPE html>
<html>
<body style="font-family: sans-serif; text-align: center; padding: 50px;">
    <h1 style="color: #27ae60;">Upload Successful!</h1>
    <p>Your Queue ID is: <b>#{{ queue_id }}</b></p>
    <p>Waiting for Staff approval.</p>
    <a href="/">Back to Home</a>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/')
def student_interface():
    return render_template_string(HTML_STUDENT)

@app.route('/staff')
def staff_interface():
    return render_template_string(HTML_STAFF, jobs=job_queue)

@app.route('/upload', methods=['POST'])
def handle_upload():
    if 'file' not in request.files: return "No file"
    file = request.files['file']
    if file.filename == '': return "No filename"

    # Save physical file
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

    # Create Job Object with all the new features
    new_job = {
        'id': random.randint(1000, 9999),
        'student': request.form['student_id'],
        'filename': file.filename,
        'paper': request.form['paper_size'],      # A4/A3/Letter
        'orientation': request.form['orientation'], # Portrait/Landscape
        'color': request.form['color_mode'],      # Color/BW
        'resolution': request.form['resolution'], # DPI settings
        'status': 'Queued',
        'timestamp': datetime.now()
    }
    
    # Insert at top of list so newest is first
    job_queue.insert(0, new_job) 
    
    return render_template_string(HTML_SUCCESS, queue_id=new_job['id'])

@app.route('/staff/rename/<int:job_id>', methods=['POST'])
def staff_rename(job_id):
    new_name = request.form['new_name']
    
    for job in job_queue:
        if job['id'] == job_id:
            # Rename the logical file name (Staff feature: Segregate by ID)
            # We append the original extension to keep it valid
            ext = os.path.splitext(job['filename'])[1]
            if not new_name.endswith(ext):
                new_name += ext
            
            job['filename'] = new_name
            break
            
    return redirect('/staff')   

@app.route('/staff/reject/<int:job_id>', methods=['POST'])
def staff_reject(job_id):
    for job in job_queue:
        if job['id'] == job_id:
            job['status'] = 'Rejected' # Staff feature: Reject request
            break
    return redirect('/staff')

# --- RUNNER ---
def open_browser():
    webbrowser.open_new(f"http://127.0.0.1:{PORT}")

if __name__ == '__main__':
    print(f">>> PrintFlow Interfaces Running on Port {PORT}")
    Timer(1, open_browser).start()
    app.run(port=PORT)
