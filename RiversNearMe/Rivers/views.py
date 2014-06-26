from django.shortcuts import render
#from django.http import HttpResponse
#from django.template import RequestContext, loader
from Rivers.models import Placemarks

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

def getLocalCoords(location_arg):
    g = geocoders.GoogleV3()
    place,  (local_lat, local_lon) = g.geocode(location_arg)
    local_location = (local_lat, local_lon)
    return local_location

# Create your views here.
def index(request):
    zipcode = "22192"
    distance = 60
    if request.method == "POST":
        zipcode = request.POST['zip']
        distance = int(request.POST['dist'])
        
    else:
        pm_list = Placemarks.objects.all().order_by('state')
        context = {'pm_list': pm_list}
        return render(request, 'rivers/index.html', context)
