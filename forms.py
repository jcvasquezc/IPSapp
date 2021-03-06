#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  12 14:44:02 2017

@author: gita
"""

from flask import Flask, render_template, flash, request, redirect,url_for, make_response, abort, Response
from flask_login import LoginManager, login_required, login_user,logout_user,UserMixin, current_user
from pymongo import MongoClient, ASCENDING #Manejos de base de datos
import pandas as pd
import numpy as np
import os
import json
import time
import read_mod
import plot_map
import plotly
#from werkzeug.utils import secure_filename
import hashlib
#from utils import send_email
from urllib.parse import urlparse, urljoin
#Newlibs
import string
import random

#Directorio de proyecto
main_path = os.path.dirname(os.path.abspath(__file__))

# App config.
DEBUG = True
#LOGIN_DISABLED = True #Solo habilitar para pruebas.
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'
#Carpeta para adjuntar archivos
UPLOAD_FOLDER = main_path+'/uploads'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Manejo de usuarios
login_manager = LoginManager()
login_manager.init_app(app)#Configurar app para login
login_manager.login_view = "Ingresar" #ir a esta html cuando se requiera el login


#Base de datos
#Crear cliente
try:
    client = MongoClient()
    #Crear database
    db = client.IPS_database
    #client.drop_database('IPS_database')

    #Crear colección
    IPS_data  = db.IPS_collection
    Users_data = db.Users_collection
    Temp_data = db.Temp_collection
except:
    print('')

usertag = "usuario"

db_files = os.listdir('./BD')
db_files.sort()

#Info general IPS
IPS = pd.read_excel('./BD/'+db_files[0])

#LAT, LON
dfpmap = pd.read_csv('./pos_col.csv')

##Delete collection
#db.Index_collection.drop()

#Crear indice basado en NIT
#db.Index_collection.create_index([('NIT', pymongo.ASCENDING)],unique=True)

#######################################################
#######################################################
#######################################################
#Usuario para login
class User(UserMixin):
    def __init__(self,usr_id):
        self.id = usr_id

    def __repr__(self):
        return '<User {}>'.format(self.usr_id)

#Cargar usuarios
try:
    users=[]
    for docs in Users_data.find():
        usr_id=docs["user_id"]
        users.append(User(usr_id))
except:
    print('')

@login_manager.user_loader
def load_user(usr_id):
    return User(usr_id)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
#######################################################
#######################################################
#######################################################
#safe redirect
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target

def redirect_back(endpoint, **values):
    target = request.form['next']
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)
#######################################################
#######################################################
#######################################################

#Obtener listas de departamentos y ciudades
def set_dptos():
    #Obtener lista de departamento y ciudades
    lista_dptos = pd.read_csv(main_path+'/static/pos_col.csv')
    #Obtener departamentos
    df = pd.DataFrame(lista_dptos)
    del  df['lat']
    del  df['lon']
    del  df['ID']
    del  df['ID2']
    df = df.dropna()
    dptos = list(np.unique(df['Departamento']))
    #Crear diccionario de ciudades
    cities = {}
    for idx in dptos:
        cities[idx.upper()] = list(np.unique(df[df['Departamento']==idx]['Municipio']))

    #Set DEPARTAMENTOS to UPPERCASE
    idx = 0
    for d in dptos:
        dptos[idx]=d.upper()
        idx = idx+1
    return dptos,cities

#Obtener codigos de departamentos y municipios
def set_cod(dpto,city):
    #Obtener lista de departamento y ciudades
    lista_dptos = pd.read_csv(main_path+'/static/pos_col.csv')
    #Obtener departamentos
    df = pd.DataFrame(lista_dptos)
    del  df['lat']
    del  df['lon']
#    del  df['ID']
#    del  df['ID2']
    df = df.dropna()
    dptos = list(np.unique(df['Departamento']))

    codes_dpto = {}
    for idx in dptos:
        codes_dpto[idx.upper()] = list(np.unique(df[df['Departamento']==idx]['ID2']))[0]

    cod_dpto = codes_dpto[dpto]
    city_list = df[df['Municipio']==city]
#    print(city_list)
    cod_city = list(city_list[city_list['ID2']==cod_dpto]['ID'])[0]
    return str(cod_dpto),str(cod_city)
##############################################
##############################################
#Extensiones permitidas
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def progreso_mod(ips):
    div=[93,25,19,3,3,5]

    if "question3" in ips["Resultados Modulo 5"].keys():
        if ips["Resultados Modulo 5"]["question3"][0]=="SI":
            div[4]=4

    if "question21" in ips["Resultados Modulo 2"].keys():
        if ips["Resultados Modulo 2"]["question21"][0]=="SI":
            div[1]=div[1]+8

    if "question26" in ips["Resultados Modulo 2"].keys():
        if ips["Resultados Modulo 2"]["question26"][0]=="SI":
            div[1]=div[1]+2

    if "question12" in ips["Resultados Modulo 3"].keys():
        if ips["Resultados Modulo 3"]["question12"][0]=="SI":
            div[2]=div[2]+10

    if "question6" in ips["Resultados Modulo 3"].keys():
        if ips["Resultados Modulo 3"]["question6"][0]=="NO":
            div[2]=div[2]-1

    if "question26" in ips["Resultados Modulo 3"].keys():
        if ips["Resultados Modulo 3"]["question26"][0]=="NO":
            div[2]=div[2]-1

    if "question1_int" in ips["Resultados Modulo 3"].keys():
        if ips["Resultados Modulo 3"]["question1_int"][0]=="NO":
            div[2]=div[2]-1



    if "question23bTOP" in ips["Resultados Modulo 3"].keys():
        div[2]=div[2]+4

    if "question23cTOP" in ips["Resultados Modulo 3"].keys():
        div[2]=div[2]+15

    if "question23dTOP" in ips["Resultados Modulo 3"].keys():
        div[2]=div[2]+6

    if "question23fTOP" in ips["Resultados Modulo 3"].keys():
        div[2]=div[2]+2

    if "question23gTOP" in ips["Resultados Modulo 3"].keys():
        div[2]=div[2]+23

    if "question23hTOP" in ips["Resultados Modulo 3"].keys():
        div[2]=div[2]+2

    if "question23iTOP" in ips["Resultados Modulo 3"].keys():
        div[2]=div[2]+8

    perc_mod = []
    for idxmod in range(1,7):
        rtas = ips["Resultados Modulo "+str(idxmod)]
        cont = 0 #Contar respuestas
        for idx in rtas.keys():
            if "INGP" not in idx:
                cont = cont+1

        calc = int(100*(cont-1)/div[idxmod-1])#cont-1 por la etiqueta "ID"
        perc_mod.append(calc)


#    perc_mod=[int(100*(len(Resultados_mod1)-1)/div[0]), int(100*(len(Resultados_mod2)-1)/div[1]), int(100*(len(Resultados_mod3)-1)/div[2]), int(100*(len(Resultados_mod4)-1)/div[3]), int(100*(len(Resultados_mod5)-1)/div[4]), int(100*(len(Resultados_mod6)-1)/div[5])]

    perc_mod=np.asarray(perc_mod)
    find0=np.asarray(np.where(np.asarray(perc_mod)<0)[0])

    perc_mod[find0]=0
    find100=np.asarray(np.where(np.asarray(perc_mod)>100)[0])

    perc_mod[find100]=100

    if len(ips["Resultados Modulo 6"])>1:
        if ips["Resultados Modulo 6"]["question1"][0].find("NO")>=0:
            perc_mod[5]=100

    return perc_mod
#def new_user(nit):
#    # Creates a new user for the company passed into the function if it doesn't already exist. se
#    import hashlib
#    user_data = {}
#    user_data['username'] =  input("Please enter your desired username: ").lower()
#    while user_exists(company.upper(), user_data['username']):
#        user_data['username'] = input("Username already exist. Please try a different username: ").lower()
#    password = input("Please enter a password: ")
#    user_data['password'] = hash_pass(password)
#    user_data['email'] = input("Please enter your email address: ")
#    update_result = update_mongo_document(company.upper(), 'user', '$push', user_data)
#
####################################
#Codificar contrasenna
def hash_pass(password,salt):
    salt_hash = hashlib.blake2b(salt=salt)
    salt_hash.update(password.encode('utf-8'))
    hash_password = salt_hash.digest()
    return hash_password
########################################################
#New password
def new_pass(password):
    salt = os.urandom(hashlib.blake2b.SALT_SIZE)
    salt_hash = hashlib.blake2b(salt=salt)
    salt_hash.update(password.encode('utf-8'))
    hash_password = salt_hash.digest()
    return hash_password,salt

def pass_generator(size=8, chars=string.ascii_uppercase + string.digits):
   return ''.join(random.choice(chars) for x in range(size))
########################################################
#Verificar credenciales
def get_credentials(usr,userpass):
    temp = Users_data.find({"usuario":usr}).count()
#    print(temp)
    if temp == 0:
        return False
    else:
        results = Users_data.find({"usuario":usr})[0]
#        print(userpass)
#        print(results['password_nc'])
        if hash_pass(userpass,results['salt']) == results['password']:
            return True
        return False
######################################################
@app.route("/", methods=['GET', 'POST'])
def index():
    LogFlag = "False"
    if current_user.is_active==True:
        LogFlag = "True"
#    dptos,cities = set_dptos()
    if request.method == 'POST':
        return redirect(url_for('index'))
#    return render_template('index.html', **{"dptos":dptos},cities=json.dumps(cities))

    return render_template('index.html',LogFlag=json.dumps(LogFlag))

@app.route("/instructivo", methods=['GET', 'POST'])
def instructivo():
    LogFlag = "False"
    if current_user.is_active==True:
        LogFlag = "True"
#    dptos,cities = set_dptos()
    if request.method == 'POST':
        return redirect(url_for('instructivo'))
#    return render_template('index.html', **{"dptos":dptos},cities=json.dumps(cities))

    return render_template('instructivo.html',LogFlag=json.dumps(LogFlag))

@app.route("/faqs", methods=['GET', 'POST'])
def faqs():
    LogFlag = "False"
    if current_user.is_active==True:
        LogFlag = "True"
#    dptos,cities = set_dptos()
    if request.method == 'POST':
        return redirect(url_for('faqs'))
#    return render_template('index.html', **{"dptos":dptos},cities=json.dumps(cities))

    return render_template('faqs.html',LogFlag=json.dumps(LogFlag))

@app.route("/contacto", methods=['GET', 'POST'])
def contacto():
    LogFlag = "False"
    if current_user.is_active==True:
        LogFlag = "True"
#    dptos,cities = set_dptos()
    if request.method == 'POST':
        return redirect(url_for('contacto'))
#    return render_template('index.html', **{"dptos":dptos},cities=json.dumps(cities))

    return render_template('contacto.html',LogFlag=json.dumps(LogFlag))

@app.route("/mapa", methods=['GET', 'POST'])
def mapa():
    loghid = 'true' #Agregar atributo de invicible de la tabla
    if request.method == 'POST':
        loghid = 'false'#Quitar atributo de invicible de la tabla
        opt = request.form['plots']
        if opt=='mgral':#Mapas genrales (tipo de rta: SI/NO)
            sttmod = request.form['sel_mgral']
            clr_rta = 'sval'#Lista de colores. 
        else:#Mapas genrales (tipo de rta: varias opciones, unica respuesta)
            sttmod = request.form['sel_mesp']
            clr_rta = 'mval'
            
        maptxt,ans_unique,tab_resp_sort,tab_total = read_mod.mapa_gral(sttmod,db_files,IPS,dfpmap,clr_rta)
        return render_template('mapa.html',maptxt=maptxt, **{"tab_rtas":tab_resp_sort,"tab_total":tab_total}, ans=ans_unique,loghid=loghid)
    return render_template('mapa.html',loghid=loghid)

###################################################3##
@app.route("/Ingresar", methods=['GET', 'POST'])
def Ingresar():
#    next = get_redirect_target()
    LogFlag = "False"
    if request.method == 'POST':
        if current_user.is_active==True:
            LogFlag = "True"
        username = request.form['usrlog']
        userpass = request.form['passlog']
        credentials = get_credentials(username,userpass)
        error = ''
        #Verificarcontrasennas
        if credentials:
            user_id = Users_data.find({"usuario":username})[0]['user_id']
            user = User(user_id)
            login_user(user)
#            if not is_safe_url(next):
#                return abort(400)

            return redirect(url_for('modulos',LogFlag=json.dumps(LogFlag)))
#            return render_template('modulos.html')
        else:
            error = ' (Usuario o Contraseña incorrecto)'
            return render_template('Ingresar.html',error=error,LogFlag=json.dumps(LogFlag))
    return render_template('Ingresar.html',LogFlag=json.dumps(LogFlag))
#####################################################
@app.route("/redirec", methods=['GET', 'POST'])
def redirec():
    next = get_redirect_target()
    LogFlag = "False"
    if request.method == 'POST':
        if current_user.is_active==True:
            LogFlag = "True"
        username = request.form['usrlog']
        userpass = request.form['passlog']
        credentials = get_credentials(username,userpass)
        error = ''
        #Verificarcontrasennas
        if credentials:
            user_id = Users_data.find({"usuario":username})[0]['user_id']
            user = User(user_id)
            login_user(user)
#            if not is_safe_url(next):
#                return abort(400)

            return redirect(next or url_for('index',LogFlag=json.dumps(LogFlag)))
#            return render_template('modulos.html')
        else:
            error = ' (Usuario o Contraseña incorrecto)'
            return render_template('Ingresar.html',error=error,LogFlag=json.dumps(LogFlag))
    return render_template('Ingresar.html',next=next,LogFlag=json.dumps(LogFlag))
######################################################
@app.route("/registro", methods=['GET', 'POST'])
@login_required
def registro():
    dptos,cities = set_dptos()
    #Current User
    usr_id = int(current_user.id)
    usrid = Users_data.find({"user_id":usr_id})[0]

    #Select colab
    if (usrid['role']!='manager'):
        return redirect(url_for('index'))

    IPSdata = IPS_data.find({"ID":usrid['ID']})[0]
    IPSdata.pop('_id', None)#JSON CANT SERIALIZED ObjectID

    if request.method == 'POST':
        #Datos prestador
        nombreIPS = request.form['reg_ips']#Nombre del prestador
        nit = request.form['reg_nit']#Nit del prestador
#        Nsed = request.form['reg_numsede']#Numero de sedes
        codhab = request.form['reg_hab']#NCdigo habilitacion
        naju = request.form['reg_natjur']#Naturaleza juridica
        clpr = request.form['reg_clase']#Clase de prestador
        niv = request.form['reg_nivel']#Nivel del prestador
        dptoP = request.form['reg_dptoP']#Departamento del prestador
        cod_dpto = request.form['reg_coddpto']#Departamento del prestador
        cod_city = request.form['reg_codcity']#Municipio del prestador
        cityP = request.form['reg_cityP']#Municipio del prestador
        userenc = request.form['reg_manag']#nombre del encargado
        mailenc = request.form['reg_manmail']#email del encargado
        telenc = request.form['reg_mantel']#Telefono del encargado
        IPS_reg_data = {
                  "Código Habilitación":codhab,
                  "Validar INFO":True,
                  "Código Municipio":cod_city,
                  "Código Departamento":cod_dpto,
                  "Departamento":dptoP,
                  "Encargado de Encuesta":userenc,
                  "E-mail del Encargado":mailenc,
                  "Teléfono del Encargado":telenc,
                  "Municipio":cityP,
                  "Nivel del Prestador":niv,
                  "Naturaleza Jurídica":naju,
                  "Clase de Prestador":clpr,
                  "Nombre del Prestador":nombreIPS,
                  "NIT":nit,
#                  "Número de sede":Nsed,
                  }
        #print(IPS_reg_data)
        usr_id = int(current_user.id)
        ID = Users_data.find({"user_id":usr_id})[0]['user_id']
        temp = IPS_data.find({"ID":ID}).count()
        if temp!=0:
            IPS_data.update_one({"ID":ID},{"$set":IPS_reg_data})
        else:
            IPS_data.insert_one(IPS_reg_data).inserted_id

        return redirect(url_for('modulos'))

    return render_template('registro.html',**{"dptos":dptos},cities=json.dumps(cities),IPSdata=json.dumps(dict(IPSdata)))
######################################################
@app.route("/registro_admin", methods=['GET', 'POST'])
@login_required
def registro_admin():
    dptos,cities = set_dptos()
    #Current User
    usr_id = int(current_user.id)
    usrid = Users_data.find({"user_id":usr_id})[0]

    #Select colab
    if (usrid['role']!='admin'):
        return redirect(url_for('index'))
    if request.method == 'POST':
        #Datos prestador
        nombreIPS = request.form['reg_ips']#Nombre del prestador
#        nit = request.form['reg_nit']#Nit del prestador
#        Nsed = request.form['reg_numsede']#Numero de sedes
        codhab = request.form['reg_hab']#NCdigo habilitacion
#        naju = request.form['reg_natjur']#Naturaleza juridica
#        clpr = request.form['reg_clase']#Clase de prestador
#        niv = request.form['reg_nivel']#Nivel del prestador
        dptoP = request.form['reg_dptoP']#Departamento del prestador
#        cod_dpto = request.form['reg_coddpto']#Departamento del prestador
#        cod_city = request.form['reg_codcity']#Municipio del prestador
        cityP = request.form['reg_cityP']#Municipio del prestador
        userenc = request.form['reg_manag']#nombre del encargado
        mailenc = request.form['reg_manmail']#email del encargado
        telenc = request.form['reg_mantel']#Telefono del encargado
#        ext = request.form['reg_mantelExt']#Telefono del encargado
#        ger = request.form['reg_gerente']
#        dirips = request.form['reg_direccion']
#        barips = request.form['reg_barrio']
#        telips = request.form['reg_ipstel']
#        emailips = request.form['reg_ipsemail']
        cod_dpto,cod_city = set_cod(dptoP,cityP)
        numID = []
        for docs in IPS_data.find():
              numID.append(int(docs['Número de sede']))
        numID.sort(reverse=True)
        numID = numID[0]+1

        IPS_reg_data = {
                  "Gerente":'',
                  "Dirección":'',
                  "Barrio":'',
                  "Teléfono":'',
                  "E-mail empresarial":'',
                  "Código Habilitación":codhab,
                  "Código Municipio":cod_city,
                  "Código Departamento":cod_dpto,
                  "Departamento":dptoP,
                  "Encargado de Encuesta":userenc,
                  "E-mail del Encargado":mailenc,
                  "Teléfono del Encargado":telenc,
                  "Extensión del Encargado":'',
                  "Municipio":cityP,
                  "Razón social":nombreIPS,
                  "Representante legal":'',
#                  "Nivel del Prestador":niv,
#                  "Naturaleza Jurídica":naju,
#                  "Clase de Prestador":clpr,
                  "Nombre del Prestador":nombreIPS,
                  "NIT":'',
                  "ID":int(str(codhab+str(numID))),
                  "Número de sede":str(numID),
                  "Resultados Modulo 1":{},
                  "Resultados Modulo 2":{},
                  "Resultados Modulo 3":{},
                  "Resultados Modulo 4":{},
                  "Resultados Modulo 5":{},
                  "Resultados Modulo 6":{},
                  "valmod1":False,
                  "Validar INFO":False
                  }


        userpass = pass_generator()
        hpassw,salt = new_pass(userpass)
        username = 'saludcol'+str(numID)
        Users_IPS = {
                     usertag:username,
                     "password":hpassw,
                     "salt":salt,
                     "Codigo":codhab,
                     'role':'manager',
                     'ID':int(str(codhab+str(numID))),#toco :(
                     'user_id':int(str(codhab+str(numID)))
                     }

        Users_data.insert_one(Users_IPS)
        IPS_data.insert_one(IPS_reg_data)

        INFO = {
             'usr':username,
             'pw':userpass,
             'cod':codhab,
             'ips':nombreIPS,
             "dpto":dptoP,
             "cod_dpto":cod_dpto,
             "cod_city":cod_city,
             "muni":cityP,
             "enc":userenc,
             "email":mailenc,
             "tel":telenc}
        ct = Temp_data.find().count()
        if ct>0:
               Temp_data.remove({})
        Temp_data.insert_one(INFO)
        return redirect(url_for('confirm_reg'))
    return render_template('registro_admin.html',**{"dptos":dptos},cities=json.dumps(cities))
######################################################
@app.route("/confirm_reg", methods=['GET', 'POST'])
@login_required
def confirm_reg():
     INFO = Temp_data.find()[0]
     if request.method == 'POST':
        Temp_data.remove({})
        return render_template('confirm_reg.html')
     return render_template('confirm_reg.html',**{"INFO":INFO})


######################################################
@app.route("/modulos", methods=['GET', 'POST'])
@login_required
def modulos():
#    dptos,cities = set_dptos()
    #Verificar si es necesario registrar
    usr_id = int(current_user.id)
    usrid = Users_data.find({"user_id":usr_id})[0]
    #Select colab
    if (usrid['role']=='admin'):
        return redirect(url_for('admin'))
    elif (usrid['role']=='gob'):
        return redirect(url_for('admin'))
    elif (usrid['role']!='manager'):
        return redirect(url_for('index'))

    IPSdata = IPS_data.find({"ID":usrid['user_id']})[0]
    perc_mod = progreso_mod(IPSdata)


    if request.method == 'POST':
#        colabs = {}
#        Ncolabs = 6 #Numero maximo de colaboradores
#        for idx in range(1,Ncolabs+1):
#            colabs['nombre'+str(idx)] = request.form['nombre'+str(idx)]
#            colabs['email'+str(idx)] = request.form['email'+str(idx)]
#            colabs['cargo'+str(idx)] = request.form['cargo'+str(idx)]
#
#        usr_id = current_user.id
#        usr =   Users_data.find({'user_id': int(usr_id)})[0]
#        temp = IPS_data.find({"ID":usr['user_id']})
#        Ntemp=temp.count()
#        if Ntemp!=0:
#            for idx in range(1,Ncolabs+1):
#                IPS_data.find_and_modify(query={'ID':usr['user_id']}, update={"$set": {'colaborador'+str(idx)+' nombre': colabs['nombre'+str(idx)]}}, upsert=False, full_response= True)
#                IPS_data.find_and_modify(query={'ID':usr['user_id']}, update={"$set": {'colaborador'+str(idx)+' cargo': colabs['cargo'+str(idx)]}}, upsert=False, full_response= True)
#                IPS_data.find_and_modify(query={'ID':usr['user_id']}, update={"$set": {'colaborador'+str(idx)+' email': colabs['email'+str(idx)]}}, upsert=False, full_response= True)

        return redirect(url_for('modulos'))
#        return render_template('modulos.html',userid=IPS_data.find({"ID":usrid['ID']})[0]['ID'], message=["","","","","",""])

    return render_template('modulos.html',perc_mod=perc_mod)


#######################ENCUESTA#######################
@app.route("/analisis", methods=['GET', 'POST'])
def analisis():
    if request.method == 'POST':
#        for idx in range(1,9):
#            #Verificacion de archivos adjuntos
#            if 'file_p'+str(idx) not in request.files:
#                flash('No file part')
##                return redirect(request.url)
#            file = request.files['file_p'+str(idx)]
#            #En caso de no adjuntar datos
#            if file.filename == '':
#                flash('No selected file')
##                return redirect(request.url)
#            if file and allowed_file(file.filename):
#                filename = secure_filename(file.filename)
#                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
##                return redirect(url_for('analisis',filename=filename))
#
#        #print('Pregunta 4 opcion '+str(request.form.getlist('question4')))
        return redirect(url_for('analisis'))
    return render_template('analisis.html')


@app.route("/preguntas_mod1", methods=['GET', 'POST'])
@login_required
def preguntas_mod1():
    global usr
    usr_id = current_user.id
    usr =   Users_data.find({'user_id': int(usr_id)})[0]
    IPSdata = IPS_data.find({"ID":usr['user_id']})[0]

    if IPSdata['Validar INFO']==False:
        return redirect(url_for('registro'))

    perc_mod = progreso_mod(IPSdata)
    if perc_mod[0]>=100:
        return redirect(url_for('mensaje'))

    temp = IPS_data.find({"ID":usr['ID']})
    temp2=temp[0]
    Rtas = temp2["Resultados Modulo 1"]
    if request.method == 'POST':
        return redirect(url_for('preguntas_mod1'))
    return render_template('preguntas_mod1.html',Rtas=json.dumps(dict(Rtas)))

@app.route("/preguntas_mod2", methods=['GET', 'POST'])
@login_required
def preguntas_mod2():
    usr_id = current_user.id
    usr =   Users_data.find({'user_id': int(usr_id)})[0]
    IPSdata = IPS_data.find({"ID":usr['user_id']})[0]


    if IPSdata['Validar INFO']==False:
        return redirect(url_for('registro'))

    perc_mod = progreso_mod(IPSdata)
    if perc_mod[1]>=100:
        return redirect(url_for('mensaje'))

    temp = IPS_data.find({"ID":usr['ID']})
    temp2=temp[0]
    Rtas = temp2["Resultados Modulo 2"]
    if request.method == 'POST':
      return redirect(url_for('preguntas_mod2'))
    return render_template('preguntas_mod2.html',Rtas=json.dumps(dict(Rtas)))

@app.route("/preguntas_mod3", methods=['GET', 'POST'])
@login_required
def preguntas_mod3():
    usr_id = current_user.id
    usr =   Users_data.find({'user_id': int(usr_id)})[0]
    IPSdata = IPS_data.find({"ID":usr['user_id']})[0]

    if IPSdata['Validar INFO']==False:
        return redirect(url_for('registro'))

    perc_mod = progreso_mod(IPSdata)
    if perc_mod[2]>=100:
        return redirect(url_for('mensaje'))


    temp = IPS_data.find({"ID":usr['ID']})
    temp2=temp[0]
    Rtas = temp2["Resultados Modulo 3"]

    if request.method == 'POST':
      return redirect(url_for('preguntas_mod3'))
    return render_template('preguntas_mod3.html',Rtas=json.dumps(dict(Rtas)))

@app.route("/preguntas_mod4", methods=['GET', 'POST'])
@login_required
def preguntas_mod4():
    usr_id = current_user.id
    usr =   Users_data.find({'user_id': int(usr_id)})[0]
    IPSdata = IPS_data.find({"ID":usr['user_id']})[0]

    if IPSdata['Validar INFO']==False:
        return redirect(url_for('registro'))

    perc_mod = progreso_mod(IPSdata)
    if perc_mod[3]>=100:
        return redirect(url_for('mensaje'))

    temp = IPS_data.find({"ID":usr['ID']})
    temp2=temp[0]
    Rtas = temp2["Resultados Modulo 4"]
    if request.method == 'POST':
        return redirect(url_for('preguntas_mod4'))
    return render_template('preguntas_mod4.html',Rtas=json.dumps(dict(Rtas)))

@app.route("/preguntas_mod5", methods=['GET', 'POST'])
@login_required
def preguntas_mod5():
    usr_id = current_user.id
    usr =   Users_data.find({'user_id': int(usr_id)})[0]
    IPSdata = IPS_data.find({"ID":usr['user_id']})[0]

    if IPSdata['Validar INFO']==False:
        return redirect(url_for('registro'))

    perc_mod = progreso_mod(IPSdata)
    if perc_mod[4]>=100:
        return redirect(url_for('mensaje'))

    temp = IPS_data.find({"ID":usr['ID']})
    temp2=temp[0]
    Rtas = temp2["Resultados Modulo 5"]
    if request.method == 'POST':
        return redirect(url_for('preguntas_mod5'))
    return render_template('preguntas_mod5.html',Rtas=json.dumps(dict(Rtas)))
################################################################
################################################################
@app.route("/preguntas_mod6", methods=['GET', 'POST'])
@login_required
def preguntas_mod6():
    usr_id = current_user.id
    usr =   Users_data.find({'user_id': int(usr_id)})[0]
    IPSdata = IPS_data.find({"ID":usr['user_id']})[0]

    if IPSdata['Validar INFO']==False:
        return redirect(url_for('registro'))

    perc_mod = progreso_mod(IPSdata)
    if perc_mod[5]>=100:
        return redirect(url_for('mensaje'))

    temp = IPS_data.find({"ID":usr['ID']})
    temp2 = temp[0]
    Rtas = temp2["Resultados Modulo 6"]
    nquestion=0
    if request.method == 'POST':
#        return render_template('preguntas_mod6.html', nquestion=nquestion,Rtas=json.dumps(dict(Rtas)))
        return redirect(url_for('preguntas_mod6'))

    return render_template('preguntas_mod6.html', nquestion=nquestion,Rtas=json.dumps(dict(Rtas)))


@app.route("/validar<modulo>", methods=['GET', 'POST'])
@login_required
def validar(modulo):
    if request.method == 'POST':
        usr_id = current_user.id
        usr =   Users_data.find({'user_id': int(usr_id)})[0]
        temp = IPS_data.find({"ID":usr['ID']})
        Ntemp=temp.count()
        dict_encuesta={}
        dict_encuesta["ID"]=usr['ID']

        dict_encuesta["Código Habilitación"]=usr['Codigo']
        dict_encuesta["Nombre del Prestador"]=temp[0]['Nombre del Prestador']
        dict_encuesta["usuario"]=usr['usuario']

        for j in request.form:
            if int(modulo)==1 and len(request.form[j])>0:
                IPS_data.find_and_modify(query={"ID":usr['ID']}, update={"$set": {"valmod1": True}}, upsert=False, full_response= True)
                temp = request.form.getlist(j)
                dict_encuesta[j] = [temp]
                if len(dict_encuesta[j])==1:
                    dict_encuesta[j]=dict_encuesta[j][0]
                continue
            if j.find("question")>=0:
                temp = request.form.getlist(j)
                if len(temp[0])>0:
                    dict_encuesta[j] = [temp]
                    if len(dict_encuesta[j])==1:
                        dict_encuesta[j]=dict_encuesta[j][0]

        IPS_data.find_and_modify(query={"ID":usr['ID']}, update={"$set": {"Resultados Modulo "+str(modulo): dict_encuesta}}, upsert=False, full_response= True)

        #VERIFICAR EL PORCENTAJE DEL MODULO
        IPSdata = IPS_data.find({"ID":usr['user_id']})[0]
        perc_mod = progreso_mod(IPSdata)
        current_mod = perc_mod[int(modulo)-1]
        if current_mod>=100:
            return redirect(url_for('modulo_completo'))

        return render_template('validar.html', nit=usr['Codigo'])
    return render_template('validar.html', nit=usr['Codigo'])

@app.route("/mensaje", methods=['GET', 'POST'])
@login_required
def mensaje():
    return render_template('mensaje.html')

@app.route("/modulo_completo", methods=['GET', 'POST'])
@login_required
def modulo_completo():
    return render_template('modulo_completo.html')


@app.route("/admin", methods=['GET', 'POST'])
@login_required
def admin():
    usr_id = int(current_user.id)
    usrid = Users_data.find({"user_id":usr_id})[0]
    #Select colab
    if ((usrid['role']=='manager')):
        return redirect(url_for('index'))

    Nregistered=0
    Nmiss=0
    tab_reg=[]
    tab_miss=[]
    n_mod=np.zeros(6)

    dpto_list = IPS_data.find().distinct("Departamento")
    dpto_list.sort()
    tab_dptos={}
    dpto_list=np.unique([k.upper() for k in dpto_list])

    for j in dpto_list:
        tab_dptos[j]=[0]*3

    #IPS registradas

    for docs in IPS_data.find().sort([("Departamento", ASCENDING), ("Municipio", ASCENDING)]):
        Depto=docs["Departamento"].upper()
        tab_dptos[Depto][0]=tab_dptos[Depto][0]+1
        if len(docs["Encargado de Encuesta"])>1:#IPS REGISTRADAS
            Nregistered=Nregistered+1
            tab_reg.append([docs["Departamento"].upper(),docs["Municipio"], docs["Nombre del Prestador"], docs["Código Habilitación"], "Aqui",docs['ID']])
            tab_dptos[Depto][1]=tab_dptos[Depto][1]+1
            perc_mod = progreso_mod(docs)
            if sum(perc_mod)>99*6:
                tab_dptos[Depto][2]=tab_dptos[Depto][2]+1
        else:#IPS FALTANTES
            Nmiss = Nmiss+1
            tab_miss.append([docs["Departamento"].upper(),docs["Municipio"], docs["Nombre del Prestador"], docs["Código Habilitación"], "Aqui",docs['ID']])

        for k in np.arange(1,7):
            if len(docs["Resultados Modulo "+str(k)])>0:
                n_mod[k-1]=n_mod[k-1]+1

    tab_dptos_list=[]
    dpto_list.sort()
    for j in range(len(dpto_list)):
        tab_dptos_list.append([dpto_list[j], tab_dptos[dpto_list[j]][0],tab_dptos[dpto_list[j]][1],tab_dptos[dpto_list[j]][2]])

    print(tab_dptos_list)
    n_mod=np.round(100*n_mod/(Nregistered+Nmiss),2)
    return render_template('admin.html', Nregistered=Nregistered, Nmiss=Nmiss, **{"tab_reg":tab_reg},**{"tab_miss":tab_miss}, **{"tab_dptos":tab_dptos_list}, n_mod=n_mod)

@app.route("/adminips_<ips_usr>", methods=['GET', 'POST'])
@login_required
def adminips_(ips_usr):
    usr_id = int(current_user.id)
    usrid = Users_data.find({"user_id":usr_id})[0]
    #Select colab
    if ((usrid['role']=='manager')):
        return redirect(url_for('index'))

    #print('IPS ID',ips_usr)
    usr =   IPS_data.find({"ID":int(ips_usr)})[0]
    general_info={
                  "Código Habilitación":usr['Código Habilitación'],
                  "ID":usr["ID"],
                  "Nombre del Prestador":usr['Nombre del Prestador'],
                  "NIT":usr['NIT'],
#                  "Razón social":usr['Razón social'],
#                  "Nivel del Prestador":usr["Nivel del Prestador"],
                  "Gerente":usr["Gerente"],
                  "Dirección":usr["Dirección"],
                  "Barrio":usr["Barrio"],
                  "Municipio":usr["Municipio"],
                  "Código Municipio":usr["Código Municipio"],
                  "Departamento":usr["Departamento"],
                  "Código Departamento":usr["Código Departamento"],
                  "Teléfono":usr["Teléfono"],
                  "E-mail empresarial":usr["E-mail empresarial"],
#                  "Representante legal":usr["Representante legal"],
#                  "E-mail del representante":usr["E-mail del representante"],
#                  "Teléfono del representate":usr["Teléfono del representate"],
                  "Encargado de Encuesta":usr["Encargado de Encuesta"],
                  "E-mail del Encargado":usr["E-mail del Encargado"],
                  "Teléfono del Encargado":usr["Teléfono del Encargado"],
    }

    Resultados_mod1=usr["Resultados Modulo 1"]
    Resultados_mod2=usr["Resultados Modulo 2"]
    Resultados_mod3=usr["Resultados Modulo 3"]
    Resultados_mod4=usr["Resultados Modulo 4"]
    Resultados_mod5=usr["Resultados Modulo 5"]
    Resultados_mod6=usr["Resultados Modulo 6"]


    perc_mod = progreso_mod(usr)
    return render_template('adminips_.html', **{"general_info":general_info},**{"Resultados_mod1":Resultados_mod1},**{"Resultados_mod2":Resultados_mod2},**{"Resultados_mod3":Resultados_mod3},**{"Resultados_mod4":Resultados_mod4},**{"Resultados_mod5":Resultados_mod5},**{"Resultados_mod6":Resultados_mod6},perc_mod=perc_mod)

@app.route("/habilitar<code_modulo>", methods=['GET', 'POST'])
@login_required
def habilitar(code_modulo):
    usr_id = int(current_user.id)
    usrid = Users_data.find({"user_id":usr_id})[0]
    if request.method == 'POST':
        code_hab_mod=code_modulo.split('_')
        codigo_hab=code_hab_mod[0]
        if (usrid['role']=='admin'):
             modulo=code_hab_mod[1]
             usr =   IPS_data.find({"ID":int(codigo_hab)})[0]
             IPS_data.find_and_modify(query={"ID":usr['ID']}, update={"$set": {"Resultados Modulo "+str(modulo): {}}}, upsert=False, full_response= True)
        return redirect('adminips_'+codigo_hab)
    return redirect('adminips_'+codigo_hab)

@app.route("/exportcsv<modulo>", methods=['GET', 'POST'])
@login_required
def exportcsv(modulo):
    # with open("outputs/Adjacency.csv") as fp:
    #     csv = fp.read()
    if request.method == 'POST':
        temp = IPS_data.find({"Encargado de Encuesta":{'$not': {'$size': 0}}})

        row = -1
        df=pd.DataFrame([])
        for reg in temp:
            if len(reg["Resultados Modulo "+str(modulo)])>0:
                print(reg["Nombre del Prestador"])
                row = row + 1
                data=reg["Resultados Modulo "+str(modulo)]
                #print(data.keys())

                usr =   IPS_data.find({"ID":int(reg["ID"])})[0]
                perc_mod = progreso_mod(usr)
                df.loc[row,"Código Habilitación"]=reg["Código Habilitación"]
                df.loc[row,"Nombre del Prestador"]=reg["Nombre del Prestador"]

                df.loc[row,"usuario"]="saludcol"+usr["Número de sede"]
                df.loc[row,"porcentaje"]=str(perc_mod[int(modulo)-1])

                for key in data.keys():
                    if key!="Código Habilitación" and key!="Nombre del Prestador" and key!="usuario" and key!="porcentaje" and key!="ID":
                        #print(data[key], key, len(data[key]))
                        if len(data[key])>1:
                            response=', '.join(data[key])
                        else:
                            response=data[key][0]
                    else:
                        response=data[key]
                    #print(response)
                    df.loc[row,key] = response
                    # if key.find("question")>=0:
                    #     columns.append(key.replace("question","Pregunta: "))
                    #else:
                        #columns.append(key)


        #print(df)

        #df.columns=columns
        columns=[]
        for nc in range(len(df.columns)):
            if df.columns[nc].find("question")>=0:
                columns.append(df.columns[nc].replace("question", "Pregunta: "))
            else:
                columns.append(df.columns[nc])
        df.columns=columns

        csv_file=df.to_csv(sep='\t')

        resp = make_response(csv_file)
        resp.headers["Content-Disposition"] = "attachment; filename=export.csv"
        resp.headers["Content-Type"] = "text/csv"
        return resp
    return render_template('admin.html')






@app.route("/download_data", methods=['GET', 'POST'])
@login_required
def download_data():
    # with open("outputs/Adjacency.csv") as fp:
    #     csv = fp.read()
    if request.method == 'POST':
        temp = IPS_data.find({"Encargado de Encuesta":{'$not': {'$size': 0}}}).sort([("Departamento", ASCENDING), ("Municipio", ASCENDING)])

        row = -1
        df=pd.DataFrame([])
        for reg in temp:

            row = row + 1
            usr =   IPS_data.find({"ID":int(reg["ID"])})[0]
            perc_mod = progreso_mod(usr)

            df.loc[row,"usuario"]="saludcol"+usr["Número de sede"]

            keys_data=reg.keys()

            for k in keys_data:
                if k.find("Resultados")>=0 or k.find("_id")>=0:
                    continue

                df.loc[row,k]=reg[k]

            df.loc[row,"porcentaje modulo 1"]=str(perc_mod[0])
            df.loc[row,"porcentaje modulo 2"]=str(perc_mod[1])
            df.loc[row,"porcentaje modulo 3"]=str(perc_mod[2])
            df.loc[row,"porcentaje modulo 4"]=str(perc_mod[3])
            df.loc[row,"porcentaje modulo 5"]=str(perc_mod[4])
            df.loc[row,"porcentaje modulo 6"]=str(perc_mod[5])




        csv_file=df.to_csv(sep='\t')

        resp = make_response(csv_file)
        resp.headers["Content-Disposition"] = "attachment; filename=Data_IPS_conexionsalud.csv"
        resp.headers["Content-Type"] = "text/csv"
        return resp
    return render_template('admin.html')

#
# @app.route('/progress1')
# def progress1():
#
#     def generate():
#         x = 0
#
#         while x <= 100:
#             yield "data:" + str(x) + "\n\n"
#             x = x + 10
#             time.sleep(0.5)
#
#     return Response(generate(), mimetype= 'text/event-stream')





#
#@app.route("/sendmail<modulo>", methods=['GET', 'POST'])
#@login_required
#def sendmail(modulo):
#    if request.method == 'POST':
#        nombres=request.form['nombre'+str(modulo)]
#
#        usr_id = int(current_user.id)
#        usrid = Users_data.find({"user_id":usr_id})[0]
#        user_encargado=usrid["usuario"]
#        user=user_encargado+"colab"+str(modulo)
#        usrid_colab = Users_data.find({"usuario":user})[0]
#        key_pass=usrid_colab["password_nc"]
#        to_email=request.form['email'+str(modulo)]
#        send_email(to_email, nombres, user, key_pass, modulo, file_email="./templates/email.html")
#        return redirect(url_for('modulos'))
#    return redirect(url_for('modulos'))




if __name__ == "__main__":
    app.run()
