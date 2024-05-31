import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request, redirect, url_for
import datetime
import random

# Initialize Flask app
app = Flask(__name__)

def generate_receipt_number():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])
# Initialize Firebase app
cred = credentials.Certificate("billmaker-c2990-firebase-adminsdk-rppbl-e6b70f32e5.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


# Home route
@app.route('/')
def index():
    return render_template('index.html')


# Calculate route
@app.route('/calculate', methods=['POST'])
def calculate():
    if request.method == 'POST':
        # Get form data
        customer_name = request.form['customer_name']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        total = quantity * price
        current_date_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        receipt_number = int(generate_receipt_number())
        # Save receipt details to Firebase
        receipt_data = {
            'customer_name': customer_name,
            'quantity': quantity,
            'price': price,
            'total': total,
            'current_date_time': current_date_time,
            'receipt_number': receipt_number
        }
        db.collection('receipts').add(receipt_data)

        # Render receipt template with data
        return render_template('receipt.html', customer_name=customer_name, quantity=quantity, price=price, total=total,receipt_number=receipt_number ,current_date_time=current_date_time )



@app.route('/print_receipt', methods=['POST'])
def print_receipt():
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        total = float(request.form['total'])
        current_date_time = request.form['current_date_time']
        receipt_number = int(request.form['receipt_number'])
        return render_template('print_receipt.html', customer_name=customer_name, quantity=quantity, price=price, total=total, current_date_time=current_date_time, receipt_number=receipt_number)




       

if __name__ == '__main__':
    app.run(debug=True)
