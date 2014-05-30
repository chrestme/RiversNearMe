import os, sys
import sqlite3
import argparse

from math import radians, cos, sin, asin, sqrt
from geopy import geocoders

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

def CalcDistance(self_location, river_location):
    local_lat, local_lon = self_location
    #print "Local: %s lat, %s lon" % (local_lat, local_lon)
    river_lon, river_lat = river_location
    #print "River: %s lat, %s lon" % (river_lat, river_lon)
    km_dist = haversine(local_lon, local_lat, river_lon, river_lat)
    #print "Distance in km: %f" % km_dist
    
    mile_ratio = 1.60934
    #print "Distance in miles: %f" % (km_dist / mile_ratio)
    return km_dist/mile_ratio
    
def FindRiverLocation(river_name, section_name):
    conn = sqlite3.connect('placemark.db')
    c = conn.cursor()
    c.execute('''SELECT lat, lon FROM placemarks WHERE section LIKE '%?%' and name LIKE '%?%' ''')
    river_lon, river_lat = c.fetchone()
    print "%s - River Lat: %f, River Lon: %f" % (section_name, river_lat, river_lon)
    
def getLocalCoords(location_arg):
    g = geocoders.GoogleV3()
    place,  (local_lat, local_lon) = g.geocode(location_arg)
    local_location = (local_lat, local_lon)
    return local_location
    
def main():
    #self_location = sys.argv[1]
    #river_name = sys.argv[2]
    #river_section = sys.argv[3]
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--river", help="Specify River Name")
    parser.add_argument("-s", "--section", help="Specify Section of River", required=False)
    parser.add_argument("-l", "--location", help="Specify your location in free text", required=False)
    parser.add_argument("-d", "--distance", help="Specify max distance from your current location", type=int, required=False)
    args = parser.parse_args()
    
    self_location = getLocalCoords(args.location)
    
    conn = sqlite3.connect('placemark.db')
    c = conn.cursor()
    
    for river_id,river_name,river_section,river_lat,river_lon in c.execute('''SELECT id, section, name, lat, lon FROM placemarks'''):
        river_location = (river_lat,river_lon)
        distance = CalcDistance(self_location, river_location)
        if distance <= args.distance:
            print "%s, %s: %f" % (river_name, river_section, distance)
            
    conn.close()
            
if __name__ == '__main__':
    main()
