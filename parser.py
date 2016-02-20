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
### Configuracion Base
reload(sys)
sys.setdefaultencoding("utf-8")
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

### ROUTE /
@app.route('/')
def parserWeb():
    urlEPG='http://www.formulatv.com/programacion/movistarplus/'
    page=fetch(urlEPG)
    # print page
    parsed_html = BeautifulSoup(page,"html.parser")

    ###Elininado: creamos un diccionario para busqueda directa. El problema es que hay mas canales que no estan en la pagina
    # Se crean 2 lista para guardar el nombre de canal y la programacion en si
    # list_epg_nombre=[]
    # list_epg=[]
    listadoEPG={}

    # Como hay filas con estilos diferentes para los canales, se unen las dos
    listado_completo=parsed_html.body.find_all('tr')
    newline='<br/>'
    p=""
    # unimos la lista de canales contratados en forma de cadena para realizar comparacioens por busqueda
    for tr in listado_completo:
        # se extrae el nombre del canal de la web
        if tr.find(attrs={'class':'prga-d'})!=None:
            idcanal=tr.find(attrs={'class':'num'}).text
            logo=tr.find(attrs={'class':'lcad'})['src']
            programa=tr.find(attrs={'class':'prga-p'}).text
            p+='%s%s[%s]-%s '%(newline,idcanal,logo,programa)
        

    #Devolvemos el listado de canales definitivo ordenado
    return str(p)

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