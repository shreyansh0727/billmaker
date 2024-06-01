import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import datetime
import random
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Set the secret key from the environment variable
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')  # 'default_secret_key' is used if the environment variable is not set


# Get admin credentials from environment variables
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

cred = credentials.Certificate("billmaker-c2990-firebase-adminsdk-rppbl-e6b70f32e5.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def generate_receipt_number():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:  # Replace with your credentials or use a database to verify
            user = User(id='admin')
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
@login_required
def calculate():
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        total = quantity * price
        current_date_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        receipt_number = int(generate_receipt_number())
        receipt_data = {
            'customer_name': customer_name,
            'quantity': quantity,
            'price': price,
            'total': total,
            'current_date_time': current_date_time,
            'receipt_number': receipt_number
        }
        db.collection('receipts').add(receipt_data)
        return render_template('receipt.html', customer_name=customer_name, quantity=quantity, price=price, total=total, receipt_number=receipt_number, current_date_time=current_date_time)

@app.route('/print_receipt', methods=['POST'])
@login_required
def print_receipt():
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        total = float(request.form['total'])
        current_date_time = request.form['current_date_time']
        receipt_number = int(request.form['receipt_number'])
        return render_template('print_receipt.html', customer_name=customer_name, quantity=quantity, price=price, total=total, current_date_time=current_date_time, receipt_number=receipt_number)

@app.route('/search_receipt/<int:receipt_number>')
@login_required
def search_receipt(receipt_number):
    receipt_ref = db.collection('receipts').where('receipt_number', '==', receipt_number).get()
    if receipt_ref:
        receipt_data = receipt_ref[0].to_dict()
        return render_template('findreceipt.html', **receipt_data)
    else:
        return "Receipt not found"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
