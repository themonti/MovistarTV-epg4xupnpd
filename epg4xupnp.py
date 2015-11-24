
# -*- coding: utf-8 -*-
import os
from flask import Flask, request, redirect, url_for
import sys
import cookielib
import urllib2
import json
from datetime import datetime, date, time, timedelta
from time import mktime
import ConfigParser
import pytz,time
from bs4 import BeautifulSoup
from flask.ext.sqlalchemy import SQLAlchemy

### Configuracion Base
reload(sys)
sys.setdefaultencoding("utf-8")

ENV='PROD'
config = ConfigParser.ConfigParser()
config.read('epg4xupnpd.cfg')


urlEPG=config.get(ENV, 'urlEPG')
jsoncanales=config.get(ENV, 'canales')
xupnpdIP=config.get(ENV, 'xupnpd-IP')

cookies = cookielib.LWPCookieJar()
handlers = [
    urllib2.HTTPHandler(),
    urllib2.HTTPSHandler(),
    urllib2.HTTPCookieProcessor(cookies)
    ]
opener = urllib2.build_opener(*handlers)
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

os.environ['TZ'] ='Europe/Madrid'
########


############################
#### Iniciamos la app  #####
############################
app = Flask(__name__)
app.debug = True
############################
############################


################################
# Configuracion DATABASE HEROKU
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://vccnjnlifunbnm:9kFmSDyg8BWTe5wFDdf4IOau0Q@ec2-54-247-170-228.eu-west-1.compute.amazonaws.com:5432/d9msst1obko80b'
db = SQLAlchemy(app)

# TABLA CANALES: definicion
class Canales(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255))
    ip = db.Column(db.String(255))
    port = db.Column(db.String(255))
    numcanal = db.Column(db.String(255))
    nombrecorto = db.Column(db.String(255))

    def __init__(self, nombre, ip,port,numcanal,nombrecorto):
        self.nombre = nombre
        self.ip = ip
        self.port = port
        self.numcanal = numcanal
        self.nombrecorto = nombrecorto
        
    def __repr__(self):
        return '<Canal %r>' % self.nombre
########################################################





### ROUTE /
@app.route('/')
def lista():
    allU=Canales.query.all()
    cadena=''
    for s in allU:
        cadena+='<tr><td>%s</td><td>%s</td><td><a href="rtp://@%s:%s">Ver</a></td></tr>'%(s.nombre,s.nombrecorto,s.ip,s.port)
    return '<h1>Movistar TV</h1><h3>epg 4 xupnp</h3><p></p><p></p><table><tr><th>Nombre</th><th>Nombre corto</th>%s</table><p></p><p></p><h5>v0.3</h5>'%(cadena)
    

### ROUTE /edit
@app.route('/edit', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        # lectura del cml en vivo
        xmlcanales=file.stream.read()
        soup = BeautifulSoup(xmlcanales,"xml")
        data=soup.find_all('UI-BroadcastService')
        # se borra la db actual
        status=borrarCanales()
        print "BORRADO db :",status
        
        # Parseamos el XML
        cadena=""
        for tag in data:
            if tag.IsInactive==None:
                # se graban los canales en la db
                status=grabarCanal(tag.SI.Name.text,tag.ServiceLocation.IPMulticastAddress['Address'],tag.ServiceLocation.IPMulticastAddress['Port'],tag.ServiceLogicalNumber.text,tag.SI.ShortName.text)
                cadena+='%s: %s<br/>'%(tag.SI.Name.text,status)
        # se hace el commit Masivo en db
        status=commitMasivo()
        print "COMMIT db: ",status

        return 'CANALES:<br/> %s<br/><br/>Commit Masivo: %s ' % (cadena,status)
    #presentacion del formulario de subida
    return '''
    <!doctype html>
    <title>Nuevo listado de canales activos</title>
    <h1>Nuevo listado de canales activos (.xml)</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>'''
### FUNCIONES DE APOYO A /edit   
# subir ficheros
ALLOWED_EXTENSIONS = set(['xml'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# borrar canales de la db
def borrarCanales():
    status=False
    try:
        num_rows_deleted = db.session.query(Canales).delete()
        db.session.commit()
        status=True
    except:
        db.session.rollback()
    return status

# grabar canales en la db - Solo session, sin commit
def grabarCanal(nombre,ip,port,numcanal,nombrecorto):
    status=False
    try:
        canal = Canales(nombre,ip,port,numcanal,nombrecorto)
        db.session.add(canal)
        # db.session.commit()
        status=True
    except:
        db.session.rollback()
    return status

# commit Masivo en db
def commitMasivo():
    status=False
    try:
        db.session.commit()
        status=True
    except:
        db.session.rollback()
    return status
##########


   
### Nueva versión de la exportancion desde la db
@app.route('/epg2.m3u')
def epg2():
    allU=Canales.query.order_by(Canales.numcanal).all()
    newline='\n'
    cadena='#EXTM3U name="NewMovistar"'
    
    for s in allU:
        cadena+='%s#EXTINF:-1 type=mpeg dlna_extras=mpeg_ps_pal group-title="NewMovistar",[%s] %s' % (newline,s.numcanal,s.nombre)
        cadena+='%shttp://%s:4022/udp/%s:%s' % (newline,xupnpdIP,s.ip,s.port)
    cadena+='''#EXTINF:-1 type=mpeg dlna_extras=mpeg_ps_pal group-title="NewMovistar",Brazzers
http://server9.balkantvmedia.com:8080/XXX1?u=user173:p=7wdjPw59
#EXTINF:-1 type=mpeg dlna_extras=mpeg_ps_pal group-title="NewMovistar",Hustler
http://server4.balkantvmedia.com:8080/XXX2?u=user173:p=7wdjPw59
#EXTINF:-1 type=mpeg dlna_extras=mpeg_ps_pal group-title="NewMovistar",Dorcel
http://server4.balkantvmedia.com:8080/XXX3?u=user173:p=7wdjPw59
#EXTINF:-1 type=mpeg dlna_extras=mpeg_ps_pal group-title="NewMovistar",PASSION XXX
http://q.gs/9830047/sex3todokodi
#EXTINF:-1 type=mpeg dlna_extras=mpeg_ps_pal group-title="NewMovistar",HUSTLER HD
http://bit.ly/1jGYwsX
#EXTINF:-1 type=mpeg dlna_extras=mpeg_ps_pal group-title="NewMovistar,Xtsy XXX
http://public.tuiptv.biz/public/PlayList.php?id=20e12547-5adb-4dc6-89af-41e6e7e6d4f3&channel=31
#EXTINF:-1 type=mpeg dlna_extras=mpeg_ps_pal group-title="NewMovistar,Juicy XXX
http://public.tuiptv.biz/public/PlayList.php?id=20e12547-5adb-4dc6-89af-41e6e7e6d4f3&channel=30
#EXTINF:-1 type=mpeg dlna_extras=mpeg_ps_pal group-title="NewMovistar,Real XXX
http://public.tuiptv.biz/public/PlayList.php?id=20e12547-5adb-4dc6-89af-41e6e7e6d4f3&channel=29
#EXTINF:-1 type=mpeg dlna_extras=mpeg_ps_pal group-title="NewMovistar,Sextreme XXX
http://public.tuiptv.biz/public/PlayList.php?id=20e12547-5adb-4dc6-89af-41e6e7e6d4f3&channel=26
#EXTINF:-1 type=mpeg dlna_extras=mpeg_ps_pal group-title="NewMovistar,Venus XXX
http://public.tuiptv.biz/public/PlayList.php?id=20e12547-5adb-4dc6-89af-41e6e7e6d4f3&channel=25
#EXTINF:-1 type=mpeg dlna_extras=mpeg_ps_pal group-title="NewMovistar,Playboy TV Latin America
http://public.tuiptv.biz/public/PlayList.php?id=20e12547-5adb-4dc6-89af-41e6e7e6d4f3&channel=28
'''

    return cadena
    

#### 20 Septiembre 2015
### Necesario para que xupnp no de error del script lua
@app.route('/epg.m3u')
def epg():
    listacanales=parserJSON_canales_contratados()
    listadoEPG=parserWeb(listacanales)
    
    return escribir_m3u(listadoEPG)

def parserJSON_canales_contratados():
    data=loadJson(jsoncanales)

    canales=data["canales"]
    lista_canales=[]
    for canal in canales:
        #print canal["id"],canal['nombre_canal']
        lista_canales.append(canal["epg_name"])
    #return ','.join(lista_canales)
    return lista_canales

def parserWeb(listacanales):
    # print "#"+urlEPG+"#"
    page=fetch(urlEPG)
    # print page
    parsed_html = BeautifulSoup(page,"html.parser")

    ###Elininado: creamos un diccionario para busqueda directa. El problema es que hay mas canales que no estan en la pagina
    # Se crean 2 lista para guardar el nombre de canal y la programacion en si
    # list_epg_nombre=[]
    # list_epg=[]
    listadoEPG={}

    # Como hay filas con estilos diferentes para los canales, se unen las dos
    listado_completo=parsed_html.body.find_all('tr', attrs={'class':'lineas0'})+parsed_html.body.find_all('tr', attrs={'class':'lineas1'})
    
    # unimos la lista de canales contratados en forma de cadena para realizar comparacioens por busqueda
    listado_canales_contratados=','.join(listacanales)
    for tr in listado_completo:
        # se extrae el nombre del canal de la web
        canal=tr.find('td',attrs={'valign':'top'}).text

        # si coinicide el canal, se agregan a la lista el nombre de canal y la programacion
        if canal in listado_canales_contratados:
            ###Elininado: creamos un diccionario para busqueda directa
            # list_epg_nombre.append(canal)
            # list_epg.append(tr.find('td',attrs={'width':'70%'}).text)
            listadoEPG[canal]=tr.find('td',attrs={'width':'70%'}).text
    
    ###Elininado: creamos un diccionario para busqueda directa, ya no hace falta ordenar
    # Se ordena el listado final de canales encontrados en funcion de la lista de canales contratados 
    #listado=zip(list_epg_nombre,list_epg)
    #listado.sort(key=lambda x: listacanales.index(x[0]))

    #Devolvemos el listado de canales definitivo ordenado
    return listadoEPG

def escribir_m3u(listadoEPG):
    data=loadJson(jsoncanales)
    canales=data['canales']
    # print canales

    newline='\n'


    str_group="MovistarTV %s" % time.strftime("%H:%M [%d/%m/%y]")
    str='#EXTM3U name="%s"' % str_group

    i=0
    for canal in canales:
        i+=1
        str_programa="[%s] %s | %s " % ("{:0>2d}".format(i),canal["nombre"], " | ".join(listadoEPG.get(canal["epg_name"],"").split('comenzó')))
        #### Limitación de caracteres [:40] para Samsung D/E Series
        #str+=newline+"#EXTINF:-1 logo=%s type=mpeg dlna_extras=mpeg_ps_pal , %s" % (canal["logo"],str_programa[:40])
        #### Sin limitación
        str+=newline+'#EXTINF:-1 group-title="%s" logo=%s type=mpeg dlna_extras=mpeg_ps_pal , %s' % (str_group,canal["logo"],str_programa)
        str+=newline+"http://%s:4022/udp/%s" % (xupnpdIP,canal['url'])
    return str

def loadJson(filename):
    json_data=open(filename).read()

    return json.loads(json_data)

def fetch(uri):
    req = urllib2.Request(uri,headers=hdr)
    ##return opener.open(req)
    #try:
    page = urllib2.urlopen(req)
    #except urllib2.HTTPError, e:
    #    print e.fp.read()
    content = page.read()
    return content
#######################

if __name__ == "__main__":
    app.run()