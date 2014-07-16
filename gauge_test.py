#!/usr/bin/python
import requests
import json

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
    
    for parameter in gauge_content['value']['timeSeries']:
        a, gauge_id, parameter_code, b = parameter['name'].split(':')
        param_unit_abbrev = parameter['variable']['unit']['unitAbbreviation']
        print "%s\t%s" % (gauge_id, parameter_code)
        
        for parameter_values in parameter['values']:
            for time_value in parameter_values['value']:
                timestamp = time_value['dateTime']
                parameter_value = time_value['value']
                print "%s\t%s %s" % (timestamp, parameter_value, param_unit_abbrev)
        print "\n"


gauge_list = ("01648000","01646500","03076100")
#gauge_list = list()
#gauge_list.append("01646500")
getGaugeInfo(gauge_list)
