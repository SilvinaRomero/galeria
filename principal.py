from flask import Flask, render_template, redirect, send_from_directory, request
from werkzeug.utils import secure_filename  # urlencode()
# envío de emails
from flask_mail import Mail, Message
from bson import ObjectId
# Mongo
from pymongo import MongoClient
import os

# creamos app flask y lanzamos el servidor
app = Flask(__name__)

# conexión y creacion de bd y colección
client = MongoClient("mongodb://127.0.0.1:27017")
basedatos = client.fondos_flask
mistareas = basedatos.fondos
# IMAGENES
EXTENSIONES = ['jpg', 'png', 'jpeg']
# definimos la ruta donde se van a guardar las imagenes
app.config["UPLOAD_FOLDER"] = './static/fondos'

########### VARIABLES ENVIO EMAIL ############
# configuración para hacerlo desde casa
app.config["MAIL_SERVER"] = "mail.gmx.es"
app.config["MAIL_PORT"] = "587"
app.config["MAIL_USERNAME"] = ""
app.config["MAIL_PASSWORD"] = ""
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False
mail = Mail(app)
##############################################


def archivo_permitido(nombre):
    # foto.jpg -> separa en [foto,jpg] pos 1 esta dentro de extensiones?
    return "." in nombre and nombre.rsplit(".", 1)[1] in EXTENSIONES

@app.route('/')  # ruta inicio
@app.route('/', methods=["POST"])  # ruta para volver desde el formulario
@app.route('/galeria')  # ruta para el item 'todos' del breadcrums
def lista_todas():
    tema = request.values.get('tema')
    # si la ruta /galeria viene sin tema designado, es porque esta en la pestaña todos
    if tema == None:
        archivos = mistareas.find()
        # si son 'todos' creo el diccionario con value 'todos' en 'active'
        activo = {"todos": "active"}
    else:
        # si el tema existe, filramos los documentos y buscamos aquellos en donde el tema (de la url) sea uno de los temas del document
        archivos = mistareas.find({"temas":{"$eq": tema}})
        # creo el diccionario para el tema que será el tema activo
        activo = {tema: "active"}
    # devolvemos la plantilla con la lista de los documentos filtados por el tema en cuestión y la clase css que esta activa
    return render_template('index.html', activo=activo, lista=archivos)


@app.route('/aportar')
def aportar_nuevo():
    mensaje=''
    # si entra para rellenar el formulario devolvemos el mensaje vacio a la template
    return render_template('aportar.html', mensaje=mensaje)


@app.route('/insertar', methods=["POST"])
def nuevo():
    # .files["archivo"] aqui buscamos en el objeto request los archivos enviados
    f = request.files["archivo"]

    # si no se ha selccionado foto para subir, o el archivo no corresponde a las extensiones que hemos definido en EXTENSIONES,
    # devolvemos /aportar.html, pero con el mensaje correspondiente
    if f.filename == "":
        return render_template("/aportar.html", mensaje="Hay que seleccionar un archivo")
    else:
        if archivo_permitido(f.filename):
            # secure_filename-> urlencode()
            archivo = secure_filename(f.filename)
            # guardamos las imagenes en ('./static/fondos/archivo_name')
            f.save(os.path.join(app.config["UPLOAD_FOLDER"], archivo))
            # RECOGEMOS EL TITULO Y LA DESCRIPCIÓN
            tema = []
            # Ponemos titulo y descripcion por defeto
            titulo = "Imagen"
            descripcion = ''
            if request.values.get("titulo") != '':
                titulo = request.values.get("titulo").strip()

            if request.values.get("descripcion") != '':
                descripcion = request.values.get("descripcion")

            # controlamos los tags que estan activos, y si es asi añadimos cada caso a la lista
            if request.values.get("animales") == 'on': tema.append('animales')
            if request.values.get("naturaleza") == 'on': tema.append('naturaleza')
            if request.values.get("ciudad") == 'on':tema.append('ciudad') 
            if request.values.get("deporte") == 'on':tema.append('deporte')
            if request.values.get("personas") == 'on': tema.append('personas')
            # Agregamos el nuevo dccumento con los parametros que hemos recogido
            mistareas.insert({"fondo":f.filename,"titulo":titulo,"descripción":descripcion,"temas":tema})
        else:
            return render_template("/aportar.html", mensaje="El archivo no esta permitido")
    return redirect("/aportar")

### EMAILS
@app.route('/form_email')
def para_email():
    # recogemos el id de la peticion get
    id = request.values.get('_id')
    # buscamos el id en la coleccion
    elemento = mistareas.find_one({'_id':ObjectId(id)})
    # pasamos los parametros
    return render_template('form_email.html',id=id,titulo=elemento['titulo'],descripcion=elemento['descripción'],fondo=elemento['fondo'])


@app.route('/email',methods=['POST'])
def email():
    id = request.values.get('_id')
    elemento = mistareas.find_one({'_id':ObjectId(id)})
    # recoger datos del formulario, comprobamos que el email no este vacio, si no volvemos a llamar a /form_email
    if request.values.get('email') != '':
        email = request.values.get('email')
        imagen = os.path.join(app.config["UPLOAD_FOLDER"],elemento['fondo'])
        msg = Message("Fondos de pantalla Flask",sender="")
        msg.recipients = [email]
        msg.html = render_template("email.html",titulo=elemento['titulo'],descripcion=elemento['descripción'])
        # ############################## ADJUNTAR ARCHIVOS AL MAIL
        with app.open_resource(imagen) as adj:
            msg.attach(imagen,"imagen/jpeg",adj.read())
        mail.send(msg)
        return redirect('/')
        # #############################
    else:
        return render_template('form_email.html',id=id,titulo=elemento['titulo'],descripcion=elemento['descripción'],fondo=elemento['fondo'])
        
if __name__ == '__main__':
    app.run(debug=True)
