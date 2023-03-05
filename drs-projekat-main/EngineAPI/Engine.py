from flask import Flask, jsonify, request, json
from flask_sqlalchemy import SQLAlchemy
import jsonpickle
from datetime import datetime

engineAPI = Flask(__name__)

db = SQLAlchemy(engineAPI)
engineAPI.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bazapodataka.db'
engineAPI.config['SECRET_KEY'] = 'tajnikljuc'

class User(db.Model):
    ime = db.Column(db.String(20), nullable = False)
    prezime = db.Column(db.String(20), nullable = False)
    adresa = db.Column(db.String(50), nullable = False)
    grad = db.Column(db.String(20), nullable = False)
    drzava = db.Column(db.String(35), nullable = False)
    brojTelefona = db.Column(db.String(15), nullable = False, unique = True)
    email = db.Column(db.String(40), nullable = False, unique = True, primary_key = True)
    lozinka = db.Column(db.String(50), nullable = False)
    verifikacija = db.Column(db.Boolean, default = False)
    novac = db.Column(db.Integer, default = 0)
    valuta = db.Column(db.String(3))

class Transaction(db.Model):
    idTransakcije = db.Column(db.Integer, nullable = False, unique = True, primary_key = True)
    posiljalac = db.Column(db.String(40), nullable = False)
    primalac = db.Column(db.String(40), nullable = False)
    suma = db.Column(db.Integer, nullable = False, default = 1)
    valuta = db.Column(db.String(3))
    datumVremeTransakcije = db.Column(db.DateTime, default = datetime.utcnow)

@engineAPI.route('/addUser', methods=['POST'])
def addUser():
    new_user = User(
        ime = request.form["FirstName"],
        prezime = request.form["LastName"],
        adresa = request.form["Address"],
        grad = request.form["City"],
        drzava = request.form["State"],
        brojTelefona = request.form["PhoneNumber"],
        email = request.form["Email"],
        lozinka = request.form["Password"]
    )
    db.session.add(new_user)
    db.session.commit()
    
    return ""

@engineAPI.route('/addTransaction', methods=['POST'])
def addTransaction():
    new_transaction = Transaction(
        idTransakcije = request.form["TransactionId"],
        posiljalac = request.form["Sender"],
        primalac = request.form["Receiver"],
        suma = request.form["Sum"],
        valuta = request.form["Currency"],
        #datumVremeTransakcije = request.form["DateTime"]
    )

    postojecaTr = Transaction.query.filter_by(idTransakcije = new_transaction.idTransakcije).first()
    if postojecaTr is None:
        db.session.add(new_transaction)
        db.session.commit()
    
    return ""

@engineAPI.route('/returnUserByEmail', methods=['GET'])
def returnUserByEmail():
    email = request.args.get("Email")
    user = User.query.filter_by(email = email).first()
    
    if user:
        json_data = jsonpickle.encode(user)
        return json_data
    else:
        return ""

@engineAPI.route('/returnUser', methods=['GET'])
def returnUser():
    email = request.args.get("Email")
    password = request.args.get("Pass")
    user = User.query.filter_by(email = email, lozinka = password).first()
    
    if user:
        json_data = jsonpickle.encode(user)
        return json_data
    else:
        return ""

@engineAPI.route('/updateUser', methods=['POST'])
def updateUser():
    tmpUser = User.query.filter_by(email = request.form["email"]).first()
    tmpUser.ime = request.form["ime"]
    tmpUser.prezime = request.form["prezime"]
    tmpUser.adresa = request.form["adresa"]
    tmpUser.grad = request.form["grad"]
    tmpUser.drzava = request.form["drzava"]
    tmpUser.brojTelefona = request.form["brojTelefona"]
    tmpUser.lozinka = request.form["lozinka"]
    if request.form["verifikacija"] == "True":
        tmpUser.verifikacija = True
    else:
        tmpUser.verifikacija = False    
    #tmpUser.verifikacija = bool(request.form["verifikacija"])
    tmpUser.novac = request.form["novac"]
    tmpUser.valuta = request.form["valuta"]

    db.session.commit()

    return ""

@engineAPI.route('/returnTransactions', methods=['GET','POST'])
def returnTransactions():
    
    email = request.args.get("Email")

    user1 = Transaction.query.filter(Transaction.posiljalac == email) or Transaction.query.filter_by(primalac = email).all()
    user2 = Transaction.query.filter(Transaction.primalac == email)
    user = user1.union(user2)

    data_list = []
    for row in user:
        data_list.append({"idTransakcije": row.idTransakcije, "posiljalac": row.posiljalac, "primalac": row.primalac, "suma": row.suma, "valuta": row.valuta, "datumVremeTransakcije": row.datumVremeTransakcije})
    
    if data_list:
        json_data = jsonpickle.encode(data_list)
        return json_data
    else:
        return ""

@engineAPI.route('/returnfilterposTransactions', methods=['GET','POST'])
def returnfilterposTransactions():
    
    email = request.args.get("Email")

    user = Transaction.query.filter(Transaction.posiljalac == email).all()

    data_list = []
    for row in user:
        data_list.append({"idTransakcije": row.idTransakcije, "posiljalac": row.posiljalac, "primalac": row.primalac, "suma": row.suma, "valuta": row.valuta, "datumVremeTransakcije": row.datumVremeTransakcije})
    
    if data_list:
        json_data = jsonpickle.encode(data_list)
        return json_data
    else:
        return ""


@engineAPI.route('/returnfilterprimTransactions', methods=['GET','POST'])
def returnfilterprimTransactions():
    
    email = request.args.get("Email")

    user = Transaction.query.filter(Transaction.primalac == email).all()

    data_list = []
    for row in user:
        data_list.append({"idTransakcije": row.idTransakcije, "posiljalac": row.posiljalac, "primalac": row.primalac, "suma": row.suma, "valuta": row.valuta, "datumVremeTransakcije": row.datumVremeTransakcije})
    
    if data_list:
        json_data = jsonpickle.encode(data_list)
        return json_data
    else:
        return ""

    
   

if __name__ == "__main__":
    engineAPI.run(port=5001, debug=True, host="0.0.0.0")