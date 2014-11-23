from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, backends
from django.core.mail.backends import console, smtp
from django.views.decorators.http import require_safe
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django import forms
#from django.forms import utils
from registration.forms import RegistrationForm
from Rivers.forms import PlacemarkForm
from Rivers.models import Placemarks, Gauges, AuthUser
from crispy_forms.utils import render_crispy_form
from crispy_forms.layout import Div
from crispy_forms.bootstrap import Alert
from jsonview.decorators import json_view
import requests
import json
import datetime
from dateutil.parser import parse
import re

from math import radians, cos, sin, asin, sqrt
from geopy import exc, geocoders

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
        geocode_obj = g.geocode(location_arg)
    except exc.GeopyError as e:
        raise "Error Getting Local Coordinates: %s" % e
    
    if geocode_obj:
        place,  (local_lat, local_lon) = geocode_obj
        local_location = (local_lat, local_lon)
        return local_location
    
    else: return None

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
        
def getDuration(local_location, river_location):
    org_lat, org_lon = local_location
    dst_lon, dst_lat = river_location
    gmaps_API_key = "AIzaSyCsV1PHBA6-FocW9_qi-Ixv7HfY3i5LDzU"
    url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=%s,%s&destinations=%s,%s&key=%s" % (org_lat,org_lon,dst_lat,dst_lon, gmaps_API_key)
    print url
    r = requests.get(url)
    if r.status_code == 200:
        distance_content = json.loads(r.content)
        print r.content

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

@login_required
def toggle_fav(request, placemark):
    user = AuthUser.objects.get(username=request.user.username)
    pm_obj = Placemarks.objects.get(id=placemark)
    if user.placemarks.filter(id=placemark):
        user.placemarks.remove(pm_obj)
        return HttpResponse("Success")
    elif not user.placemarks.filter(id=placemark):
        user.placemarks.add(pm_obj)
        return HttpResponse("Success")

@login_required
@json_view
def addRiver(request):
    if request.method == 'POST':
        form = PlacemarkForm(request.POST or None)
        if form.is_valid():
            user = AuthUser.objects.get(username=request.user.username)

            """Build Placemark Record"""
            pm_obj = Placemarks(name = form.cleaned_data['name'],
                        class_field = form.cleaned_data['class_field'],
                        section = form.cleaned_data['section'],
                        description = form.cleaned_data['description'],
                        state = form.cleaned_data['state'],
                        lon = form.cleaned_data['lat'],                 #Fix this shit
                        lat = form.cleaned_data['lon'],                 #Fix this shit
                        flow_min = form.cleaned_data['flow_min'],
                        flow_max = form.cleaned_data['flow_max'],
                        stage_min = form.cleaned_data['stage_min'],
                        stage_max = form.cleaned_data['stage_max'],)
            
            """If Gauge Field is not empty"""
            if form.cleaned_data['usgs_gauge']:
                """Get Gauge object if it already exists, else create it"""
                try:
                    gauge_obj, created = Gauges.objects.get_or_create(usgs_gauge = form.cleaned_data['usgs_gauge'])
                except IntegrityError as e:
                    form.errors['__all__'] = form.error_class(['Error getting or creating USGS gauge.'])
                else:
                    pm_obj.usgs_gauge = gauge_obj
            
            """Save new placemark in DB"""
            try:
                pm_obj.save()
            except Exception as e:
                form.errors['__all__'] = form.error_class(['Error saving new river section'])
                return {'success': False, 'form_html': render_crispy_form(form, context=RequestContext(request))}
            
            """Save new placemark as a user favorite"""
            try:
                user.placemarks.add(pm_obj)
            except Exception as e:
                form.errors['__all__'] = form.error_class(['Error adding new section to My Rivers.'])
            
            form.helper.layout.insert(0, Alert(content="Successfully added river section.", css_class="alert-success"))
            form.helper[1:11].wrap(Div, css_class='hidden')
            send_mail('Test Subject','Test Message','Rivers Near Me',['chrestme@gmail.com'])
            return {'success': True, 'form_html': render_crispy_form(form, context=RequestContext(request))}

        else:
            """form is not valid"""
            form_html = render_crispy_form(form, context=RequestContext(request))
            return {'success': False, 'form_html': form_html}
    
    elif request.method == 'GET':
        form = forms.PlacemarkForm()
        return render(request, 'rivers/crispy.html',{'form': form})
    
def crispyTest(request):
    if request.method == 'GET':
        form = PlacemarkForm()
        context = {'form': form}
        return render(request, 'rivers/crispy.html', context)
        

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = AuthUser
        fields = ['first_name', 'last_name', 'default_loc', 'default_lat', 'default_lon']

class UserRegisterForm(RegistrationForm):
    pass

def user_register(request):
    if request.method == 'Post':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            print form.cleaned_data
        else:
            return render(request, '/rivers/account/register',{
                          'form': form,
                          'errors': registrationForm.error_messages
            })
    else:
        form = UserRegistrationForm()
    return render(request,'/rivers/',{
                  'form': form
    })

@login_required
def user_profile(request):
    user = AuthUser.objects.get(username=request.user.username)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            user.first_name = form.cleaned_data['first_name']   #Needs input validation
            user.last_name = form.cleaned_data['last_name']     #Needs input validation
            if form.cleaned_data['default_loc']:
                user.default_loc = form.cleaned_data['default_loc']
                user.default_lat, user.default_lon = getLocalCoords(form.cleaned_data['default_loc'])

            user.save()
            return redirect(my_rivers)
    
    form = UserProfileForm(instance = user)
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
            regMatch = p.findall(placemark.description)
            if len(regMatch) > 0:
                section_url = regMatch[0][5:-3]
                section_url =  section_url.strip('"')
            else:
                section_url = placemark.description
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
    location_latlon = (38.8977332, -77.0365305)     #Lat/Lon Coordinates for The White House
    max_distance = 60
    user_placemarks = None
    local_coords = None
    errors = []
    add_river_form = None
    
    if request.user.is_authenticated():
        user = AuthUser.objects.get(username=request.user.username)
        add_river_form = PlacemarkForm()
        user_placemarks = user.placemarks.all()
        if user.default_loc:
            location = user.default_loc
            location_latlon = (float(user.default_lat), float(user.default_lon))

    if request.method == "POST":
        location = request.POST['loc']
        if request.POST['dist'] == None or request.POST['dist'] == '':
            errors.append("Unspecified Value for Max Distance")
        else:
            max_distance = int(request.POST['dist'])
            if max_distance < 0:
                errors.append("Negative value for Max Distance; using 0 instead.")
                max_distance = 0
            elif max_distance > 9999:
                errors.append("Value for Max Distance exceeds maximum allowable, using 9999 instead.")
                max_distance = 9999
                
        try:
            local_coords = getLocalCoords(location)
        except Exception as e:
            errors.append(e)
        if local_coords == None:
            errors.append("Could not find coordinates for %s" % location)
        else:
            location_latlon = local_coords

    pm_list = parsePlacemarks(Placemarks.objects.all().order_by('state'), max_distance, location_latlon, user_placemarks)
    
    RequestContext = {'pm_list': pm_list,
                      'distance': max_distance,
                      'spec_location': location,
                      'spec_lat': location_latlon[0],
                      'spec_lon': location_latlon[1],
                      'errors': errors,
                      'form': add_river_form}
    return render(request, 'rivers/index.html', RequestContext)
