from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import re
import requests  # Add this line
from flask import Flask, render_template, request, jsonify
import subprocess


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:password@localhost/salesman_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    shopname = db.Column(db.String(150), nullable=False)

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')  # 'pending', 'accepted', 'rejected'
    customer_name = db.Column(db.String(150), nullable=False)  # User's name
    customer_address = db.Column(db.String(255), nullable=False)  # User's address
    customer_contact = db.Column(db.String(50), nullable=False)  # User's contact number
    customer_name = db.Column(db.String(150), nullable=False)  # Customer's name
    customer_address = db.Column(db.String(255), nullable=False)  # Customer's address
    customer_contact = db.Column(db.String(50), nullable=False)  # Customer's contact number


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='unpaid')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def validate_password(password):
    if (len(password) < 8 or 
        not re.search("[a-z]", password) or 
        not re.search("[A-Z]", password) or 
        not re.search("[0-9]", password) or 
        not re.search("[@#$%^&+=]", password)):
        return False
    return True

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        shopname = request.form['shopname']

        if not validate_password(password):
            flash('Password must be at least 8 characters long and contain an uppercase letter, a lowercase letter, a numeric digit, and a special character.', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, password=password, shopname=shopname)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        shopname = request.form['shopname']  # Get shopname from the form

        user = User.query.filter_by(username=username, password=password, shopname=shopname).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username, password, or shop name')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_requests = Request.query.filter_by(user_id=current_user.id).all()
    user_payments = Payment.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', requests=user_requests, payments=user_payments, trackings='track.html')

@app.route('/')
def home():
    return render_template('request.html')  # Adjust to your HTML file name

@app.route('/run_script', methods=['POST'])
def run_script():
    try:
        # Replace 'your_script.py' with the name of your Python file
        subprocess.run(['python', 'aiapp.py'], check=True)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route('/request', methods=['GET', 'POST'])
@login_required
def make_request():
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        customer_address = request.form['customer_address']
        customer_contact = request.form['customer_contact']
        
        new_request = Request(
            user_id=current_user.id,
            customer_name=customer_name,
            customer_address=customer_address,
            customer_contact=customer_contact
        )
        db.session.add(new_request)
        db.session.commit()
        
        # Send a POST request to the commuter portal
        request_data = {
            'user_id': current_user.id,
            'customer_name': customer_name,
            'customer_address': customer_address,
            'customer_contact': customer_contact
        }
        response = requests.post('http://127.0.0.1:5000/api/requests', json=request_data)  # Change here
        if response.status_code == 200:
            flash('Request sent successfully!', 'success')
        else:
            flash('Failed to send request', 'danger')

        return redirect(url_for('dashboard'))
    
    return render_template('request.html')



@app.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    if request.method == 'POST':
        amount = request.form['amount']
        new_payment = Payment(user_id=current_user.id, amount=amount)
        db.session.add(new_payment)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('payment.html')

@app.route('/track', methods=['GET', 'POST'])
@login_required
def track():
    if request.method == 'POST':
        request_id = request.form['request_id']
        location = request.form['location']
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('track.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)