from flask import Flask,render_template,redirect,flash,url_for,request,session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo,Length,AnyOf,InputRequired
from flask_sqlalchemy import SQLAlchemy
import os
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_login import current_user, login_user
from werkzeug.urls import url_parse
from datetime import datetime
from time import time
from flask_login import UserMixin
from flask_login import logout_user
from flask_login import login_required

app=Flask(__name__)
app.secret_key="staying_home_saves_lives"
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = 'staying_home_saves_lives'
app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///' + os.path.join(basedir, 'app.db')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

order=[]
bills=dict()

@login.user_loader
def load_user(id):
    return seller_db.query.get(int(id))

@app.route('/logout')
def logout():
    session.pop("gov_logged_in",None)
    session.pop("seller_logged_in",None)
    logout_user()
    return redirect(url_for('index'))

class seller_login_form(FlaskForm):
    username = StringField('Username',validators=[InputRequired(),Length(min=4 , max=30)])
    password = PasswordField('Password',validators=[InputRequired(),Length(min=5 , max=80)])
    remember = BooleanField('Remember')
    submit = SubmitField('Submit')

class seller_register_form(FlaskForm):
    username = StringField('Username',validators=[DataRequired(),Length(min=4 , max=30)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password',validators=[DataRequired(),Length(min=5 , max=80)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password'),Length(min=5 , max=80)])
    area = StringField('Area', validators=[DataRequired(), Length(min=5, max=40)])
    submit = SubmitField('Submit')

class gov_register_form(FlaskForm):
    username = StringField('Username',validators=[DataRequired(),Length(min=4 , max=30)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password',validators=[DataRequired(),Length(min=5 , max=80)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password'),Length(min=5 , max=80)])
    submit = SubmitField('Submit')

class gov_login_form(FlaskForm):
    username = StringField('Username',validators=[DataRequired(),Length(min=4 , max=30)])
    password = PasswordField('Password',validators=[DataRequired(),Length(min=5 , max=80)])
    remember = BooleanField('Remember')
    submit = SubmitField('Submit')

class citizen_index_form(FlaskForm):
    orderlist = StringField('Order List', validators=[DataRequired(), Length(max=200)])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=30)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phno = IntegerField('Ph no', validators=[DataRequired()])
    area = StringField('Area', validators=[DataRequired(), Length(min=5, max=40)])
    address = StringField('Address', validators=[DataRequired(), Length(min=15)])
    submit = SubmitField('Submit')

class edit_seller_form(FlaskForm):
    id = IntegerField('Id', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=30)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=5, max=80)])
    area = StringField('Area', validators=[DataRequired(), Length(min=5, max=40)])
    submit = SubmitField('+ Add')

class add_commodities_form(FlaskForm):
    commodity_name = StringField('Commodity Name', validators=[InputRequired()])
    amount = IntegerField('Amount in Kg',validators=[InputRequired()])
    price = IntegerField('Price ( /Kg )',validators=[InputRequired()])
    submit = SubmitField('+ Add')

class seller_index_form(FlaskForm):
    id = IntegerField('Id', validators=[DataRequired()])
    submit = SubmitField('- Order Delivered')

class gov_index_form(FlaskForm):
    id = IntegerField('Id',validators=[InputRequired()])
    submit = SubmitField('- Delete')

@app.route('/', methods=('GET', 'POST'))
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/about', methods=('GET', 'POST'))
def about():
    return render_template('about.html')

@app.route('/portal', methods=('GET', 'POST'))
def portal():
    if "seller_logged_in" in session:
        return redirect(url_for('seller_index'))
    elif "gov_logged_in" in session:
        return redirect(url_for('gov_index'))
    return redirect(url_for('index'))


@app.route('/gov_register', methods=('GET', 'POST'))
def gov_register():
    form = gov_register_form()
    if "gov_logged_in" in session:
        if form.validate_on_submit():
            user = gov_db(username=form.username.data, email=form.email.data, password=form.password.data)
            db.session.add(user)
            db.session.commit()
            commit_message=session["gov_logged_in"]+" added new officer : "+form.username.data+" with email : "+form.email.data
            add_commit=commits(commit_text=commit_message)
            db.session.add(add_commit)
            db.session.commit()
            flash('Congratulations, new officer registered !')
            return redirect(url_for('gov_index'))
        return render_template('gov_register.html',form=form)
    else:
        return redirect(url_for('gov_login'))

@app.route('/gov_login', methods=('GET', 'POST'))
def gov_login():
    if "gov_logged_in" in session:
        flash('Already logged in !')
        return render_template(url_for('gov_index'))
    form = gov_login_form()
    if form.validate_on_submit():
        user = gov_db.query.filter_by(username=form.username.data).first()
        if user is None:
            flash('Invalid username or password')
            return redirect(url_for('gov_login'))
        else:
            if user.password != form.password.data:
                flash('Invalid username or password')
                return redirect(url_for('gov_login'))
        session["gov_logged_in"]=form.username.data
        login_user(user, remember=form.remember.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('gov_index')
        return redirect(next_page)
    return render_template('gov_login.html', form=form)

@app.route('/gov_index', methods=('GET', 'POST'))
def gov_index():
    if "gov_logged_in" in session:
        form = gov_index_form()
        return render_template('gov_index.html',sellers=seller_db.query.all(),officers=gov_db.query.all(),commits=commits.query.all(),form=form)
    else:
        return redirect(url_for('gov_login'))

@app.route('/edit_seller', methods=('GET', 'POST'))
def edit_seller():
    if "gov_logged_in" in session:
        form = edit_seller_form()
        if form.validate_on_submit():
            user = seller_db.query.filter_by(id=int(form.id.data)).first()
            if user:
                commit_message=session["gov_logged_in"]+" changed name of seller : "+user.username+" to "+form.username.data+" & email from "+user.email+" to "+form.email.data+" & password from "+str(user.password)+" to "+str(form.password.data)+" & area from "+user.area+" to "+form.area.data
                add_commit=commits(commit_text=commit_message)
                db.session.add(add_commit)
                db.session.commit()
                db.session.delete(user)
                db.session.commit()
                user = seller_db(id=form.id.data, username=form.username.data, email=form.email.data, password=form.password.data, area=form.area.data)
                db.session.add(user)
                db.session.commit()
                flash(f'Seller Details Updated','info')
                return redirect(url_for('gov_index'))
            else:
                flash(f'Invalid Id !','error')
        return render_template('edit_seller.html',sellers=seller_db.query.all(),form=form)
    else:
        return redirect(url_for('gov_login'))

@app.route('/delete', methods=('GET', 'POST'))
def delete():
    if "gov_logged_in" in session:
        form = gov_index_form()
        if form.validate_on_submit():
            user = seller_db.query.filter_by(id=form.id.data).first()
            if user:
                commit_message=session["gov_logged_in"]+" deleted seller : "+user.username+" with email "+user.email+" with area "+user.area
                add_commit=commits(commit_text=commit_message)
                db.session.add(add_commit)
                db.session.commit()
                db.session.delete(user)
                db.session.commit()
                flash(f'Updated Successfully', 'info')
            else:
                flash(f'Invalid Id Entered. Try again !', 'error')
                return redirect(url_for('gov_index'))
        return render_template('gov_index.html',sellers=seller_db.query.all(),form=form)
    else:
        return redirect(url_for('gov_login'))

@app.route('/seller_register', methods=('GET', 'POST'))
def seller_register():
    if "gov_logged_in" in session:
        form = seller_register_form()
        if form.validate_on_submit():
            print('form.username.data = ',form.username.data)
            commit_message=session["gov_logged_in"]+" added new seller : "+form.username.data+" with email : "+form.email.data+" with area : "+form.area.data
            add_commit=commits(commit_text=commit_message)
            db.session.add(add_commit)
            db.session.commit()
            me = seller_db(username=form.username.data, email=form.email.data, password=form.password.data,area=form.area.data)
            db.session.add(me)
            db.session.commit()
            flash('Congratulations, new seller registered !!')
            return redirect(url_for('gov_index'))
        return render_template('seller_register.html',form=form)
    else:
        return redirect(url_for('gov_login'))

@app.route('/seller_login', methods=('GET', 'POST'))
def seller_login():
    if "seller_logged_in" in session:
        flash('Already logged in !','info')
        return redirect(url_for('seller_index'))
    else:
        form = seller_login_form()
        if form.validate_on_submit():
            user = seller_db.query.filter_by(username=form.username.data).first()
            if user is None:
                flash('Invalid username or password')
                return redirect(url_for('seller_login'))
            else:
                if user.password != str(form.password.data):
                    flash('Invalid username or password')
                    return redirect(url_for('seller_login'))
                elif user.password == str(form.password.data) and user.username==form.username.data:
                    session["seller_logged_in"]=form.username.data
                    login_user(user, remember=form.remember.data)
                    next_page = request.args.get('next')
                    if not next_page or url_parse(next_page).netloc != '':
                        next_page = url_for('seller_index')
                    return redirect(next_page)
        return render_template('seller_login.html',form=form)

@app.route('/seller_index', methods=('GET', 'POST'))
def seller_index():
    if "seller_logged_in" in session:
        form = seller_index_form()
        if form.validate_on_submit():
            return redirect('order_delivered')
        seller_name = session["seller_logged_in"]
        seller_details = seller_db.query.filter_by(username=seller_name).first()
        order_no = orders.query.filter_by(area=seller_details.area).all()
        return render_template('seller_index.html',orderno=order_no,comodities=commodities.query.all(),form=form)
    else:
        return redirect(url_for('seller_login'))

@app.route('/order_delivered', methods=('GET', 'POST'))
def order_delivered():
    if "seller_logged_in" in session:
        form = seller_index_form()
        user = orders.query.filter_by(id=form.id.data).first()
        if form.validate_on_submit():
            if user:
                commit_message=session["seller_logged_in"]+" confirmed an order : "+user.orderlist+" on "+str(user.order_date)
                add_commit=commits(commit_text=commit_message)
                db.session.add(add_commit)
                db.session.commit()
                db.session.delete(user)
                db.session.commit()
                flash(f'Order with Id = {form.id.data} delivered successfully .', 'info')
            else:
                flash(f'Invalid Order Id Entered. Try again !', 'error')
                return redirect(url_for('gov_index'))
        return redirect(url_for('seller_index'))
    else:
        return redirect(url_for('seller_login'))

@app.route('/citizen_index', methods=('GET', 'POST'))
def citizen_index():
    form = citizen_index_form()
    if form.validate_on_submit():
        available_seller=seller_db.query.filter_by(area=form.area.data).first()
        if available_seller:
            orderno = orders(username=form.username.data, email=form.email.data, phno=form.phno.data, address=form.address.data, area=form.area.data ,orderlist=form.orderlist.data)
            db.session.add(orderno)
            db.session.commit()
            bill_name=form.username.data+".txt"
            fhand=open(bill_name,"a")
            fhand.close()
            os.remove(bill_name)
            order = form.orderlist.data.split()
            fhand=open(bill_name,"a")
            data="Customer Name : "+form.username.data+"\nEmail Id : "+form.email.data+"\nPhone No : "+str(form.phno.data)+"\nAddress : "+form.address.data+"\nArea : "+form.area.data+"\n\nOrders\n--------\nItemname\t\t\tQuantity\t\t\tPrice\n"
            fhand.write(data)
            tot_bill=0
            for item in order:
                product = commodities.query.filter_by(itemname=item).first()
                if product:
                    itemname_temp=product.itemname
                    if product.quantity>0:
                        quantity_temp = product.quantity-1
                        tot_bill+=product.price
                        data=item+"\t\t\t\t1 Kg\t\t\t\t"+str(product.price)+"\n"
                        fhand.write(data)
                    else:
                        tot_bill+=0
                        data=item+"\t\t\t\t0 Kg\t\t\t\t-----"+"\n"
                        fhand.write(data)
                    price_temp = product.price
                    db.session.delete(product)
                    db.session.commit()
                    product = commodities(itemname=itemname_temp,quantity=quantity_temp,price=price_temp)
                    db.session.add(product)
                    db.session.commit()
                else:
                    flash(f'The commodity you entered i.e., {item} is unavailable !')
            data="------------------------------------------------------------------------------------\nTotal Bill : "+str(tot_bill)+"\n------------------------------------------------------------------------------------\n"
            fhand.write(data)
            fhand.close()
            commit_message=form.username.data+" placed an order : "+form.orderlist.data+" with total bill : "+str(tot_bill)
            add_commit=commits(commit_text=commit_message)
            db.session.add(add_commit)
            db.session.commit()
            return redirect(url_for('index'))
        else:
            return redirect(url_for('unavailable_user'))
    return render_template('citizen_index.html',comodities=commodities.query.all(),form=form)

@app.route('/unavailable_user', methods=('GET', 'POST'))
def unavailable_user():
    return render_template('unavailable_user.html')

@app.route('/add_commodities', methods=('GET', 'POST'))
def add_commodities():
    if "seller_logged_in" in session:
        form = add_commodities_form()
        print('\n\n\nout if\n\n\n')
        if form.validate_on_submit():
            print('\n\n\nin if\n\n\n')
            user = commodities.query.filter_by(itemname=form.commodity_name.data).first()
            if user:
                itemname_temp=form.commodity_name.data
                quantity_temp=user.quantity+form.amount.data
                price_temp=form.price.data
                commit_message=session["seller_logged_in"]+" added "+str(form.amount.data)+" units of "+form.commodity_name.data+" and updated its price from "+str(user.price)+" to "+str(form.price.data)
                add_commit=commits(commit_text=commit_message)
                db.session.add(add_commit)
                db.session.commit()
                db.session.delete(user)
                db.session.commit()
                user = commodities(itemname=itemname_temp, quantity=quantity_temp, price=price_temp)
                db.session.add(user)
                db.session.commit()
                flash('Commodities Updated !')
                return redirect(url_for('seller_index'))
            else:
                user1 = commodities(itemname=form.commodity_name.data,quantity=form.amount.data,price=form.price.data )
                db.session.add(user1)
                db.session.commit()
                commit_message=session["seller_logged_in"]+" added new commodity : "+str(form.amount.data)+" units of "+form.commodity_name.data+" with price : "+str(form.price.data)
                add_commit=commits(commit_text=commit_message)
                db.session.add(add_commit)
                db.session.commit()
                flash('New Commodity Added !')
                return redirect('seller_index')
        return render_template('add_commodities.html',form=form)
    else:
        return redirect(url_for('seller_login'))

class seller_db(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password = db.Column(db.String(128))
    area = db.Column(db.String(20), index=True, unique=True)

    def __repr__(self):
        return '<seller_db {}>'.format(self.username)

class gov_db(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password = db.Column(db.String(128))

    def __repr__(self):
        return '<gov_db {}>'.format(self.username)

class commodities(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    itemname = db.Column(db.String(200), index=True, unique=True)
    quantity = db.Column(db.Integer, index=True, unique=False)
    price = db.Column(db.Integer,index=True,unique=False)

    def __repr__(self):
        return '<commodities {}>'.format(self.itemname)

class orders(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200),index=True,unique=False)
    email = db.Column(db.String(120), index=True, unique=False)
    phno = db.Column(db.Integer)
    address = db.Column(db.String(200), index=True, unique=False)
    area = db.Column(db.String(200), index=True, unique=False)
    orderlist = db.Column(db.String(200), index=True, unique=False)
    order_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<orders {}>'.format(self.id)

class commits(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    commit_text=db.Column(db.String(300),index=True,unique=False)

    def __repr__(self):
        return '<commited {}>'.format(self.id)


if __name__ == '__main__':
    app.run(debug=True)