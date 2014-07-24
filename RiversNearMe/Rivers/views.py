from django.shortcuts import render
#from django.http import HttpResponse
from django.template import RequestContext
from Rivers.models import Placemarks, Gauges
import requests
import json
import datetime
from dateutil.parser import parse

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

def calcRateofChange(first_time_value, last_time_value, first_value, last_value):
    first_timestamp = parse(first_time_value)
    last_timestamp = parse(last_time_value)
    time_diff = last_timestamp-first_timestamp
    diff_hours = time_diff.total_seconds() / 3600
    
    value_diff = float(last_value) - float(first_value)
    try:
        rateChange = "{0:.2f}".format(value_diff/diff_hours)
    except ZeroDivisionError:
        return "0.00"
    return rateChange

def getGaugeInfo(gauges):
    STAGE_PARAM_CODE = "00060"
    DISCHARGE_PARAM_CODE = "00065"
    TEMPC_PARAM_CODE = "00010"
    
    params = (STAGE_PARAM_CODE, DISCHARGE_PARAM_CODE, TEMPC_PARAM_CODE)
    
    usgs_url = "http://waterservices.usgs.gov/nwis/iv/?format=json&sites=%s&period=PT2H&parameterCd=%s" % (','.join(gauges),','.join(params)) 
    r = requests.get(usgs_url)
    if r.status_code == 200:
        gauge_content = json.loads(r.content)
    
    for parameter in gauge_content['value']['timeSeries']:
        a, gauge_id, parameter_code, b = parameter['name'].split(':')
        gauge_obj = Gauges.objects.get(usgs_gauge__exact=gauge_id)

        param_unit_abbrev = parameter['variable']['unit']['unitAbbreviation']

        current_time = datetime.datetime.now().isoformat()
        gauge_obj.last_update = current_time

        time_values = parameter['values'][0]['value']

        for time_value in time_values:
            timestamp = time_value['dateTime']
            parameter_value = time_value['value']
        
        if not time_values:
            continue
        first_timestamp = time_values[0]['dateTime']
        last_timestamp = time_values[len(time_values)-1]['dateTime']
        first_param_value = time_values[0]['value']
        last_param_value = time_values[len(time_values)-1]['value']
            
        changeRate = calcRateofChange(first_timestamp,last_timestamp,first_param_value,last_param_value)
        
        if parameter_code == STAGE_PARAM_CODE:
            gauge_obj.stage = last_param_value
            gauge_obj.stage_delta = changeRate
        elif parameter_code == DISCHARGE_PARAM_CODE:
            gauge_obj.flow = last_param_value
            gauge_obj.flow_delta = changeRate
        elif parameter_code == TEMPC_PARAM_CODE:
            gauge_obj.water_temp = last_param_value
            gauge_obj.temp_delta = changeRate
        else:
            raise "Unknown parameter code"
        
        gauge_obj.save()

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
        if haversine_distance <= distance:
            #gauges.append(placemark.usgs_gauge)
            #gauge_update = parse(placemark.usgs_gauge.last_update)
            current_time  = datetime.datetime.now()
            #print current_time
            #print placemark.usgs_gauge.last_update
            #print placemark.usgs_gauge.last_update.replace(tzinfo=None)
            
            time_diff = current_time - placemark.usgs_gauge.last_update.replace(tzinfo=None)
            #print time_diff.total_seconds()
            if time_diff.total_seconds() > 900:
                gauges.append(placemark.usgs_gauge.usgs_gauge)
                #try:
                getGaugeInfo(gauges)
                #except Exception as e:
                #    RequestContext = {'error': e}
                #    return render(request, 'rivers/index.html', RequestContext)
            
            pm_dict = {'placemark': placemark,
                       'distance': "{0:.2f}".format(haversine_distance)}
            pm_list.append(pm_dict)
            
    RequestContext = {'pm_list': pm_list,
                      'distance': distance,
                      'spec_location': location}
    return render(request, 'rivers/index.html', RequestContext)
