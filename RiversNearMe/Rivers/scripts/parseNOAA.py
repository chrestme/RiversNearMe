#/usr/bin/python

from __future__ import division
from django.db.utils import IntegrityError
from Rivers.models import NOAA_Gauges, Gauges
import csv

def parse_NOAA_file():
    with open('/opt/ALL_USGS-HADS_SITES.txt') as csvfile:
        noaa_reader = csv.reader(csvfile, delimiter='|')
        i = 0
        for row in noaa_reader:
            if i > 3:
		
		noaa_gauge = NOAA_Gauges(nws_id=row[0])
		
		try:
		    noaa_gauge.usgs_gauge = Gauges.objects.get(usgs_gauge=row[1].rstrip())
                except:
		    usgs_gauge = Gauges.objects.create(usgs_gauge=row[1].rstrip())
		    noaa_gauge.usgs_gauge = usgs_gauge #Gauges.objects.get(usgs_gauge=row[1].rstrip())
		
		noaa_gauge.goes_id = row[2]
		
		lat_deg, lat_min, lat_sec = row[4].split()
		if int(lat_deg) < 0:
		    noaa_gauge.latitude = (int(lat_deg) - (int(lat_min)/60) - (int(lat_sec)/3600))
		else:
                    noaa_gauge.latitude = (int(lat_deg) + (int(lat_min)/60) + (int(lat_sec)/3600))
		    
		lon_deg, lon_min, lon_sec = row[5].split()
		if int(lon_deg) < 0:
		    noaa_gauge.longitude = (int(lon_deg) - (int(lon_min)/60) - (int(lon_sec)/3600))
		else:
		    noaa_gauge.longitude = (int(lon_deg) + (int(lon_min)/60) + (int(lon_sec)/3600))
		
		noaa_gauge.location = row[6]
		
		try:
		    noaa_gauge.save()
		except IntegrityError:
		    print "Skipping duplicate: %s" % row[0]
            
	    i = i + 1

def run():
    parse_NOAA_file()()
