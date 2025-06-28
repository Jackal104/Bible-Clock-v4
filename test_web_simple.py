#!/usr/bin/env python3
"""
Simple test to check if Flask web server can start
"""

from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def test():
    return """
    <h1>Bible Clock Web Test</h1>
    <p>If you can see this, the web server is working!</p>
    <p>Current time: {}</p>
    """.format(os.popen('date').read() if os.name != 'nt' else 'N/A')

@app.route('/status')
def status():
    return {"status": "ok", "message": "Flask server is running"}

if __name__ == '__main__':
    print("Starting simple Flask test server...")
    print("Access at: http://localhost:5000 or http://bible-clock:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)