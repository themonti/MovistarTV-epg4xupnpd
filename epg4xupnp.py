import os
from flask import Flask
import sys
import cookielib
import urllib2
import json
from datetime import datetime, date, time, timedelta
from time import mktime
import ConfigParser


reload(sys)
sys.setdefaultencoding("utf-8")



app = Flask(__name__)

@app.route('/')
def epg4xupnp():
	contenido=escribir_lista_m3u()
	return contenido
    #return 'Hello World!'


ENV='PROD'
config = ConfigParser.ConfigParser()
config.read('epg4xupnpd.cfg')


root_script=config.get(ENV, 'root_script')
end_m3u=config.get(ENV, 'end_m3u')


cookies = cookielib.LWPCookieJar()
handlers = [
    urllib2.HTTPHandler(),
    urllib2.HTTPSHandler(),
    urllib2.HTTPCookieProcessor(cookies)
    ]
opener = urllib2.build_opener(*handlers)

def fetch(uri):
    req = urllib2.Request(uri)
    return opener.open(req)

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

	str='#EXTM3U name="Movistar+ - Remote"'
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