from django.shortcuts import render
#from django.http import HttpResponse
from django.template import RequestContext
from Rivers.models import Placemarks
import requests
import json

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
    river_lon, river_lat = river_location
    km_dist = haversine(local_lon, local_lat, river_lon, river_lat)
    
    mile_ratio = 1.60934
    return km_dist/mile_ratio

def getLocalCoords(location_arg):
    g = geocoders.GoogleV3()
    try:
        place,  (local_lat, local_lon) = g.geocode(location_arg)
    except Exception as e:
        raise "Error Getting Local Coordinates: %s" % e
    local_location = (local_lat, local_lon)
    return local_location

def getGaugeInfo(gauge_ids):
    STAGE_PARAM_CODE = "00060"
    DISCHARGE_PARAM_CODE = "00065"
    TEMPC_PARAM_CODE = "00010"
    
    params = (STAGE_PARAM_CODE, DISCHARGE_PARAM_CODE, TEMPC_PARAM_CODE)
    
    usgs_url = "http://waterservices.usgs.gov/nwis/iv/?format=json&sites=%s&period=PT2H&parameterCd=%s" % (','.join(gauge_ids),','.join(params)) 
    r = requests.get(usgs_url)
    if r.status_code == 200:
        gauge_content = json.loads(r.content)
    #gauge_content['value']['timeSeries'][2]['values'][0]['value'][0]['value']      Stage Height
    #gauge_content['value']['timeSeries'][1]['values'][0]['value'][0]['value']      Flow
    #gauge_content['value']['timeSeries'][0]['values'][0]['value'][0]['value']      Temp
    
    for parameter in gauge_content['value']['timeSeries']:
        a, gauge_id, parameter_code, b = parameter['name'].split(':')
        param_unit_abbrev = parameter['variable']['unit']['unitAbbreviation']
        
        for parameter_values in parameter['values']:
            for time_value in parameter_values['value']:
                timestamp = time_value['dateTime']
                parameter_value = time_value['value']
        
    
    

# Create your views here.
def index(request):
    location = "22192"
    local_location = (38.676929,-77.271296)     #My House
    #local_location = (39.2, -74.79)
    distance = 60
    if request.method == "POST":
        location = request.POST['loc']
        distance = int(request.POST['dist'])
        try:
            local_location = getLocalCoords(location)
        except Exception as e:
            print e
    pm_list=list()
    gauges = list()
    for placemark in Placemarks.objects.all().order_by('state'):
        river_location = (float(placemark.lat),float(placemark.lon))
        haversine_distance = CalcDistance(local_location,river_location)
        gauges.append(placemark.gauge)
        if  haversine_distance <= distance:
            pm_dict = {'placemark': placemark,
                       'distance': "{0:.2f}".format(haversine_distance)}
            pm_list.append(pm_dict)
    RequestContext = {'pm_list': pm_list,
                      'distance': distance,
                      'spec_location': location}
    return render(request, 'rivers/index.html', RequestContext)
