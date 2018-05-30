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
PENDIENTES: transformar la informacion en un xarray para manejarla mejor
            Incorporar la escala cuando se grafica la pp
            Agregar límites de departamentos (tenemos shapefile??)            
Created on Tue May 29 10:11:05 2018

@author: marisol
"""
ruta_IDs = '/home/marisol/Dropbox/investigacion/chaco/mapas_pluviometros_chaco/IDs/'
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
#Evento 1: 1-3 noviembre 2017

lluvia_evento1 = np.nansum(lluvia[:,0,0:3,10], axis = 1)

lluvia_evento1_2d =np.empty((lluvia_evento1.shape[0],lluvia_evento1.shape[0]))
lluvia_evento1_2d.fill(np.nan)

np.fill_diagonal(lluvia_evento1_2d, lluvia_evento1)

#grafico

fig1 = plt.figure(figsize=(16,20),dpi=300)  #fig size in inches\
ax = fig1.add_axes([0.1,0.1,0.8,0.8])
mapproj = bm.Basemap(projection='merc',
                     llcrnrlat=-27.3, llcrnrlon=301.0,
                     urcrnrlat=-26.7, urcrnrlon=301.5,resolution = 'i')    #projection and map limits
    
mapproj.drawcoastlines()          # coast
mapproj.drawcountries()          # ccountries
mapproj.drawstates()          
mapproj.drawparallels(np.array([-60, -45, -30,-15,0]), labels=[1,0,0,0])    #draw parallels
mapproj.drawmeridians(np.array([280, 300, 320]), labels=[0,0,0,1])     #draw meridians\
lonproj, latproj = mapproj(np.array([estaciones2[i]['Coordenadas'][0] for i 
                                     in indices])+360, np.array([estaciones2[i]
                                     ['Coordenadas'][1] for i in indices]))      #poject grid
CS1 = mapproj.scatter(lonproj, latproj,s = lluvia_evento1/(np.max(lluvia_evento1)-7)*1000*4) 
for i in range(len(lonproj)):
    plt.text(lonproj[i],latproj[i],estaciones2[indices[i]]['Nombre'],Fontsize = 14)
ax.set_title('Lluvia 1-3 Noviembre 2017', Fontsize = 14)
#save figure
fig1.savefig('pp_evento1.jpg',dpi=300,bbox_inches='tight',orientation='landscape',papertype='A4')
