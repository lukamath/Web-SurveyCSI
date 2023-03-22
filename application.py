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

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///db_csi03.db'
db=SQLAlchemy(app)

class Customer(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	username=db.Column(db.String(13),nullable=False, unique=True)
	password=db.Column(db.String(13),nullable=False)
	idcorso=db.Column(db.Integer,db.ForeignKey('course.id'))
	status=db.Column(db.Integer)
	#I set 0 as default status to identify a not-consumed account. When the account will fill the survey
	#I will set the statu as 1 and the account won't be more usable
	def __init__(self):
		self.staus = 0

# ===== <ManyToMany> ===== 
questions = db.Table('questions',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True),
    db.Column('mastersurvey_id', db.Integer, db.ForeignKey('mastersurvey.id'), primary_key=True)
)

class Question(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	qtype=db.Column(db.String)
	quest=db.Column(db.String)

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
    db.Column('section_id', db.Integer, db.ForeignKey('section.id'), primary_key=True),
    db.Column('qweight', db.Integer)
)

class Section(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	mastersurvey_id=db.Column(db.Integer, db.ForeignKey('mastersurvey.id'))
	stype=db.Column(db.String)
	insectionquestions=db.relationship('Question', secondary=insectionquestions, lazy='subquery', backref=db.backref('sections', lazy=True))

# =======================

# ===== <ManyToMany> ===== 

professor_course = db.Table('professor_course',
    db.Column('professor_id', db.Integer, db.ForeignKey('professor.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True)
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
	date_start=db.Column(db.DateTime)
	date_end=db.Column(db.DateTime)
	#professors=db.relationship('Professor', secondary=professor_course, lazy='subquery', backref=db.backref('courses', lazy=True))

# =======================


class Survey(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	customer_id=db.Column(db.Integer, db.ForeignKey('customer.id'))
	mastersurvey_id=db.Column(db.Integer, db.ForeignKey('mastersurvey.id'))
	answers=db.relationship('Answer', backref='survey', lazy=True)

class Answer(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	survey_id=db.Column(db.Integer, db.ForeignKey('survey.id'))
	question_id=db.Column(db.Integer, db.ForeignKey('question.id'))
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
			if customer:
				session["customer"] = username
				session["customer_id"] = customer.id
				#session["customer_type"] = customer.customertype
				return redirect(url_for('all_courses'))
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

@app.route('/api/addcourse', methods=['GET','POST'])
def add_course():
	if request.method=='POST':
		courseid=request.form['courseid']
		coursetype=request.form['coursetype']
		datestart=request.form['datestart']
		dateend=request.form['dateend']
		if not courseid:
			flash('id corso obbligatorio!')
		elif not coursetype:
			flash('tipo corso obbligatoria!')
		elif not datestart:
			flash('data inizio obbligatoria!')
		elif not dateend:
			flash('data fine  obbligatoria!')
		else:
			checkcourse=Course.query.filter_by(course_id=courseid).first()
			if checkcourse:
				flash('Corso gia'' presente')
			course=Course(
				course_id=courseid,
				course_type=coursetype,
				#date_start=datestart, 
				#date_end=dateend
				)
			db.session.add(course)
			db.session.commit()
			return redirect(url_for('index'))
		return render_template('newcourse.html') #I land again on newuser page if conditions are not all ok
	else:
		return render_template('newcourse.html')


@app.route('/api/allcourses', methods=['GET','POST'])
def all_courses():
	courses=Course.query.all()
	return render_template('listcourses.html', courses=courses)

@app.route('/api/addcustomer', methods=['GET','POST'])
def add_customer():
	courses=Course.query.all()
	if request.method=='POST':
		idcorso=request.form['idcorso']
		username=request.form['username']
		password=request.form['password']
		if not idcorso:
			flash('id corso obbligatorio!')
		else:
			course=Course.query.filter_by(course_id=idcorso).first()
			if course:
				idc=course.id
			else: 
				flash('Errore nella creazione customer')
				return 0;

			customer=Customer(
				idcorso=idcorso,
				username=username,
				password=password
				#date_start=datestart, 
				#date_end=dateend
				)
			db.session.add(customer)
			db.session.commit()
			return redirect(url_for('index'))
		return render_template('newcustomer.html') #I land again on newuser page if conditions are not all ok
	else:
		return render_template('newcustomer.html', courses=courses)

@app.route('/api/allcustomers', methods=['GET','POST'])
def all_customers():
	customers=Customer.query.all()
	return render_template('listcustomers.html', customers=customers)


@app.route('/api/addquestion', methods=['GET','POST'])
def add_question():
	questions=Question.query.all()
	if request.method=='POST':
		questiontype=request.form['questiontype']
		newquestion=request.form['newquestion']
		if not questiontype:
			flash('tipo domamnda obbligatorio!')
		elif not newquestion:
			flash('testo domanda obbligatorio!')
		else:
			question=Question(
				qtype=questiontype,
				quest=newquestion
				)
			db.session.add(question)
			db.session.commit()
		return render_template('questionmanager.html') #I land again on newuser page if conditions are not all ok
	else:
		return render_template('questionmanager.html', questions=questions)


@app.route('/api/allquestions', methods=['GET','POST'])
def all_questions():
	questions=Question.query.all()
	return render_template('listquestions.html', questions=questions)