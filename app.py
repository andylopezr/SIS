from flask import Flask, request, jsonify, render_template, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import datetime
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging

# Initializes app and authentication
app = Flask(__name__)
homedir = os.path.abspath(os.path.dirname(__file__))
auth = HTTPBasicAuth()

users = {
    "andy": generate_password_hash("password"),
    "test": generate_password_hash("pwd")
}


# Database location + secret key for flash messages
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(homedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '2496c6d62b0c524876c5e05ce420677651e7e38bd0383609'

# Initializes DB
db = SQLAlchemy(app)

# Initializes Marshmallow
ma = Marshmallow(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

    def __init__(self, email, name, password):
        self.email = email
        self.name = name
        self.password = password

# Creates DB
db.create_all()

# User Schema
class FormSchema(ma.Schema):
    class Meta:
       fields = ('id', 'email', 'name', 'password')

# Initialize Schema
form_schema = FormSchema()
forms_schema = FormSchema(many=True)

#Verifies password and username fields
@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username

# Display index
@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')

# Obtain form data
@app.route('/create/', methods=('GET', 'POST'))
def create():

    if request.method == 'POST':

        email = request.form['email']
        name = request.form['name']
        password = request.form['password']
        
        if not email:
            flash('Email is required')
        elif not name:
            flash('Name is required')
        elif not password:
            flash('Password is required')
        else:

            new_reg = User(email, name, password)
            db.session.add(new_reg)

            try:
                db.session.commit()
                flash('User Created successfully')
                # Logging user creation event
                logging.basicConfig(filename='creation.log', encoding='utf-8', level=logging.NOTSET)
                logging.info('{} - {} \n'.format(name, datetime.now()))

            except Exception as e:
                # logging
                flash('Email or Name already on record')

            return render_template('create.html')

    return render_template('create.html')

# Get all regs
@app.route('/all/', methods=['GET'])
def all():

    all_regs = User.query.all()
    results = forms_schema.dump(all_regs)
    return render_template('all.html', results=results)

# Update email field
@app.route('/update/', methods=['GET', 'POST'])
def update():

    if request.method == 'POST':
        current_email = request.form['cemail']
        new_email = request.form['nemail']

        if not current_email:
            flash('Current Email is required')
        elif not new_email:
            flash('New Email is required')
        else:

            try:
                form = User.query.filter_by(email=current_email).first()
                form.email = new_email
                db.session.commit()
                flash('Update Successful')

            except Exception as e:
                flash('Email not found or on file')

            return render_template('update.html')

    return render_template('update.html')

@app.route('/delete/', methods=['GET', 'POST'])
def delete():

    if request.method == 'POST':
        del_id = request.form['del_id']

        if not del_id:
            flash('ID is required')

        else:
            try:

                form = User.query.filter_by(id=del_id).first()
                db.session.delete(form)
                db.session.commit()
                flash('User deleted successfully')

            except Exception as e:
                flash('ID not found')

            return render_template('delete.html')
            
    return render_template('delete.html')
    
# Run Server as Dev
if __name__ == '__main__':
    app.run(debug=True)
