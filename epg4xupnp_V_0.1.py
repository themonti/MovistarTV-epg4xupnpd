
# -*- coding: utf-8 -*-
import os
from flask import Flask
import sys
import cookielib
import urllib2
import json
from datetime import datetime, date, time, timedelta
from time import mktime
import ConfigParser
import time
from bs4 import BeautifulSoup


reload(sys)
sys.setdefaultencoding("utf-8")

### Configuracion Base
ENV='DEV2'
config = ConfigParser.ConfigParser()
config.read('epg4xupnpd.cfg')


root_script=config.get(ENV, 'root_script')
end_m3u=config.get(ENV, 'end_m3u')
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
########

app = Flask(__name__)



### Necesario para que xupnp no de error del script lua
@app.route('/movistartv-epg4xupnp.m3u')
def epg4xupnp():
	contenido=escribir_lista_m3u()
	return contenido
    #return 'Hello World!'

### App base
@app.route('/')
def lista():
	return '<h1>Movistar TV</h1><h3>epg 4 xupnp</h3>'

#### 20 Septiembre 2015

### Necesario para que xupnp no de error del script lua
@app.route('/epg')
def epg():
	listacanales=parserJSON_canales_contratados()
	listadoEPG=parserWeb(listacanales)
	
	escribir_m3u(listadoEPG)

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


	str='#EXTM3U name="MovistarTV EPG %s"' % time.strftime("%d-%m-%Y %H:%M")
	for canal in canales:
		str_programa=listadoEPG.get(canal["epg_name"],None)
		if(str_programa==None):
			str_programa=canal["nombre"]
		str+=newline+"#EXTINF:-1 type=mpeg dlna_extras=mpeg_ps_pal logo=%s, %s" % (canal["logo"],str_programa)
		str+=newline+"http://%s:4022/udp/%s" % (xupnpdIP,canal['url'])
	print str

def loadJson(filename):
	json_data=open(filename).read()

	return json.loads(json_data)

def fetch(uri):
    req = urllib2.Request(uri,headers=hdr)
    ##return opener.open(req)
    #try:
    page = urllib2.urlopen(req)
	#except urllib2.HTTPError, e:
    #	print e.fp.read()
    content = page.read()
    return content
#######################



def dump():
    for cookie in cookies:
        print cookie.name, cookie.value


def epg_periodo_temporal():
	date_ahora=datetime.now()
	date_fin=date_ahora+timedelta(minutes=1)

	str_ahora=str(mktime(date_ahora.timetuple())).split(".")[0]
	str_fin=str(mktime(date_fin.timetuple())).split(".")[0]

	return str_ahora,str_fin



def procesar_json_movistar(res):
	file=root_script+"json_movistar.tv"
	fh = open(file, "w")
	# read from request while writing to file
	fh.write(res.read())
	fh.close()

	json_data=open(file).read()

	# data = json.loads(json_data)
	# # print(data)
	# json_data.close()


	# ourResult = data['Content']['List']
	# for rs in ourResult:
	# 	print rs['ChannelId'],rs['CallLetter'], rs['ProgramName'], rs['Images'][1]['Url']
	return json.loads(json_data)

def leer_imagenio_json():
	file=root_script+"imagenio.json"
	json_data=open(file).read()

	return json.loads(json_data)


def listar_canales_movistar_tv():
	data = leer_imagenio_json()

	canales=data['canales']
	lista_canales=[]
	for canal in canales:
		#print canal["id"],canal['nombre_canal']
		lista_canales.append(canal["id"])
	return '%2C'.join(lista_canales)

def obtener_epg_imagenio():
	str_canales=listar_canales_movistar_tv()
	inicio,fin=epg_periodo_temporal()
	uri = 'http://fut.tv.movistar.es/LiveGuide/GetLiveChannelsReducedLiveSchedules?offset=0&limit=100&liveChannelIds='+str_canales+'&startDate='+inicio+'&endDate='+fin+'&imageWidth=95&imageHeight=60&adultFilter=1'
	res = fetch(uri)
	# save cookies to disk. you can load them with cookies.load() as well.
	cookies.save(root_script+'imagenio.cookies')
	return procesar_json_movistar(res)

def buscar_canal_epg(id,epg):
	str_programa=""
	canales=epg['Content']['List']
	for canal in canales:
		# print canal['ChannelId'],id,
		if (str(canal['ChannelId'])==str(id)):
			str_programa=canal['ProgramName']
			# print str_programa
			break
	
	return str_programa

def escribir_lista_m3u():
	data = leer_imagenio_json()
	canales=data['canales']
	# print canales
	lista_canales=[]

	newline='\n'

	epg=obtener_epg_imagenio()

	str='#EXTM3U name="Movistar+ | epg4xupnp"'
	for canal in canales:
		str_programa=buscar_canal_epg(canal["id"],epg)
		if(str_programa==""):
			str_programa=canal["nombre_canal"]
		str+=newline+"#EXTINF:-1 type=mpeg dlna_extras=mpeg_ps_pal logo=%s, %s" % (canal["logo_canal"],str_programa)
		str+=newline+"http://%s:4022/udp/%s" % (config.get(ENV, 'xupnpd-IP'),canal['udp'])
	return str

	# file=end_m3u+"MovistarTV.m3u"
	# f = open(file, "w")
	# f.write(str)
	# f.close()


epg()