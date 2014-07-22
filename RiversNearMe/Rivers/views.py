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
    #print len(gauge_content['value']['timeSeries'][0]['values'])
    
    conn = sqlite3.connect('/opt/RiversNearMe/RiversNearMe/placemark.db')
    c = conn.cursor()
    
    for parameter in gauge_content['value']['timeSeries']:
        a, gauge_id, parameter_code, b = parameter['name'].split(':')
        param_unit_abbrev = parameter['variable']['unit']['unitAbbreviation']
        print "%s\t%s" % (gauge_id, parameter_code)
        current_time = datetime.datetime.now().isoformat()
        try:
            c.execute('''UPDATE gauges SET last_update = ?''',(current_time,))
        except sqlite3.Error as e:
            raise e
        time_values = parameter['values'][0]['value']

        for time_value in time_values:
            timestamp = time_value['dateTime']
            parameter_value = time_value['value']
            #print "%s\t%s %s" % (timestamp, parameter_value, param_unit_abbrev)
        
        if not time_values:
            continue
        first_timestamp = time_values[0]['dateTime']
        last_timestamp = time_values[len(time_values)-1]['dateTime']
        first_param_value = time_values[0]['value']
        last_param_value = time_values[len(time_values)-1]['value']
            
        changeRate = calcRateofChange(first_timestamp,last_timestamp,first_param_value,last_param_value)

        #print '''%s:\t%s\n%s:\t%s\n%s %s per hour''' % (first_timestamp,first_param_value,last_timestamp,last_param_value,changeRate,param_unit_abbrev)
        
        #parameter_value = time_value['value']
        if parameter_code == STAGE_PARAM_CODE:
            param_column = "stage"
            change_column = "stage_delta"
        elif parameter_code == DISCHARGE_PARAM_CODE:
            param_column = "flow"
            change_column = "flow_delta"
        elif parameter_code == TEMPC_PARAM_CODE:
            param_column = "water_temp"
            change_column = "temp_delta"
        else:
            raise "Unknown parameter code"
            
        sql = "UPDATE gauges SET %s = ?,%s = ? WHERE usgs_gauge LIKE '%s'" % (param_column,change_column,gauge_id)
        try:
            c.execute(sql,(last_param_value,changeRate))
        except sqlite3.Error as e:
            raise e
        
        conn.commit()
    conn.close()

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
            time_diff = datetime.timedelta(parse(placemark.usgs_gauge.last_update), datetime.datetime.now())
            if time_diff.total_seconds() > 900:
                gauges.append(placemark.usgs_gauge)
            
            pm_dict = {'placemark': placemark,
                       'distance': "{0:.2f}".format(haversine_distance)}
            pm_list.append(pm_dict)
            
    RequestContext = {'pm_list': pm_list,
                      'distance': distance,
                      'spec_location': location}
    return render(request, 'rivers/index.html', RequestContext)
