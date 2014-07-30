#!/usr/bin/python
import requests
import json
import sqlite3
import datetime
from dateutil.parser import parse
import sys
import logging

query_interval = 900        #in seconds

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
    STAGE_PARAM_CODE = "00065"
    DISCHARGE_PARAM_CODE = "00060"
    TEMPC_PARAM_CODE = "00010"
    
    params = (STAGE_PARAM_CODE, DISCHARGE_PARAM_CODE, TEMPC_PARAM_CODE)
    
    usgs_url = "http://waterservices.usgs.gov/nwis/iv/?format=json&sites=%s&period=PT2H&parameterCd=%s&modifiedSince=PT15M" % (','.join(gauge_ids),','.join(params)) 
    try:
        r = requests.get(usgs_url)
    except Error as e:
        logging.critical("Error performing request: %s -- %s" % (e,usgs_url) )
    if r.status_code == 200:
        gauge_content = json.loads(r.content)
    else:
        logging.critical("Received unexpected status code from USGS server: %d" % r.status_code)
    
    conn = sqlite3.connect('/opt/RiversNearMe/RiversNearMe/placemark.db')
    c = conn.cursor()
    
    for parameter in gauge_content['value']['timeSeries']:
        a, gauge_id, parameter_code, b = parameter['name'].split(':')
        param_unit_abbrev = parameter['variable']['unit']['unitAbbreviation']
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
            
        sql = "UPDATE gauges SET %s = ?,%s = ?,last_update = ? WHERE usgs_gauge LIKE '%s'" % (param_column,change_column,gauge_id)
        try:
            c.execute(sql,(last_param_value,changeRate,last_timestamp))
        except sqlite3.Error as e:
            raise e
        
        conn.commit()
    conn.close()

logging.basicConfig(filename='/var/log/rivers.log',level=logging.DEBUG)

conn = sqlite3.connect('/opt/RiversNearMe/RiversNearMe/placemark.db')
c = conn.cursor()
c.execute('''SELECT usgs_gauge FROM gauges''')
try:
    rows = c.fetchall()
except sqlite3.Error as e:
    logging.critical("Error fetching gauges from database: %s" % e)
conn.close()


for i in xrange(0,len(rows),20):
    gauges_list = list()
    gauge_tuples = rows[i:i+20]
    for gauge in gauge_tuples:
        gauges_list.append(gauge[0])
    try:
        getGaugeInfo(gauges_list)
    except Exception as e:
        logging.critical("Error updating gauge info: %s" % e)
    #sys.exit()

#gauge_list = ("01648000","01646500","03076500")
#gauge_list = list()
#gauge_list.append("01646500")
#
