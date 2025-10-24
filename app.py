from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import psutil

# --- Flask setup ---
app = Flask(__name__)
CORS(app)

# --- Database setup ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Ticket model ---
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default="Open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

# Create database tables (only the first time)
with app.app_context():
    db.create_all()

# --- Routes ---

@app.route('/')
def home():
    return jsonify({"message": "IT Support API running ✅"})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    })

@app.route('/tickets', methods=['GET'])
def get_tickets():
    tickets = Ticket.query.all()
    return jsonify([t.to_dict() for t in tickets])

@app.route('/tickets', methods=['POST'])
def create_ticket():
    data = request.json
    if not data.get("title") or not data.get("description"):
        return jsonify({"error": "Title and description are required"}), 400

    ticket = Ticket(title=data["title"], description=data["description"])
    db.session.add(ticket)
    db.session.commit()
    return jsonify({"message": "Ticket created successfully", "ticket": ticket.to_dict()}), 201

@app.route('/tickets/<int:ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    data = request.json
    ticket.status = data.get("status", ticket.status)
    db.session.commit()
    return jsonify({"message": "Ticket updated", "ticket": ticket.to_dict()})

if __name__ == '__main__':
    app.run(debug=True)

import os

# (your Flask setup code above...)

if __name__ == "__main__":
    CORS(app)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
