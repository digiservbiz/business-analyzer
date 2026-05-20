from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import sys
import sqlite3

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from business_outreach import fetch_and_save_businesses, generate_outreach_message
from database.manage_templates import add_template, get_all_templates
from outreach.email_sender import send_email, get_email_template
from reports.report_generator import generate_report
from integrations.n8n_connector import send_to_n8n

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-production")

def sanitize_input(value, max_length=500):
    """Basic input sanitization."""
    if not value:
        return ""
    return str(value).strip()[:max_length]

def get_db_connection():
    conn = sqlite3.connect('businesses.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    businesses = conn.execute('SELECT * FROM businesses').fetchall()
    templates = get_all_templates()
    conn.close()
    return render_template('index.html', businesses=businesses, templates=templates)

@app.route('/fetch', methods=['POST'])
def fetch():
    query = sanitize_input(request.form.get('query', ''))
    location = sanitize_input(request.form.get('location', ''))
    if not query or not location:
        flash("Query and location are required.", 'error')
        return redirect(url_for('index'))
    fetch_and_save_businesses(query, location)
    flash(f"Successfully fetched businesses for query: {query}", 'success')
    return redirect(url_for('index'))

@app.route('/add_template', methods=['POST'])
def add_template_route():
    name = request.form['name']
    subject = request.form['subject']
    body = request.form['body']
    add_template(name, subject, body)
    flash(f"Successfully added template: {name}", 'success')
    return redirect(url_for('index'))

@app.route('/send_outreach', methods=['POST'])
def send_outreach_route():
    template_name = request.form['template_name']
    template = get_email_template(template_name)
    if not template:
        flash("Template not found!", 'error')
        return redirect(url_for('index'))

    conn = get_db_connection()
    businesses = conn.execute('SELECT * FROM businesses').fetchall()
    conn.close()

    for business in businesses:
        subject = template['subject'].format(business_name=business['name'])
        body = generate_outreach_message(business['name'], business['website'])
        to_email = f"contact@{business['website'].replace('http://', '')}" if business['website'] else "mock@example.com"
        send_email(to_email, subject, body)
    
    flash("Outreach emails have been sent successfully!", 'success')
    return redirect(url_for('index'))

@app.route('/generate_report')
def generate_report_route():
    conn = get_db_connection()
    businesses = conn.execute("SELECT name, address, website FROM businesses").fetchall()
    conn.close()
    businesses = [(b['name'], b['address'], b['website']) for b in businesses]

    report_path = generate_report(businesses)
    return send_file(report_path, as_attachment=True)

@app.route('/send_to_n8n', methods=['POST'])
def send_to_n8n_route():
    webhook_url = request.form['webhook_url']
    if not webhook_url:
        flash("Please provide an n8n webhook URL.", 'error')
        return redirect(url_for('index'))

    conn = get_db_connection()
    businesses = conn.execute('SELECT * FROM businesses').fetchall()
    conn.close()

    data_to_send = [dict(row) for row in businesses]
    send_to_n8n(webhook_url, data_to_send)
    flash("Successfully sent business data to n8n.", 'success')
    return redirect(url_for('index'))

@app.route('/edit_business/<int:business_id>', methods=['POST'])
def edit_business(business_id):
    name = request.form.get('name', '').strip()
    address = request.form.get('address', '').strip()
    website = request.form.get('website', '').strip()
    if not name:
        flash("Business name is required.", 'error')
        return redirect(url_for('index'))
    conn = get_db_connection()
    conn.execute(
        "UPDATE businesses SET name=?, address=?, website=? WHERE id=?",
        (name, address, website, business_id)
    )
    conn.commit()
    conn.close()
    flash(f"Business '{name}' updated successfully.", 'success')
    return redirect(url_for('index'))

@app.route('/delete_business/<int:business_id>', methods=['POST'])
def delete_business(business_id):
    conn = get_db_connection()
    business = conn.execute("SELECT name FROM businesses WHERE id=?", (business_id,)).fetchone()
    if business:
        conn.execute("DELETE FROM businesses WHERE id=?", (business_id,))
        conn.commit()
        flash(f"Business '{business['name']}' deleted.", 'success')
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
