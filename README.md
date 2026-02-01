PrintFlow Prototype
PrintFlow is a lightweight, Flask-based web application designed to manage document printing queues between students and staff. It features a real-time status tracker for students and a management dashboard for staff to handle print requests.

## Features
Student Interface: Allows students to upload documents, specify paper size (A4, A3, Letter), and choose color modes (B&W or Color).

Live Status Tracking: Students can see if their job is "Queued," "Printing," or "Ready for Pickup" through an automated progress bar.

Smart Refresh: The student page automatically reloads every 10 seconds to update job status, but intelligently pauses if the user is currently typing in the form to prevent data loss.

Staff Dashboard: A dedicated view for staff to view the queue, download/open uploaded files, and update job statuses or reject requests.

Automatic Setup: Automatically creates the necessary storage folders and launches your default web browser upon startup.

## Technical Specifications
Backend: Python with the Flask web framework.

Frontend: HTML5, CSS3, and JavaScript (embedded in Python strings).

Storage: Local file system (uploaded documents are stored in the uploaded_docs directory).

Concurrency: Uses Python threading to run the server and the browser launcher simultaneously.

## Installation and Usage
Prerequisites: Ensure you have Python installed. You will need the Flask library:

Bash
pip install flask
Running the App: Execute the script directly:

Bash
python printflow.py
Accessing the App:

The Student View will automatically open at http://127.0.0.1:5050.

The Staff Dashboard can be accessed via the link at the bottom of the student page or directly at http://127.0.0.1:5050/staff.

## System Logic & Workflow
Job Submission: When a student uploads a file, a unique Ticket ID (starting from 1001) is assigned.

Queue Management: Newest jobs are inserted at the top of the queue for immediate visibility.

Status Updates:

Accept & Print: Moves job from "Queued" to "Printing."

Mark Ready: Moves job to "Ready for Pickup."

Reject: Stops the job and strikes through the file information.

Mock Firebase Sync: A placeholder function sync_to_firebase simulates real-time cloud database synchronization by logging status updates to the terminal.
