from flask import Flask, redirect, render_template, request, flash, session, jsonify, url_for
import requests
import jsonpickle
import random
# importing sys
import sys
# adding Folder_2 to the system path
sys.path.insert(0, 'C:/Users/User/Desktop/DRS/EngineAPI')
from collections import OrderedDict
from operator import itemgetter

uiAPI = Flask(__name__)
ipValue = "http://Engine:5001/"
#url = "https://apilayer.com/exchange?access_key=BE4jgK3YRW4H7wAIju9crG5gB539fkYa&base="
uiAPI.config['SECRET_KEY'] = "uitajnikljuc"



@uiAPI.route("/")
def index():
    user_data = get_session_user()
    valute = {}
    if user_data:
        if user_data["valuta"] is None:
            valute = getCurrencies('RSD')
        else:
            valute = getCurrencies(user_data["valuta"])
    else:
        valute = getCurrencies('RSD')

    set_session_cur(valute)

    return render_template('home.html', user_data = user_data, valute=valute)

@uiAPI.route('/login', methods=['GET', 'POST'])
def login():
    email = request.form["login_email"]
    password = request.form["login_password"]

    loginCheckRaw = requests.get(ipValue + "returnUser?Email=" + email + "&Pass=" + password)
    if loginCheckRaw.content:
        user_data = jsonpickle.decode(loginCheckRaw.content)
    else:
        user_data = dict()

    if user_data:
        set_session_user(user_data)
        return redirect(url_for('index'))
    else:
        flash("Pogresni email ili loznka. Ako niste, ulogujte se ")
        return render_template("login.html")

@uiAPI.route('/logout', methods=['GET', 'POST'])
def logout():
    pop_session_user()
    return redirect(url_for('index'))

@uiAPI.route('/register', methods=['GET', 'POST'])
def register():
    firstName = request.form["register_firstname"]
    surname = request.form["register_surname"]
    address = request.form["register_address"]
    city = request.form["register_city"]
    state = request.form["register_state"]
    tel = request.form["register_tel"]
    email = request.form["register_email"]
    password = request.form["register_password"]

    rawResponse = requests.get(ipValue + "returnUserByEmail?Email="+ email)

    if rawResponse.content:
        user= jsonpickle.decode(rawResponse.content)
    else:
        user = dict()

    if user:
        if user["email"] == email:
            flash("Vec postoji korisnik sa tom email adresom.")
            return render_template("register.html")
        else:
            flash("There was an error!")
            return render_template("register.html")
    else:
        User = {
            "FirstName" :  firstName,
            "LastName" :  surname,
            "Address" :  address,
            "City" :  city,
            "State" :  state,
            "PhoneNumber" :  tel,
            "Email" :  email,
            "Password" :  password,
        }

        requests.post(ipValue + "addUser", User)

    return redirect(url_for('index'))

@uiAPI.route('/payment', methods=['POST', 'GET'])
def payment():
    user_data = get_session_user()
    trId = random.randint(0, 99999)

    Transaction = {
        "TransactionId" : trId,
        "Sender" : request.form["br-kartice"],
        "Receiver" : user_data["email"],
        "Sum" : request.form["suma"],
        "Currency" : 'RSD',
    }

    suma = float(request.form["suma"])
    novac = float(user_data["novac"])

    if user_data["valuta"] == "RSD":
        novac += suma
    elif user_data["valuta"] is None:
        novac += suma
        user_data["valuta"] = "RSD"
        user_data["verifikacija"] = "True"
        kursna_lista = getCurrencies("RSD")
        novac -= 1 * kursna_lista['USD']
    else:
        kursna_lista = getCurrencies("RSD")
        for cur in kursna_lista.keys():
            if cur == user_data["valuta"]:
                novac += suma / kursna_lista[cur]

    user_data["novac"] = round(novac, 3)
    rawResponseTransactionAdd = requests.post(ipValue + "addTransaction", Transaction)
    
    if rawResponseTransactionAdd.status_code == 200:
        rawResponseUserUpdate = requests.post(ipValue + "updateUser", user_data)
        if rawResponseUserUpdate.status_code == 200:
            set_session_user(user_data)
        else:
            flash("Neuspela izmena stanja korisnika")
            user_data = get_session_user()
            return render_template("payment.html", user_data=user_data)
    else:
        flash("Neuspela transakcija")
        user_data = get_session_user()
        return render_template("payment.html", user_data=user_data)

    return redirect(url_for('index'))

@uiAPI.route('/update', methods=['POST', 'GET'])
def update():
    user_data = get_session_user()

    user_data["ime"] = request.form["first-name"]
    user_data["prezime"] = request.form["last-name"]
    user_data["adresa"] = request.form["address"]
    user_data["grad"] = request.form["city"]
    user_data["drzava"] = request.form["country"]
    user_data["brojTelefona"] = request.form["phone-number"]
    user_data["lozinka"] = request.form["password"]

    rawResponse = requests.post(ipValue + "updateUser", user_data)
    #set_session_user(user_data)

    if rawResponse.status_code == 200:
        set_session_user(user_data)
        return redirect(url_for('index'))
    else:
        flash("Nisam uspeo da izmenim korisnicke podatke.")
        user_data = get_session_user()
        return render_template('update.html', user_data = user_data)

@uiAPI.route('/convert', methods=['GET', 'POST'])
def convert():
    sign = request.args.get('sign')
    value = float(request.args.get('value'))

    user_data = get_session_user()
    novac = float(user_data["novac"])

    user_data["valuta"] = sign

    novac /= value

    user_data["novac"] = round(novac, 3)
    set_session_user(user_data)
    requests.post(ipValue + "updateUser", user_data)

    return redirect(url_for('index'))

@uiAPI.route('/transactionByEmail', methods=['GET', 'POST'])
def transactionByEmail():
    kursna_lista = get_session_cur()
    posiljalac = get_session_user()
    sumaZaSlanje = float(request.form["suma"])
    nazivValute = request.form["valuta"]
    emailPrim = request.form["email_primaoca"]
    #valutaZaSlanje = kursna_lista[nazivValute]

    primalac = {}

    rawResponse = requests.get(ipValue + "returnUserByEmail?Email=" + emailPrim)

    if rawResponse.content:
        primalac = jsonpickle.decode(rawResponse.content)
    else:
        flash("Ne postoji korisnik sa tim email-om! Pokusajte sa nekim drugim")
        return render_template("transaction.html", cur = kursna_lista)


    posNovac = float(posiljalac["novac"])
    primNovac = float(primalac["novac"])

    posNovac = posNovac - sumaZaSlanje * kursna_lista[nazivValute]

    if posNovac < 0:
        flash("Nemate toliko novca na racunu")
        return render_template("transaction.html", cur = kursna_lista)
    
    kursna_lista = getCurrencies(nazivValute)

    primNovac = primNovac + sumaZaSlanje / kursna_lista[primalac["valuta"]]

    posiljalac["novac"] = round(posNovac, 4)
    primalac["novac"] = round(primNovac, 4)

    rawResponsePos = requests.post(ipValue + "updateUser", posiljalac)
    rawResponsePrim = requests.post(ipValue + "updateUser", primalac)

    if rawResponsePrim.status_code == rawResponsePos.status_code == 200:
        set_session_user(posiljalac)
        trId = trId = random.randint(0, 99999)
        Transaction = {
        "TransactionId" : trId,
        "Sender" : posiljalac["email"],
        "Receiver" : primalac["email"],
        "Sum" : sumaZaSlanje,
        "Currency" : nazivValute,
        }
        rawResponseTransactionAdd = requests.post(ipValue + "addTransaction", Transaction)
        if rawResponseTransactionAdd.status_code == 200:
            return redirect(url_for('index'))
        else:
            flash("Nisam uspeo da sacuvam transakciju")
            return render_template("transaction.html", cur = kursna_lista)
    else:
        flash("Nisam uspeo da sacuvam korisnicke izmene, neuspela transakcija")
        return render_template("transaction.html", cur = kursna_lista)

@uiAPI.route('/transactionToNonRegistered', methods=['GET', 'POST'])
def transactionToNonRegistered():
    posiljalac = get_session_user()
    sumaZaSlanje = float(request.form["suma"])
    nazivValute = request.form["valuta"]
    brRacunaPrim = request.form["broj-racuna"]
    adresaPrim = request.form["adresa"]
    imePrezimePrimaoca = request.form["ime-prezime"]

    stanje = float(posiljalac["novac"])

    kursna_lista = get_session_cur()

    stanje = stanje - sumaZaSlanje * kursna_lista[nazivValute]

    if stanje < 0:
        flash("Nemate toliko novca na racunu")
        return render_template("transaction.html", cur = kursna_lista)

    posiljalac["novac"] = round(stanje, 4)

    rawResponsePos = requests.post(ipValue + "updateUser", posiljalac)

    if rawResponsePos.status_code == 200:
        set_session_user(posiljalac)
        trId = trId = random.randint(0, 99999)
        Transaction = {
        "TransactionId" : trId,
        "Sender" : posiljalac["email"],
        "Receiver" : brRacunaPrim,
        "Sum" : sumaZaSlanje,
        "Currency" : nazivValute,
        }
        rawResponseTransactionAdd = requests.post(ipValue + "addTransaction", Transaction)
        if rawResponseTransactionAdd.status_code == 200:
            return redirect(url_for('index'))
        else:
            flash("Nisam uspeo da sacuvam transakciju")
            redirect(url_for('transactionPage'))
    else:
        flash("Nisam uspeo da sacuvam korisnicke izmene, neuspela transakcija")
        redirect(url_for('transactionPage'))


@uiAPI.route('/getTransactions', methods=['POST','GET'])
def getTransactions():
    posiljalac = get_session_user()
    email = posiljalac["email"]

    transactions = {}

    try:
        rawResponse = requests.post(ipValue + "returnTransactions?Email=" + email)
    except:
        flash("Ne postoji korisnik sa tim email-om! Pokusajte sa nekim drugim")

    transactions = jsonpickle.decode(rawResponse.content)


    if  rawResponse.status_code == 200:
        return render_template('transaction1.html', transactions = transactions)
    else:
        flash("Nisam uspeo da ucitam istoriju transakcija")
        redirect(url_for('transactionPage'))


@uiAPI.route('/getPosiljalac', methods=['POST','GET'])
def getPosiljalac():
    posiljalac = get_session_user()
    email = posiljalac["email"]

    transactions = {}

    try:
        rawResponse = requests.post(ipValue + "returnfilterposTransactions?Email=" + email)
    except:
        flash("Ne postoji korisnik sa tim email-om! Pokusajte sa nekim drugim")

    transactions = jsonpickle.decode(rawResponse.content)


    if  rawResponse.status_code == 200:
        return render_template('transaction2.html', transactions = transactions)
    else:
       flash("Nisam uspeo da ucitam istoriju transakcija")
       redirect(url_for('transactionPage'))

@uiAPI.route('/getPrimalac', methods=['POST','GET'])
def getPrimalac():
    posiljalac = get_session_user()
    email = posiljalac["email"]

    transactions = {}

    try:
        rawResponse = requests.post(ipValue + "returnfilterprimTransactions?Email=" + email)
    except:
        flash("Ne postoji korisnik sa tim email-om! Pokusajte sa nekim drugim")

    transactions = jsonpickle.decode(rawResponse.content)


    if  rawResponse.status_code == 200:
        return render_template('transaction2.html', transactions = transactions)
    else:
       flash("Nisam uspeo da ucitam istoriju transakcija")
       redirect(url_for('transactionPage'))



@uiAPI.route('/sortTransaction', methods=['POST','GET'])
def sortTransaction():
    posiljalac = get_session_user()
    email = posiljalac["email"]
    sort = request.args.get("Sort")

    transactions = {}

    try:
        rawResponse = requests.post(ipValue + "returnTransactions?Email=" + email)
    except:
        flash("Ne postoji korisnik sa tim email-om! Pokusajte sa nekim drugim")

    transactions = jsonpickle.decode(rawResponse.content)


    if(sort == 'RASTUCEID'):
        transactions = sorted(transactions, key = itemgetter('idTransakcije'))
    elif(sort == 'OPADAJUCEID'):
        transactions = sorted(transactions, key = itemgetter('idTransakcije'),reverse=True)
    elif(sort == 'RASTUCEPOS'):
        transactions = sorted(transactions, key = itemgetter('posiljalac'))
    elif(sort == 'OPADAJUCEPOS'):
        transactions = sorted(transactions, key = itemgetter('posiljalac'),reverse=True)
    elif(sort == 'RASTUCEPRIM'):
        transactions = sorted(transactions, key = itemgetter('primalac'))
    elif(sort == 'OPADAJUCEPRIM'):
        transactions = sorted(transactions, key = itemgetter('primalac'),reverse=True)
    elif(sort == 'RASTUCESUMA'):
        transactions = sorted(transactions, key = itemgetter('suma'))
    elif(sort == 'OPADAJUCESUMA'):
        transactions = sorted(transactions, key = itemgetter('suma'),reverse=True)
    elif(sort == 'RASTUCEVALUTA'):
        transactions = sorted(transactions, key = itemgetter('valuta'))
    elif(sort == 'OPADAJUCEVALUTA'):
        transactions = sorted(transactions, key = itemgetter('valuta'),reverse=True)
    elif(sort == 'RASTUCEDATUM'):
        transactions = sorted(transactions, key = itemgetter('datumVremeTransakcije'))
    elif(sort == 'OPADAJUCEDATUM'):
        transactions = sorted(transactions, key = itemgetter('datumVremeTransakcije'),reverse=True)


    if  rawResponse.status_code == 200:
        return render_template('transaction1.html', transactions = transactions)
    else:
       flash("Nisam uspeo da sortiram istoriju transakcija")
       redirect(url_for('transactionPage'))


@uiAPI.route('/loginPage', methods=['GET', 'POST'])
def loginPage():
    return render_template("login.html")

@uiAPI.route('/registerPage', methods=['GET', 'POST'])
def registerPage():
    return render_template('register.html')

@uiAPI.route('/updatePage', methods=['GET', 'POST'])
def updatePage():
    user_data = get_session_user()
    return render_template('update.html', user_data = user_data)

@uiAPI.route('/paymentPage', methods=['GET', 'POST'])
def paymentPage():
    #prviPut = request.args.get('first')
    user_data = get_session_user()
    return render_template('payment.html', user_data = user_data)

@uiAPI.route('/transactionPage', methods=['GET', 'POST'])
def transactionPage():
    cur = get_session_cur()
    user_data = get_session_user()
    return render_template('transaction.html', cur=cur, user_data=user_data)

def set_session_user(user):
    session["user_data"] = user
    return True

def get_session_user():
    user_data = session.get("user_data", {})
    return user_data

def set_session_cur(cur):
    session["cur"] = cur
    return True

def get_session_cur():
    cur = session.get("cur", {})
    return cur

def pop_session_user():
    session.clear()
    return True

def getCurrencies(base : str):
    symbols = "RSD%2CEUR%2CUSD%2CJPY%2CGBP%2CAUD%2CCAD%2CCHF%2CRUB%2CCHN%2CHUF%2CBAM%2CBGN%2CMKD%2CRON"
    url = "https://api.apilayer.com/fixer/latest?symbols=" + symbols + "&base=" + base

    payload = {}
    headers= {
        "apikey": "4781KVGn2zVb740IxAs11L9brWUfg72z"
    }

    try:
        response = requests.request("GET", url, headers=headers, data=payload)
    #sc = response.status_code
    except:
        print("Nisam uspeo da nabavim kursnu listu")
    response_json = response.json()
    
    exchange_rates = response_json['rates']

    #currencies_data = {key: value for key, value in exchange_rates.items()}
    for key, value in exchange_rates.items():
        #currency_dict[key] = 1 / value
        tmpval = value and (1 / value)
        exchange_rates[key] = round(tmpval, 5)

    return exchange_rates

if __name__ == "__main__":
    uiAPI.run(port=5000, debug=True, host="0.0.0.0")

    