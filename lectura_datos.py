#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
codigo para leer los archivos con la informacion de la lluvia registrada con los
pluviomentros de la red de monitoreo de CLIMAX y graficar los mapas
Requerimientos:
    Es necesario habilitar la API de google drive. Yo seguí las indicaciones de
    https://developers.google.com/sheets/api/quickstart/python
    Generar el archivo vacio 'credentials.json'
    directorio con el spreadsheet id para cada estacion
    carpeta con shapefiles de bermejo y chaco
    Es neceario convertir los shapefile de nahuel usando
    ogr2ogr -t_srs EPSG:4326 newshape.shp oldshape.shp
    https://gis.stackexchange.com/questions/231734/unable-to-load-a-shapefile-with-basemap

PENDIENTES: transformar la informacion en un xarray para manejarla mejor
                                 
Created on Tue May 29 10:11:05 2018

@author: marisol
"""
ruta_IDs = '/home/marisol/Dropbox/investigacion/chaco/mapas_pluviometros_chaco/IDs/'
ruta_shapefiles = '/home/marisol/mapas/'
shapefile_chaco = ruta_shapefiles + 'Shapes_Chaco/'
shapefile_bermejo = ruta_shapefiles + 'Shapes_Bermejo/'

sheets_name = ['2017', '2018']

from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from os import listdir 
from os.path import isfile, join
import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.basemap as bm

#genero diccionario con nombre de estaciones y el ID de google spreadsheet
estaciones = []
keys = ['Nombre', 'Sheet_ID']
files = [ruta_IDs + f for f in listdir(ruta_IDs) if isfile (join(ruta_IDs, f))]
for i in files:
    ids = [line.rstrip('\n') for line in open(i)]
    estaciones.append(dict(zip(keys,[i[71:].replace('_',' '), ids[0]])))


# Setup the Sheets API
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
store = file.Storage('credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('sheets', 'v4', http=creds.authorize(Http()))

# Call the Sheets API

RANGE_NAME = "!A4:M34"
lluvia = np.zeros([len(estaciones),len(sheets_name),31,12])
jj = 0
for j in estaciones:
    ii = 0
    for i in sheets_name:
        result = service.spreadsheets().values().get(spreadsheetId = 
                                     j['Sheet_ID'], range = i + 
                                     RANGE_NAME, valueRenderOption = 'UNFORMATTED_VALUE').execute()
        values = result.get('values',[])
        y=np.array([[yi.replace(',','.') if isinstance(yi,str) else yi for yi in xi] +[None]*(13-len(xi)) for xi in values])
        y [np.where(y =='')] = None
        lluvia[jj,ii,:,:] = np.asarray(y[:,1:], dtype = float)
        ii = ii + 1
    jj = jj + 1

dicts_from_file = []
with open('coordenadas') as f:
    all_lines = f.readlines()
    [dicts_from_file.append(eval(i))  for i in all_lines[5:22]]
f.close()
# me quedo solo con los nombres y las coordenadas

keys2 = ['ID','Nombre','Coordenadas']
estaciones2 = []
for i in dicts_from_file:
    estaciones2.append(dict(zip(keys2, [i[0]['properties']['ID'], 
                                        i[0]['properties']['Paraje'][:], 
                                        i[0]['geometry']['coordinates'][:]])))

indices = [i['ID']-1 for j in estaciones for i in estaciones2  if j['Nombre'] in i['Nombre']]
#selecciono las fechas que eligio fede para caracterirzar eventos.
#Evento 1: 17-23 enero 2018

lluvia_evento1 = np.nansum(lluvia[:,1,16:23,0], axis = 1)

lluvia_evento1_2d =np.empty((lluvia_evento1.shape[0],lluvia_evento1.shape[0]))
lluvia_evento1_2d.fill(np.nan)

np.fill_diagonal(lluvia_evento1_2d, lluvia_evento1)

#grafico

fig1 = plt.figure(figsize=(16,20),dpi=300)  #fig size in inches\
ax = fig1.add_axes([0.1,0.1,0.8,0.8])
# Reading shape file
sf_rio_paraguay = shapefile_chaco + 'Rio_Paraguay'
sf_cuencas_chaco = shapefile_chaco + 'Cuencas_Chaco'
sf_munis_bermejo = shapefile_bermejo + 'Munis_Bermejo'
sf_loc_bermejo = shapefile_bermejo + 'LocalidadesBermejoconDatos'
sf_munis_chaco = shapefile_bermejo + 'Municipios_Chaco'#
#

mapproj = bm.Basemap(projection='merc',
                     llcrnrlat=-27.3, llcrnrlon=301.0-360,
                     urcrnrlat=-26.7, urcrnrlon=-58.5,resolution = 'i')    #projection and map limits
    
mapproj.drawstates()          
lonproj, latproj = mapproj(np.array([estaciones2[i]['Coordenadas'][0] for i 
                                     in indices]), np.array([estaciones2[i]
                                     ['Coordenadas'][1] for i in indices]))      #poject points
#local departments and rivers
mapproj.readshapefile(sf_cuencas_chaco,'cuencas_chaco',linewidth=1.0,color = 'b')
mapproj.readshapefile(sf_rio_paraguay,'Rio_Paraguay',linewidth=1.0,color = 'b')
mapproj.readshapefile(sf_munis_bermejo,'Munis_Bermejo',linewidth=1.0,color = 'k')
mapproj.readshapefile(sf_munis_chaco,'Munis_Chaco',linewidth=1.0,color = 'k')
mapproj.readshapefile(sf_loc_bermejo,'Loc_Bermejo',linewidth=1.0,color = 'k')

CS1 = mapproj.scatter(lonproj, latproj,s = lluvia_evento1/(np.max(lluvia_evento1)-7)*1000*4, c='C0') 
#dibujo referencia
x, y = mapproj(-58.95,-27.25)
mapproj.scatter(x,y,s = 50/(np.max(lluvia_evento1)-7)*1000*4, c='C0')
x, y = mapproj(-58.94,-27.25)
plt.text(x,y,'50mm',Fontsize = 10, fontweight='bold')
#write stations name
for i in range(len(lonproj)):
    plt.text(lonproj[i],latproj[i],estaciones2[indices[i]]['Nombre'],Fontsize = 12, fontweight='bold')
x, y = mapproj(-58.72,-27.03)
#write city of reference
plt.text(x,y,'+ La Leonesa- Las Palmas', color='r', Fontsize = 12, fontweight='bold')

ax.set_title('Lluvia 17-23 Enero 2018', Fontsize = 14, fontweight='bold')
#save figure
fig1.savefig('pp_evento1.jpg', bbox_inches='tight', orientation='landscape', papertype='A4')
