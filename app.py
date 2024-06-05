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

app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=1)  # Adjust the lifetime as needed

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
def index():
    return render_template('index.html')


@app.route('/calculate', methods=['POST'])
@login_required
def calculate():
        if request.method == 'POST':
            customer_name = request.form['customer_name']
            product_id = request.form['product_id']
            quantity = int(request.form['quantity'])

            # Fetch product details from Firestore
            product_ref = db.collection('products').document(product_id)
            product = product_ref.get()
            if not product.exists:
                return "Product not found"

            product_data = product.to_dict()
            price = product_data['price']
            total = quantity * price
            current_date_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            receipt_number = int(generate_receipt_number())

            # Ensure the quantity is an integer
            product_quantity = int(product_data['quantity'])

            # Save receipt details to Firebase
            receipt_data = {
                'customer_name': customer_name,
                'product_id': product_id,
                'product_name': product_data['name'],
                'quantity': quantity,
                'price': price,
                'total': total,
                'current_date_time': current_date_time,
                'receipt_number': receipt_number
            }
            db.collection('receipts').add(receipt_data)

            # Update product quantity in Firestore
            new_quantity = product_quantity - quantity
            if new_quantity < 0:
                return "Insufficient product quantity"
            product_ref.update({'quantity': new_quantity})

            return render_template('receipt.html', customer_name=customer_name, product_name=product_data['name'], quantity=quantity, price=price, total=total, receipt_number=receipt_number, current_date_time=current_date_time)
           




if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)