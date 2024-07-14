from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:password@localhost/commuter_portal'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')  # 'pending', 'accepted', 'rejected'
    
    user_name = db.Column(db.String(150), nullable=False)  # User's name
    user_address = db.Column(db.String(255), nullable=False)  # User's address
    user_contact = db.Column(db.String(50), nullable=False)  # User's contact number



class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='unpaid')  # 'unpaid', 'paid', 'refunded'
    accepted_by = db.Column(db.String(150), nullable=True)  # To track who accepted the payment


class Tracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False)
    location = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect(url_for('login'))

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
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
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
    user_trackings = Tracking.query.filter(Tracking.request_id.in_([r.id for r in user_requests])).all()
    return render_template('dashboard.html', requests=user_requests, payments=user_payments, trackings=user_trackings)

@app.route('/manage_requests', methods=['GET', 'POST'])
@login_required
def manage_requests():
    if request.method == 'POST':
        action = request.form.get('action')
        request_id = request.form.get('request_id')

        request_obj = Request.query.get(request_id)

        if action == 'accept':
            request_obj.status = 'accepted'
            request_obj.accepted = True
            flash('Request accepted successfully!', 'success')
        elif action == 'reject':
            request_obj.status = 'rejected'
            flash('Request rejected successfully!', 'warning')

        db.session.commit()
        return redirect(url_for('manage_requests'))

    # Get all requests for the logged-in user
    user_requests = Request.query.all()  # You can filter based on your requirements
    return render_template('manage_requests.html', requests=user_requests)



@app.route('/manage_payments', methods=['GET', 'POST'])
@login_required
def manage_payments():
    if request.method == 'POST':
        action = request.form.get('action')
        payment_id = request.form.get('payment_id')

        payment_obj = Payment.query.get(payment_id)

        if action == 'accept':
            payment_obj.status = 'paid'
            payment_obj.accepted_by = current_user.username
            flash('Payment accepted successfully!', 'success')
        
        db.session.commit()
        return redirect(url_for('manage_payments'))

    # Get all unpaid payments
    unpaid_payments = Payment.query.filter_by(status='unpaid').all()
    return render_template('manage_payments.html', payments=unpaid_payments)


@app.route('/track', methods=['GET', 'POST'])
@login_required
def track():
    if request.method == 'POST':
        request_id = request.form['request_id']
        location = request.form['location']
        new_tracking = Tracking(request_id=request_id, location=location)
        db.session.add(new_tracking)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('track.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

