from flask import Flask, request, render_template, url_for, flash, redirect, session, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_session import Session
from datetime import date, datetime
import pandas as pd
import openpyxl
import os

app=Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config['SECRET_KEY']='uOzPG137aJNoq2bBJ4b9P81DY5vCiRWj'

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///db_csi.db'
db=SQLAlchemy(app)

class Customer(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	username=db.Column(db.String(13),nullable=False, unique=True)
	password=db.Column(db.String(13),nullable=False)
	course_id=db.Column(db.String,db.ForeignKey('course.id'))

# ===== <ManyToMany> ===== 
questions = db.Table('questions',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True),
    db.Column('mastersurvey_id', db.Integer, db.ForeignKey('mastersurvey.id'), primary_key=True)
)

class Question(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	qtype=db.String(db.String)
	quest=db.String(db.String)

class Mastersurvey(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	questions = db.relationship('Question', secondary=questions, lazy='subquery', backref=db.backref('mastersurveys', lazy=True))
	sections=db.relationship('Section', backref='mastersurvey')

	#from questions to mastersurveys the query is lazy because the need to find masters from questions is rare 

#If you want to use many-to-many relationships you will need 
#to define a helper table that is used for the relationship. 
#For this helper table it is strongly recommended 
#to not use a model but an actual table:



#sections

insectionquestions = db.Table('insectionquestions',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True),
    db.Column('section_id', db.Integer, db.ForeignKey('section.id'), primary_key=True)
)

class Section(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	mastersurvey_id=db.Column(db.Integer)
	stype=db.Column(db.Integer)
	questions=db.relationship('Question', secondary=questions, lazy='subquery', backref=db.backref('sections', lazy=True))

# =======================

# ===== <ManyToMany> ===== 

professor_course = db.Table('professor_course',
    db.Column('professor_id', db.Integer, db.ForeignKey('Professor.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('Course.id'), primary_key=True)
)

class Professor(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	name=db.Column(db.String,nullable=False)
	surname=db.Column(db.String,nullable=False)
	teaching=db.Column(db.String)
	courses=db.relationship('Course', secondary=professor_course, lazy='subquery', backref=db.backref('professors', lazy=True))

class Course(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	course_id=db.Column(db.String, nullable=False)
	course_type=db.Column(db.String)
	date_start=db.Column(db.DateTime, nullable=False)
	date_end=db.Column(db.DateTime)
	professors=db.relationship('Professor', secondary=professor_course, lazy='subquery', backref=db.backref('courses', lazy=True))

# =======================


class Survey(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	customer_id=db.Column(db.Integer, db.ForeignKey('customer.id'))
	mastersurvey_id=db.Column(db.Integer, db.ForeignKey('mastersurvey.id'))
	answers=db.relationship('Answer', backref='survey', lazy=True)

class Answer(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	survey_id=db.Column(db.Integer)
	question_id=db.Column(db.Integer)
	value=db.Column(db.Integer)

@app.route('/',methods=['GET','POST'])
def index():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		if not username:
			flash('username obbligatorio!')
		elif not password:
			flash('password obbligatoria!')
		else:
			customer=Customer.query.filter_by(username=username, password=password).first()
			if user:
				session["user"] = username
				session["user_id"] = user.id
				session["user_type"] = user.usertype
				return redirect(url_for('list_students'))
		flash('Utente non trovato. Verifica le tue credenziali')
		return render_template('index.html')
	else:
		return render_template('index.html')

@app.route('/logout')
def logout():
	session["user"] = ''
	session["user_id"] = ''
	session["user_type"] = ''
	return render_template('loggedout.html')
