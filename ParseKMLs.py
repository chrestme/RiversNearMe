#!/usr/bin/env python

import os, sys
import fnmatch
import sqlite3
from fastkml import kml
from math import radians, cos, sin, asin, sqrt
from geopy import geocoders
from bs4 import BeautifulSoup
import re
import urllib
import codecs

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


def CalcDistance(location_arg):
    g = geocoders.GoogleV3()
    place, (local_lat, local_lon) = g.geocode(location_arg)
    print "%s: %f, %f" % (place, local_lat, local_lon)
    
    conn = sqlite3.connect('placemark.db')
    c = conn.cursor()
    c.execute('''SELECT section,lat, lon FROM placemarks WHERE section LIKE '%6. Little Falls%' ''')
    section_name,river_lon, river_lat = c.fetchone()
    print "%s - River Lat: %f, River Lon: %f" % (section_name, river_lat, river_lon)
    
    km_dist = haversine(local_lon, local_lat, river_lon, river_lat)
    print "Distance in km: %f" % km_dist
    
    mile_ratio = 1.60934
    print "Distance in miles: %f" % (km_dist / mile_ratio)
    

class AppURLopener(urllib.FancyURLopener):
    version = "App/ParseKMLs-ThanksAW"

def getSectionNames():
    urllib._urlopener = AppURLopener()
    
    conn = sqlite3.connect('placemark.db')
    c = conn.cursor()
    p = re.compile('HREF=\".*\">AW')
    c.execute('''SELECT id, description FROM placemarks''')
    rows = c.fetchall()
    entries = []
    
    with codecs.open('sectionNames.csv', 'w+', encoding='utf-8') as section_f:
        for row in rows:
            section_name = ''
            section_url = p.findall(row[1])[0][5:-3]
            f = urllib.urlopen(section_url.strip('"'))
            aw_page = f.read()
            soup = BeautifulSoup(aw_page)
            try:
                aw, section_name = soup.title.string.split('American Whitewater - ')
            except:
                section_name = soup.title.string
            print row[0], section_name
            entries.append((row[0],section_name))
            if section_name == None: section_name = ''
            line = str(row[0])+","+section_name+"\n"
            section_f.write(line)
            
def getUSGSGauge():
    conn = sqlite3.connect('/opt/RiversNearMe/RiversNearMe/placemark.db')
    c = conn.cursor()
    p = re.compile('/id/.*/">AW')
    q = re.compile('usgs-[0-9]*')
    
    c.execute('''SELECT id, description FROM placemarks''')
    rows = c.fetchall()
    
    for row in rows:
        section_gauge = None
        section_id = row[0]
        AWurl = p.findall(row[1])
        AWpage = AWurl[0].split('/')[2]
        page_path = "/opt/RiversNearMe/AWPages/" + AWpage
        with open (page_path) as f:
            html = f.read()
        usgs_gauges = q.findall(html)
        for usgs_gauge in usgs_gauges:
            a,section_gauge = usgs_gauge.split('usgs-')
        print section_id, section_gauge
        try:
            c.execute('''UPDATE placemarks SET usgs_gauge = ? WHERE id = ?''', (section_gauge,section_id))
        except sqlite3.Error as e:
            print "Error executing gauge update: %s" % e
        conn.commit()
    conn.close()
    
def getAWpage():
    urllib._urlopener = AppURLopener()
    
    conn = sqlite3.connect('placemark.db')
    c = conn.cursor()
    p = re.compile('HREF=\".*\">AW')
    c.execute('''SELECT id, description FROM placemarks''')
    rows = c.fetchall()
    
    for row in rows:
        section_url = p.findall(row[1])[0][5:-3]
        section_url =  section_url.strip('"')
        section_url_parts = section_url.rsplit('/',2)
        aw_file = "AWPages/%s" % section_url_parts[1]
        print "%s - %s" % (aw_file,section_url)
        urllib.urlretrieve(section_url.strip('"'),aw_file)

def getRange():
    conn = sqlite3.connect('/opt/RiversNearMe/RiversNearMe/placemark.db')
    c = conn.cursor()
    
    for root, dirs, files in os.walk('/opt/RiversNearMe/AWPages'):
        for filename in files:
            #root = '/opt/RiversNearMe/AWPages'
            #filename = '753'
            print filename
            with open(os.path.join(root,filename), 'r') as f:
                html = f.read()
            
            td_gauge = None
            td_range = None
            min_val = None
            max_val = None
            unit = None
            
            soup = BeautifulSoup(html)
            tables = soup.findAll('table', {'class': 'data_table'})
            for table in tables:
                if table.find('th', text='Range'):
                    td_gauge = tables[1].find('td', {'rowspan': '2', 'valign': 'top'})
                    if td_gauge:
                        td_range = td_gauge.findNext('td')
                        break
            if td_range:
                td_range = td_range.text.strip()
                try:
                    min_val, dash, max_val, unit = td_range.split()
                except Exception as e:
                    continue
                print min_val, dash, max_val, unit
                if unit == 'ft' or unit == 'inches':
                    min_column = 'stage_min'
                    max_column = 'stage_max'
                elif unit == 'cfs' or unit == '%%':
                    min_column = 'flow_min'
                    max_column = 'flow_max'
                else:
                    continue
                if max_val.lower() == "unknown":
                    max_val = '999999'
                if min_val.lower() == "unknown":
                    min_val = '0'
                
                sql = '''UPDATE placemarks SET %s = ?, %s = ? WHERE description LIKE '%%id/%s/%%' ''' % (min_column, max_column,filename)
                c.execute(sql, (min_val,max_val))
            
            else:continue
        
        conn.commit()
    conn.close()
            

#print entries
def populateDB():
    conn = sqlite3.connect('placemark.db')
    c = conn.cursor()
    
    with open('sectionNames.csv','r') as f:
        lines = f.readlines()
        for line in lines:
            #print line
            entry = line.split(',',1)
            section_id = entry[0]
            try:
                section_name_river, river_city_state, country = entry[1].rsplit(',',2)
            except:
                section_name_river, river_city_state, country = '','',''
            try:
                section_name, river_name = section_name_river.rsplit(',',1)
            except:
                section_name = section_name_river
                river_name = ''
                
            river_city_state = river_name+river_city_state
            print "%s\t%s\t%s\t%s" % (section_id, section_name, river_city_state, country)
            try:
                c.execute('''UPDATE placemarks SET section = ? WHERE id == ?''', (section_name,section_id))
            except sqlite3.Error as e:
                print "Error updating section names: %s" % e
            conn.commit()
        conn.close()    

def main():
    #self_location = sys.argv[1]
    #print location_arg
    #getAWpage()
    #getUSGSGauge()
    try:
        getRange()
    except Exception as e:
        print e
    
    #CalcDistance(self_location, river_location)
    

if __name__ == '__main__':
    main()
    
