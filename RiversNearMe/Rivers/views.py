from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_safe
from django.core.exceptions import PermissionDenied
from django.forms import ModelForm
from Rivers.models import Placemarks, Gauges, AuthUser
import requests
import json
import datetime
from dateutil.parser import parse
import re

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
    STAGE_PARAM_CODE = "00065"
    DISCHARGE_PARAM_CODE = "00060"
    TEMPC_PARAM_CODE = "00010"
    
    params = (STAGE_PARAM_CODE, DISCHARGE_PARAM_CODE, TEMPC_PARAM_CODE)
    
    usgs_url = "http://waterservices.usgs.gov/nwis/iv/?format=json&sites=%s&period=PT2H&parameterCd=%s&modifiedSince=PT15M" % (','.join(gauges),','.join(params)) 
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

@login_required
def add_fav(request, placemark):
    user = AuthUser.objects.get(username=request.user.username)
    pm_obj = Placemarks.objects.get(id=placemark)
    try:
        user.placemarks.add(pm_obj)
    except:
        return PermissionDenied
    return HttpResponse("Success")

@login_required
def rem_fav(request, placemark):
    user = AuthUser.objects.get(username=request.user.username)
    pm_obj = Placemarks.objects.get(id=placemark)
    try:
        user.placemarks.remove(pm_obj)
    except Exception as e:
        print e
        return PermissionDenied
    return HttpResponse("Success")

class UserForm(ModelForm):
    class Meta:
        model = AuthUser
        fields = ['first_name', 'last_name', 'default_loc', 'default_lat', 'default_lon']

@login_required
def user_profile(request):
    user = AuthUser.objects.get(username=request.user.username)
    
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            print form.cleaned_data
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            if form.cleaned_data['default_loc']:
                user.default_loc = form.cleaned_data['default_loc']
                user.default_lat, user.default_lon = getLocalCoords(form.cleaned_data['default_loc'])
            #else:
            #    user.default_loc = "1600 Pennsylvania Ave, Washington, DC"
            #    user.default_lat = 38.8977332
            #    user.default_lon = -77.0365305
            user.save()
            return redirect(my_rivers)
    
    form = UserForm(instance = user)
    return render(request, 'rivers/user_profile.html', {
        'form': form
    })
    
def parsePlacemarks(placemarks, distance, local_location, user_placemarks=None):
    pm_list=list()
    gauges = list()
    p = re.compile('HREF=\".*\">AW')
    for placemark in placemarks:
        river_location = (float(placemark.lat),float(placemark.lon))
        haversine_distance = CalcDistance(local_location,river_location)
        user_fav = False
        if user_placemarks:
            if placemark in user_placemarks:
                user_fav = True
        
        if haversine_distance <= distance:
            section_url = p.findall(placemark.description)[0][5:-3]
            section_url =  section_url.strip('"')
            delta_sign = ''
            if hasattr(placemark, 'usgs_gauge'):
                if placemark.usgs_gauge.stage_delta > 0.0 or placemark.usgs_gauge.flow_delta > 0.0:
                    delta_sign = '&#10138'
                elif placemark.usgs_gauge.stage_delta < 0.0 or placemark.usgs_gauge.flow_delta < 0.0:
                    delta_sign = '&#10136'

            pm_dict = {'placemark': placemark,
                       'distance': "{0:.2f}".format(haversine_distance),
                       'AW_url': section_url,
                       'delta_sign': delta_sign,
                       'user_fav': user_fav
            }
            pm_list.append(pm_dict)
            
    return pm_list

@login_required
def my_rivers(request):
    user = AuthUser.objects.get(username=request.user.username)
    user_placemarks = user.placemarks.all()
    user_default_latlon = (user.default_lat, user.default_lon)
    pm_list = parsePlacemarks(user_placemarks, 9999, user_default_latlon, user_placemarks)
    
    RequestContext = {'pm_list': pm_list,
                      'spec_location': user.default_loc}
    
    return render(request, 'rivers/my_rivers.html', RequestContext)

# Create your views here.
def index(request):
    location = "The White House"
    location_latlon = (38.8977332, -77.0365305)     #My House
    max_distance = 60
    user_placemarks = None
    
    if request.user.is_authenticated():
        user = AuthUser.objects.get(username=request.user.username)
        user_placemarks = user.placemarks.all()
        if user.default_loc:
            location = user.default_loc
            location_latlon = (float(user.default_lat), float(user.default_lon))

    if request.method == "POST":
        location = request.POST['loc']
        max_distance = int(request.POST['dist'])
        try:
            location_latlon = getLocalCoords(location)
        except Exception as e:
            print e
            
    pm_list = parsePlacemarks(Placemarks.objects.all().order_by('state'), max_distance, location_latlon, user_placemarks)
            
    RequestContext = {'pm_list': pm_list,
                      'distance': max_distance,
                      'spec_location': location}
    return render(request, 'rivers/index.html', RequestContext)
