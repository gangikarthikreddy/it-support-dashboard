import subprocess
import time
import os

# Start Flask API in background
flask_process = subprocess.Popen(["python", "app.py"])

# Wait for Flask to start
time.sleep(3)

# Run Streamlit app
os.system("streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0")
