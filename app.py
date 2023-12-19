import email
from flask import Flask, render_template, request, flash, session, redirect
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import json
import os
from werkzeug.utils import secure_filename
from base64 import b64encode
from datetime import datetime
import csv
import sys
from flask_mail import Mail, Message
#from werkzeug import secure_filename

#config file attachment with server

with open('config.json', 'r') as var:
    para = json.load(var) ["para"]

local_server = True


app = Flask(__name__)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = para['local_uri']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = para['img_location']
    app.secret_key = 'my unobvious secret key'
    ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
    app.config['MAIL_SERVER']='smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = para['gmail-user']
    app.config['MAIL_PASSWORD'] = para['gmail-password']
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    mail = Mail(app)

else:
    app.config['SQLALCHEMY_DATABASE_URI'] = para['prod_uri']
db = SQLAlchemy(app)

class Emp(db.Model):

    # Sno, Name, Age, Email, Address, Post, Phone, Photo

    Sno = db.Column(db.String(10), primary_key=True, nullable=False)
    Name = db.Column(db.String(20), unique=False, nullable=False)
    Age = db.Column(db.Integer, unique=False, nullable=False)
    Email = db.Column(db.String(30), unique=True, nullable=False)
    Address = db.Column(db.String(120), unique=True, nullable=False)
    Post = db.Column(db.String(20), unique=False, nullable=False)
    Phone = db.Column(db.String(120), unique=True, nullable=False)
    Photo = db.Column(db.String(length=5056), unique=True, nullable=False)
    

    def __repr__(self) -> str:
        return f"{self.Sno} - {self.Name} - {self.Email} - {self.Post} - {self.Phone} - {self.Photo}"



class Pres(db.Model):
    Sno = db.Column(db.String(10), primary_key=True, nullable=False)
    Time = db.Column(db.Time(), primary_key=True, nullable=False)
    Date = db.Column(db.Date(), primary_key=True, nullable=False)

    def __repr__(self) -> str:
        return f"{self.Sno} - {self.Time} - {self.Date}"





@app.route("/mkatnd", methods=['GET', 'POST'])
def makeattend():
    #file name and path define in code
    directory = "Attendance/"
    filename = datetime.now().strftime("%Y%m%d")
    filepath = directory + filename
    if os.path.exists(filepath+'.csv'):
        if ('user' in session and session['user'] == para['admin_user']):
            #set the session variable
            #session['user'] = username

            with open(filepath+'.csv') as csv_file:
                csvfile = csv.reader(csv_file, delimiter=',')
                all_value = []
                for row in csvfile:
                    value1 = row[0]
                    value2 = row[1]
                    value3 = row[2]
                    value4 = Pres(Sno=value1, Time=value2, Date=value3)
                    db.session.add(value4)
                    db.session.commit()

                data = Emp.query.filter(Emp.Sno==Pres.Sno).all()
            return render_template('Present.html', alldata=data)

        if request.method == 'POST':
            username = request.form.get('uname')
            userpass = request.form.get('password')
            if (username == para['admin_user'] and userpass == para['admin_password']):
                flash("Login Successfully!", "success")
                #set the session variable
                session['user'] = username
                with open(filepath+'.csv') as csv_file:
                    csvfile = csv.reader(csv_file, delimiter=',')
                    all_value = []
                    for row in csvfile:
                        value1 = row[0]
                        value2 = row[1]
                        value3 = row[2]
                        value4 = Pres(Sno=value1, Time=value2, Date=value3)
                        db.session.add(value4)
                        db.session.commit()
                    
                    data = Emp.query.filter(Emp.Sno==Pres.Sno).all()
                return render_template('Present.html', alldata=data)

            elif (username != para['admin_user'] or userpass != para['admin_password']):
                flash("Login Failed. Password or User name incorrect", "danger")

        return render_template('pages-login.html')
    else:
        with open(filepath+'.csv', 'w+') as csv_file:
            pass
    return redirect('/mkatnd')


@app.route("/mail/<string:Sno>", methods = ['GET', 'POST'])
def mailsend(Sno):
    if ('user' in session and session['user'] == para['admin_user']):
        emailid = db.session.query(Emp).filter(Emp.Sno==Sno).first()
        msg = Message('Your Attendance has been marked', sender = para['gmail-user'], recipients = [emailid.Email])
        msg.body = Sno + "your attendance has succesfully marked! have a nice day."
        mail.send(msg)
        return redirect('/index')

@app.route("/mailabs/<string:Sno>", methods = ['GET', 'POST'])
def mailsend1(Sno):
    if ('user' in session and session['user'] == para['admin_user']):
        emailid = db.session.query(Emp).filter(Emp.Sno==Sno).first()
        msg = Message('Your are absent', sender = para['gmail-user'], recipients = [emailid.Email])
        msg.body = Sno + " You are absent today."
        mail.send(msg)
        return redirect('/absent')


@app.route("/camon", methods=['GET', 'POST'])
def camon():
    from subprocess import call
    call(["python", "attend.py"])
    flash("Camera Turned On", "success")
    return redirect('/Present')



@app.route("/wicamon", methods=['GET', 'POST'])
def camonwifi():
    from subprocess import call
    call(["python", "attendwifi.py"])
    flash("Camera Turned On", "success")
    return redirect('/Present')



@app.route("/offcam", methods=['GET', 'POST'])
def camoff():
    os.system("taskkill /f /im Python.exe")
    return redirect('/Present')



@app.route("/offwificam", methods=['GET', 'POST'])
def camoffwifi():
    os.system("taskkill /f /im Python.exe")
    flash("Login Successfully!", "success")
    return redirect('/Present')


@app.route("/absent", methods=['GET', 'POST'])
def absent():
    if ('user' in session and session['user'] == para['admin_user']):
        data = db.session.query(Emp).join(Pres, Emp.Sno!=Pres.Sno).all()
        return render_template('Absent.html', alldata=data)



@app.route("/Present", methods=['GET', 'POST'])
def Present():

    if ('user' in session and session['user'] == para['admin_user']):
        #set the session variable
        data = Emp.query.filter(Emp.Sno==Pres.Sno).all()
        return render_template('Present.html', alldata=data)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('password')
        if (username == para['admin_user'] and userpass == para['admin_password']):
            flash("Login Successfully!", "success")
            #set the session variable
            session['user'] = username
            data = Emp.query.filter(Emp.Sno==Pres.Sno).all()
            mail.send_message('hello', sender=[para['gmail-user']], recipients=data.Email, body = "hello 1")
            return render_template('Present.html', alldata=data)

        elif (username != para['admin_user'] or userpass != para['admin_password']):
            flash("Login Failed. Password or User name incorrect", "danger")

    return render_template('pages-login.html')



@app.route("/register", methods = ['GET', 'POST'])
def register():
       
    if(request.method == 'POST'):
        Sno1 = request.form.get('sno')
        Name1 = request.form.get('name')
        Age1 = request.form.get('age')
        Email1 = request.form.get('email')
        Address1 = request.form.get('address')
        Post1 = request.form.get('position')
        Phone1= request.form.get('phone')
        
        f = request.files['photo']
        f.filename = Sno1 + '.png'
        ph = f # File rename here

        if db.session.query(Emp.Sno).filter(Emp.Sno==Sno1).count()>0:
            flash("Sno is already decleread", "danger")
        
        elif db.session.query(Emp.Sno).filter(Emp.Email==Email1).count()>0:
            flash("Email is already decleread", "danger")

        elif db.session.query(Emp.Sno).filter(Emp.Phone==Phone1).count()>0:
            flash("Phone Number is already decleread", "danger")

        #Add entry to the database
        else:
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            p = filename
            entry = Emp(Sno=Sno1, Name=Name1, Age=Age1, Email=Email1, Address=Address1, Post=Post1, Phone=Phone1, Photo=p)
            db.session.add(entry)
            db.session.commit()
                                                            ##########   Flash Error Message Section Start  ###########
    
            flash("Data Entered Successfully!", "success")

    return render_template('pages-register.html')

                                                            ##########   Flash Error Message Section Start  ###########






@app.route("/index", methods=['GET', 'POST'])
def index():
    
    if ('user' in session and session['user'] == para['admin_user']):
        #set the session variable
        rows1 = db.session.query(Emp).count()
        rows2 = db.session.query(Pres).filter(Emp.Sno==Pres.Sno).count()
        rows3 = db.session.query(Pres).filter(Emp.Sno!=Pres.Sno).count()
        data = db.session.query(Emp).join(Pres, Emp.Sno==Pres.Sno).all()
        Time = db.session.query(Pres).filter(Pres.Sno==Emp.Sno).first()
        return render_template('index.html', alldata=data, totalemp=rows1, presemp=rows2, presemp1=rows3, Time=Time)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('password')
        if (username == para['admin_user'] and userpass == para['admin_password']):
            flash("Login Successfully!", "success")
            #set the session variable
            session['user'] = username
            Times = Pres.Time
            #data = Emp.query.filter(Emp.Sno==Pres.Sno).all()
            data = db.session.query(Emp).join(Pres, Emp.Sno==Pres.Sno).all()
            return render_template('index.html', alldata=data)   

        elif (username != para['admin_user'] or userpass != para['admin_password']):
            flash("Login Failed. Password or User name incorrect", "danger")

    return render_template('pages-login.html')
    

    

@app.route("/edit/<string:Sno>", methods = ['GET', 'POST'])
def edit(Sno):
    if ('user' in session and session['user'] == para['admin_user']):
        if request.method == 'POST':
            E_Sno = request.form.get('sno')
            E_Age = request.form.get('age')
            E_Name = request.form.get('name')
            E_Email = request.form.get('email')
            E_Post = request.form.get('post')
            E_Phone = request.form.get('phone')
            E_Address = request.form.get('address')
            #E_Photo = request.form.get('photo')
            f = request.files['photo']
            f.filename = E_Sno + '.png'
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            E_Photo = filename
            
            editdata = Emp.query.filter_by(Sno=Sno).first()
            
            editdata.Sno = E_Sno
            editdata.Name = E_Name
            editdata.Age = E_Age
            editdata.Email = E_Email
            editdata.Post = E_Post
            editdata.Phone = E_Phone
            editdata.Photo = E_Photo
            editdata.Address = E_Address
            
            db.session.add(editdata)
            db.session.commit()
            flash("Update is already decleread", "Success")
            return redirect('/edit/'+Sno)
        editdata = Emp.query.filter_by(Sno=Sno).first()
        
        return render_template('editable.html', para=para, editdata=editdata)
    


@app.route("/tablesdatatable")
def databs():
    if ('user' in session and session['user'] == para['admin_user']):
        #set the session variable
        empdata = Emp(Sno=Emp.Sno, Name=Emp.Name, Email=Emp.Email, Post=Emp.Post, Phone=Emp.Phone, Photo=Emp.Photo)
        alldata = empdata.query.all()
        return render_template('tables-datatable.html', alldata=alldata)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('password')
        if (username == para['admin_user'] and userpass == para['admin_password']):
            #set the session variable
            session['user'] = username
            empdata = Emp(Sno=Emp.Sno, Name=Emp.Name, Email=Emp.Email, Post=Emp.Post, Phone=Emp.Phone, Photo=Emp.Photo)
    
            alldata = empdata.query.all()
            return render_template('tables-datatable.html', alldata=alldata)

    return render_template('pages-login.html')


    
@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/index')



@app.route("/delete/<string:Sno>", methods = ['GET', 'POST'])
def delete(Sno):
    if ('user' in session and session['user'] == para['admin_user']):
        deldata = Emp.query.filter_by(Sno=Sno).first()
        filename = Sno + '.png'
        filename = secure_filename(filename)
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        db.session.delete(deldata)
        db.session.commit()
        flash("Record is deleted", "success")
    return redirect('/tablesdatatable')



@app.route("/database")
def database():
    if ('user' in session and session['user'] == para['admin_user']):
        #set the session variable
        #session['user'] = username
        empdata = Emp(Sno=Emp.Sno, Name=Emp.Name, Email=Emp.Email, Post=Emp.Post, Phone=Emp.Phone, Photo=Emp.Photo)
    
        alldata = empdata.query.all()
        return render_template('database.html', alldata=alldata)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('password')
        if (username == para['admin_user'] and userpass == para['admin_password']):
            #set the session variable
            session['user'] = username
            empdata = Emp(Sno=Emp.Sno, Name=Emp.Name, Email=Emp.Email, Post=Emp.Post, Phone=Emp.Phone, Photo=Emp.Photo)
    
            alldata = empdata.query.all()
            return render_template('database.html', alldata=alldata)

    return render_template('pages-login.html')



@app.route("/deldata", methods = ['GET', 'POST'])
def deletedb():
    if ('user' in session and session['user'] == para['admin_user']):
        db.session.query(Pres).delete()
        db.session.commit()
    return redirect('/Present')



@app.route("/emptime", methods = ['GET', 'POST'])
def emptime():
    if ('user' in session and session['user'] == para['admin_user']):
        #set the session variable
        data = db.session.query(Pres).all()
        return render_template('timetable.html', data=data)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('password')
        if (username == para['admin_user'] and userpass == para['admin_password']):
            flash("Login Successfully!", "success")
            #set the session variable
            session['user'] = username
            data = db.session.query(Pres).all()
            return render_template('timetable.html', data=data)   

        elif (username != para['admin_user'] or userpass != para['admin_password']):
            flash("Login Failed. Password or User name incorrect", "danger")

    return render_template('pages-login.html')



if __name__=='__main__':
    app.secrect_key='secrectivekeyagain'
    app.run(debug=True, port=19000)