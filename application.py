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

questions = db.Table('questions',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True),
    db.Column('mastersurvey_id', db.Integer, db.ForeignKey('mastersurvey.id'), primary_key=True)
)

#sections
class Section(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	mastersurvey_id=db.Column(db.Integer)
	type=db.Column(db.Integer)
	questions=db.relationship('Question', secondary=questions, lazy='subquery', backref=db.backref('sections', lazy=True))

insectionquestions = db.Table('insectionquestions',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True),
    db.Column('section_id', db.Integer, db.ForeignKey('section.id'), primary_key=True)
)

# =======================

# ===== <ManyToMany> ===== 
class Professor(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	name=db.Column(db.String,nullable=False)
	surname=db.Column(db.String,nullable=False)
	teaching=db.Column(db.String)
	courses=db.relationship('Course', secondary=professor_course, lazy='subquery', backref=db.backref('courses', lazy=True))

class Course(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	course_id=db.Column(db.String, nullable=False)
	course_type=db.Column(db.String)
	date_start=db.Column(db.DateTime, nullable=False)
	date_end=db.Column(db.DateTime)

professor_course = db.Table('professor_course',
    db.Column('professor_id', db.Integer, db.ForeignKey('Professor.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('Course.id'), primary_key=True)
)

# =======================



class Answer(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	survey_id=db.Column(db.Integer)
	question_id=db.Column(db.Integer)
	value=db.Column(db.Integer)


class Payment(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	total=db.Column(db.Numeric, nullable=False)
	paym_card=db.Column(db.Integer)
	type_card=db.Column(db.String)
	paym_bank=db.Column(db.Integer)
	customer_id=db.Column(db.Integer, db.ForeignKey('customer.id'))
	receipt=db.relationship('Receipt',backref='payment')
	cash=db.relationship('Cash',backref='payment')
	user_id=db.Column(db.Integer, db.ForeignKey('user.id'))  #da correggere con username --> user.username

class Cash(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	date_collection=db.Column(db.DateTime, nullable=False)
	cash001=db.Column(db.Integer)
	cash002=db.Column(db.Integer)
	cash005=db.Column(db.Integer)
	cash010=db.Column(db.Integer)
	cash020=db.Column(db.Integer)
	cash050=db.Column(db.Integer)
	cash100=db.Column(db.Integer)
	cash200=db.Column(db.Integer)
	vault=db.Column(db.Integer, db.ForeignKey('cashvault.id'))  	#for user cash sheet
	deposit=db.Column(db.Integer, db.ForeignKey('cashdeposit.id'))	#for admin deposit
	payment_id=db.Column(db.Integer, db.ForeignKey('payment.id'))
	user_id=db.Column(db.Integer, db.ForeignKey('user.id'))

class Cashvault(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	date_vault=db.Column(db.DateTime, nullable=False)
	total_vault=db.Column(db.Numeric, nullable=False)
	user_id=db.Column(db.Integer, db.ForeignKey('user.id'))
	cash=db.relationship('Cash',backref='cashvault')

class Cashdeposit(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	date_deposit=db.Column(db.DateTime, nullable=False)
	total_deposit=db.Column(db.Numeric, nullable=False)
	user_id=db.Column(db.Integer, db.ForeignKey('user.id'))	
	cash=db.relationship('Cash',backref='cashdeposit')

class Customer(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	name=db.Column(db.String(25), nullable=False)
	surname=db.Column(db.String(25), nullable=False)
	tax_code=db.Column(db.String(16), nullable=False)
	address=db.Column(db.String(40))
	zip_code=db.Column(db.String(10))
	city=db.Column(db.String(25))
	prov_state=db.Column(db.String(2))
	nation=db.Column(db.String)
	course_id=db.Column(db.Integer)
	receipts=db.relationship('Receipt',backref='customer', lazy=True)
	payments=db.relationship('Payment',backref='customer')

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
			user=User.query.filter_by(username=username, password=password).first()
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

@app.route('/addpayment/<customer_id>',methods=['GET','POST'])
def add_payment(customer_id):
	customer=Customer.query.filter_by(id=customer_id).first()
	payments=Payment.query.filter_by(customer_id=customer_id).all()
	if request.method == 'POST':
		description=request.form['description']
		payment_method=request.form['payment-method']
		payment_quote=request.form['payment-quote']
		if not description:
			flash('description obbligatorio!')
		elif not payment_method:
			flash('payment-method obbligatoria!')
		elif not payment_quote:
			flash('payment-quote obbligatorio!')
		else:

			if payment_method=='Contante':
				#add_cash(payment, payments, receipt, customer)
				return redirect(url_for('add_cash', 
					customer_id=customer_id,
					description=description, 
					payment_method=payment_method, 
					payment_quote=payment_quote))

			else:	
				flash('sono fuori da add cash e dentro else --> GRAVISSIMO')
				flash('payment_method: '+ payment_method)				
				payments=Payment.query.filter_by(customer_id=customer_id).all()
				return render_template('liststudentspayments.html',customer=customer,payments=payments)
	else:
		print("customer id: " + customer_id)
		return render_template('liststudentspayments.html',customer=customer,payments=payments)


@app.route('/addcash',methods=['GET','POST'])
def add_cash():
	customer_id  = request.args.get('customer_id', None)
	description  = request.args.get('description', None)
	payment_method  = request.args.get('payment_method', None)
	payment_quote  = request.args.get('payment_quote', None)
	customer=Customer.query.filter_by(id=customer_id).first() #da rivedere se conviene rifare la query

	if request.method=='POST':

		payment=Payment(
				total=payment_quote,
				type_card=payment_method,
				customer_id=customer_id,
				user_id=session.get('user')
				)
		db.session.add(payment)
		db.session.commit()

		receipt=Receipt(
					customer_id=payment.customer_id,
					payment_id=payment.id,
					date_issue=date.today(),
					description=description
			)
		db.session.add(receipt)
		db.session.commit()

		customer=Customer.query.filter_by(id=customer_id).first()
		payments=Payment.query.filter_by(customer_id=customer_id).all()

		print('add pieces of cash here -->' + str(session.get('user_id')) + " - " + session.get('user') + " --> payment id: " + str(payment_quote))

		cash001 = request.form['cash001']
		cash002 = request.form['cash002']
		cash005 = request.form['cash005']
		cash010 = request.form['cash010']
		cash020 = request.form['cash020']
		cash050 = request.form['cash050']
		cash100 = request.form['cash100']
		cash200 = request.form['cash200']
		vault=0
		deposit=0
		payment_id=payment.id
		user_id=session.get('user_id')
		cash=Cash(
			date_collection=date.today(),
			cash001=cash001,
			cash002=cash002,
			cash005=cash005,
			cash010=cash010,
			cash020=cash020,
			cash050=cash050,
			cash100=cash100,
			cash200=cash200,
			vault=vault,
			deposit=deposit,
			payment_id=payment_id,
			user_id=user_id
			)
		db.session.add(cash)
		db.session.commit()
		return redirect(url_for('add_payment',customer_id=customer_id)) 	
	else:
		flash=("Sono entrato in ADD_CASH con GET... ekkekkazzo, no!!!!")
		return render_template('newcash.html',customer=customer, payment_quote=payment_quote)

#API
@app.route('/adduser', methods=['GET','POST'])
def add_user():
	if request.method == 'POST':
		name=request.form['name']
		surname=request.form['surname']
		username=request.form['username']
		password=request.form['password']
		repeatpassword=request.form['repeatpassword']
		usertype=request.form['usertype']
		if not username:
			flash('username obbligatorio!')
		elif not password:
			flash('password obbligatoria!')
		elif not name:
			flash('nome obbligatorio!')
		elif not surname:
			flash('cognome obbligatorio!')
		elif password!=repeatpassword:
			flash('le password non corrispondono!')
		else:
			checkuser=User.query.filter_by(username=username).first()
			if checkuser:
				flash('Utente gia'' presente')
			user=User(
				name=name,
				surname=surname,
				username=username, 
				password=password,
				usertype=usertype
				)
			db.session.add(user)
			db.session.commit()
			return redirect(url_for('index'))
		return render_template('newuser.html') #I land again on newuser page if conditions are not all ok
	else:
		return render_template('newuser.html')

@app.route('/bankmanagement', methods=['GET','POST'])
def bank_management():
	total_deposit=0
	if request.method=='POST':
		#cashes=Cash.query.filter_by(deposit=False).all()
		cashdeposit=Cashdeposit(date_deposit=date.today(), total_deposit=total_deposit, user_id=session.get('user'))
		db.session.add(cashdeposit)
		db.session.commit()
		cashes=Cash.query.filter_by(deposit=False).all()
		for cash in cashes:
			Cash.query.filter_by(id=cash.id).update(dict(deposit=cashdeposit.id))	
	else:
		#cashes=Cash.query.filter_by(deposit=False).all()
		cashes=Cash.query.all()
	db.session.commit()
	return render_template('bankmanagement.html', cashes=cashes, user_id=str(session.get('user_id')))

@app.route('/addcustomer', methods=['GET','POST'])
def add_customer():
	if request.method=='POST':
		name=request.form['name']
		surname=request.form['surname']
		tax_code=request.form['tax_code']
		address=request.form['address']
		zip_code=request.form['zip_code']
		city=request.form['city']
		prov_state=request.form['prov_state']
		nation=request.form['nation']
		course_id=request.form['course_id']
		customer=Customer(name=name, surname=surname, tax_code=tax_code,address=address,zip_code=zip_code,city=city, prov_state=prov_state,nation=nation, course_id=course_id)
		db.session.add(customer)
		db.session.commit()
		return redirect(url_for('list_students'))
	else:
		return render_template('newcustomer.html')

@app.route('/liststudents', methods=['GET','POST'])
def list_students():
	if request.method=='POST':
	    keysearch=request.form['srchsurname']
	    customers=Customer.query.filter_by(surname=keysearch).all()
	    return render_template('liststudents.html', customers=customers)
	else:
		customers=Customer.query.all()
		return render_template('liststudents.html', customers=customers)

#@app.route('/search', methods=['GET','POST'])
#def search():
# 	if request.method=='POST':
# 	    keysearch=request.form['srchsurname']
# 	    customer=Customer.query.filter_by(surname=keysearch).first()
# 	    return redirect(url_for('add_payment',customer_id=customer.id))
# 	else:
#	return redirect(url_for('list_students'))
	    
@app.route('/listpayments')
def list_payments():
	payments=Payment.query.all()
	return render_template('listpayments.html', payments=payments)

@app.route('/listreceipts')
def list_receipts():
	receipts=Receipt.query.all()
	return render_template('listreceipts.html', receipts=receipts)

@app.route('/listusers')
def list_users():
	users=User.query.all()
	return render_template('listusers.html', users=users)

@app.route('/listcashes', methods=['GET','POST'])
def list_cashes():
	cashes=Cash.query.all()
	return render_template('listcashes.html', cashes=cashes)

@app.route('/casheet/<user_id>', methods=['GET','POST'])
def cash_sheet(user_id):
	if request.method=='POST':
		username=request.form['username']
		return redirect(url_for('print_casheet'))
	else:
		tot=0
		cash001=0
		cash002=0
		cash005=0
		cash010=0
		cash020=0
		cash050=0
		cash100=0
		cash200=0
		usercashes=Cash.query.filter_by(user_id=user_id, vault=0).all()
		#tot = Cash.query(func.sum(Cash.cash001)).filter_by(user_id=user_id).first()
		for cash in usercashes:
			if cash.cash001!='':
				cash001=cash001+cash.cash001
			if cash.cash002!='':
				cash002=cash002+cash.cash002
			if cash.cash005!='':
				cash005=cash005+cash.cash005
			if cash.cash010!='':
				cash010=cash010+cash.cash010
			if cash.cash020!='':
				cash020=cash020+cash.cash020
			if cash.cash050!='':
				cash050=cash050+cash.cash050
			if cash.cash100!='':
				cash100=cash100+cash.cash100
			if cash.cash200!='':
				cash200=cash200+cash.cash200
		daily_total=cash001*1+cash002*2+cash005*5+cash010*10+cash020*20+cash050*50+cash100*100+cash200*200
		return render_template('casheet.html', user=session.get('user'),usercashes=usercashes, dailycash=DailyUserCash(cash001,cash002,cash005,cash010,cash020,cash050,cash100,cash200,daily_total),day=date.today())

class DailyUserCash:
	def __init__(self, cash001, cash002, cash005, cash010, cash020, cash050, cash100, cash200, daily_total):
		self.cash001 = cash001
		self.cash002 = cash002
		self.cash005 = cash005
		self.cash010 = cash010
		self.cash020 = cash020
		self.cash050 = cash050
		self.cash100 = cash100
		self.cash200 = cash200
		self.daily_total=daily_total


#===================== test Export DB in Excel =====================

UPLOAD_FOLDER = 'F:/Luka/Programming/Python/WebCash/Downloads' 
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER

def to_dict(row):
    if row is None:
        return None

    rtn_dict = dict()
    keys = row.__table__.columns.keys()
    for key in keys:
        rtn_dict[key] = getattr(row, key)
    return rtn_dict


@app.route('/excel', methods=['GET', 'POST'])
def exportexcel():

    data = User.query.all()
    data_list = [to_dict(item) for item in data]
    df = pd.DataFrame(data_list)
    filename = app.config['UPLOAD_FOLDER']+"/userlist.xlsx"
    print("Filename: "+ filename)

    writer = pd.ExcelWriter(filename, engine='openpyxl')
    df.to_excel(writer, sheet_name='kaz01')
    writer.save()

    return redirect(url_for('add_user'))


#https://www.tutorialexample.com/python-pandas-append-data-to-excel-a-step-guide-python-pandas-tutorial/
@app.route('/newrow', methods=['GET','POST'])
def new_row():

	#excel_name = app.config['UPLOAD_FOLDER']+"/userlist03.xlsx"
	excel_name ='/Downloads/userlist.xlsx'

	data=User.query.order_by(User.id.desc()).first()
	data_list = [to_dict(data)]
	df = pd.DataFrame(data_list, index= None)
	
	df_source = None
	if os.path.exists(excel_name):
		data_list=pd.read_excel('/Downloads/userlist.xlsx',engine='openpyxl',index_col=None)
		df_source = pd.DataFrame(data_list)
	if df_source is not None:
		df_dest = df_source.append(df)
	else:
		df_dest = df

	writer=pd.ExcelWriter(excel_name)
	df_dest.to_excel(writer, sheet_name='kaz02')
	writer.save()

	return redirect(url_for('add_user'))


@app.route('/printcasheet', methods=['GET','POST'])
def print_casheet():
	user_id=session.get('user_id')
	data = Cash.query.filter_by(user_id=user_id	, vault=0).all()
	#create a cashvault obj
	cashvault=Cashvault(date_vault=date.today(), total_vault=0,user_id=user_id)
	db.session.add(cashvault)
	db.session.commit()
	tot=0
	cash001=0
	cash002=0
	cash005=0
	cash010=0
	cash020=0
	cash050=0
	cash100=0
	cash200=0
	daily_total=0
	for cash in data:
		if cash.cash001!='':
				cash001=cash001+cash.cash001
		if cash.cash002!='':
			cash002=cash002+cash.cash002
		if cash.cash005!='':
			cash005=cash005+cash.cash005
		if cash.cash010!='':
			cash010=cash010+cash.cash010
		if cash.cash020!='':
			cash020=cash020+cash.cash020
		if cash.cash050!='':
			cash050=cash050+cash.cash050
		if cash.cash100!='':
			cash100=cash100+cash.cash100
		if cash.cash200!='':
			cash200=cash200+cash.cash200
		flash(cashvault.id)
		Cash.query.filter_by(id=cash.id).update(dict(vault=cashvault.id))
		db.session.commit()
		daily_total=cash001*1+cash002*2+cash005*5+cash010*10+cash020*20+cash050*50+cash100*100+cash200*200
	Cashvault.query.filter_by(id=cashvault.id).update(dict(total_vault=daily_total))

	#write file
	data_list = [to_dict(item) for item in data]
	df = pd.DataFrame(data_list)
	filename = app.config['UPLOAD_FOLDER']+"/Foglio_Cassa_"+str(session.get('user'))+"_"+str(date.today())+".xlsx"
	print("Filename: "+ filename)

	writer = pd.ExcelWriter(filename, engine='openpyxl')
	df.to_excel(writer, sheet_name='Cash')
	writer.save()
	Cash.query.filter_by(user_id=user_id,vault=0).update(dict(vault=1))
	db.session.commit()
	return redirect(url_for('cash_sheet', user_id=user_id, username	=session.get('user')))


@app.route('/testkaz/<username>', methods=['GET','POST'])
def test_kaz(username):
	usercashes=Cash.query.filter_by(user_id=session.get('user_id'), vault=0).all()
	return render_template('testkaz.html', username=username, usercashes=usercashes)