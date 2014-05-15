#!/usr/bin/env python

import os
import fnmatch
import sqlite3
from fastkml import kml
from math import radians, cos, sin, asin, sqrt
from geopy import geocoders
from bs4 import BeautifulSoup
import re
import urllib

def parseKMLs():
    conn = sqlite3.connect('placemark.db')
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE IF NOT EXISTS placemarks (id INTEGER PRIMARY KEY AUTOINCREMENT, name, class, description BLOB, state, lat REAL, lon REAL)''')
    except Exception as e:
        print "Error creating table: %s" % e
    
    kmlFiles = []
    for dirfile in os.listdir('.'):
        if fnmatch.fnmatch(dirfile,'*.kml'):
            kmlFiles.append(dirfile)
            #print dirfile
            
    for kmlFile in kmlFiles:
        with open (kmlFile, 'rb') as kFile:
            data = kFile.read()
            
        k = kml.KML()
        k.from_string(data)
        PMList = list(list(k.features())[0].features())
        for placemark_obj in PMList:
            placemark_state, extension = os.path.splitext(kmlFile)
            placemark_class_name = placemark_obj.name
            placemark_classification, placemark_name = placemark_class_name.split(': ')
            
            placemark_description = placemark_obj.description
            lat, lon, alt = placemark_obj.geometry.coords[0]
            #print "%s\t%s\t%s\t(%s,%s)" % (placemark_classification, placemark_name, placemark_state, lat, lon)
            try:
                c.execute('''INSERT INTO placemarks (name, class, description, state, lat, lon) VALUES (?,?,?,?,?,?)''', (placemark_name, placemark_classification, placemark_description, placemark_state, lat, lon))
            except Exception as e:
                print "Error inserting row into DB: %s" % e
                
        conn.commit()
    conn.close()
    



def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 

    # 6367 km is the radius of the Earth
    km = 6367 * c
    return km


def CalcDistance():
    g = geocoders.GoogleV3()
    place, (local_lat, local_lon) = g.geocode("22192")
    print "%s: %f, %f" % (place, local_lat, local_lon)
    
    conn = sqlite3.connect('placemark.db')
    c = conn.cursor()
    c.execute('''SELECT lat, lon FROM placemarks WHERE name LIKE '%Potomac%Little Falls%' ''')
    river_lon, river_lat = c.fetchone()
    print "River Lat: %f, River Lon: %f" % (river_lat, river_lon)
    
    km_dist = haversine(local_lon, local_lat, river_lon, river_lat)
    print "Distance in km: %f" % km_dist
    
    mile_ratio = 1.60934
    print "Distance in miles: %f" % (km_dist / mile_ratio)
    

class AppURLopener(urllib.FancyURLopener):
    version = "App/ParseKMLs-ThanksAW"

urllib._urlopener = AppURLopener()
    
conn = sqlite3.connect('placemark.db')
c = conn.cursor()
p = re.compile('HREF=\".*\">AW')
for row in c.execute('''SELECT id, description FROM placemarks'''):
    section_url = p.findall(row[1])[0][5:-3]
    f = urllib.urlopen(section_url.strip('"'))
    aw_page = f.read()
    soup = BeautifulSoup(aw_page)
    aw, section_name = soup.title.string.split(' - ')
    print row[0], section_name
    try:
        c.execute('''UPDATE placemarks SET section = ? WHERE id == ?''', (section_name, row[0]))
    except Exception as e:
        print "Error updating section names: %s" % e
conn.commit()
    
