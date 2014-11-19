from django.core.exceptions import ValidationError
import requests
import json

def validGauge(gauge):
    url = "http://waterservices.usgs.gov/nwis/iv/?format=json&sites=%s" % (gauge)
    for i in range(3):
        try:
            r = requests.get(url)
        except Exception as e:
            continue
        else:
            if r.status_code == 200:
                gauge_info = json.loads(r.content)
                if not len(gauge_info['value']['timeSeries']) > 0:
                    raise ValidationError("%s is not a valid USGS Gauge." % gauge)
                else:
                    return
            else:
                continue
    raise ValidationError("Unable to validate Gauge: %s with the USGS site." % gauge)
    