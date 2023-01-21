import requests
import csv
import re
import sys
import time
import json
from datetime import datetime
######### Get program parameters names and values from parameter file #############
if_file = sys.argv[1] + ".csv" # input parameters csv file
### open parameter csv file and read one parameter aat the time
inputFile = open(if_file, 'r', newline='')  # input csv file open
rr = csv.reader(inputFile, dialect='excel')
### each csv line contains one variable parameter name and its value
i=0
for irow in rr:  # reads a line at a time arrays use for solar calculation
    i += 1
    if irow[0] == "===": break # === signifies that there are no more parameters to read
    if i == 1 : #Skip header (line 1)
        continue
    if irow[1] == "t" :  # read text (string) parameter variable and assign to it its value
        vars() [irow[0]] = irow[3]
    elif irow[1] == "f" :
        vars() [irow[0]] = float(irow[3]) # read float parameter variable and assign to it its value
    elif irow[1] == "i" : # read integer parameter variable and assign to it its value
        vars() [irow[0]] = int(irow[3])
    elif irow[1] == "a":  # read array parameter variable and assign to it its values
        vars()[irow[0]] = irow[3:]
    else :
        print("unrecognized type: ",irow[1])
        exit(1)
inputFile.close() # close parameter file

#build NREL PVwatts API to retrive complete year solar hourly electrical energy (AC)
api_url="https://developer.nrel.gov/api/pvwatts/v6.json?api_key=DEMO_KEY&timeframe=hourly&array_type=1&module_type=1&losses=10&ac&"
api_url +="lat=" + lat +"lon="  + lon + "tilt=" + tilt + "system_capacity=" + system_capacity + "azimuth=" + azimuth

print("solar panel latitude: " + re.sub(r'&$','', lat) + "  lognitude: " + re.sub(r'&$','', lon))
print("solar panel capacity kW: " + re.sub(r'&$','', system_capacity) + "  azimuth angle: " + re.sub(r'&$','', azimuth))
print("solar panel roof tilt: " + re.sub(r'&$','',tilt))

# download a compete yeer hourly alternating current (AC) solar energy data from PVwatts 24x365 = 8760 vlaues
rq = requests.get(api_url)
jsonString = rq.text
parseJstring = json.loads(jsonString)
ACsolar_kWh = parseJstring["outputs"]["ac"]
print("AC curent solar energy: ", ACsolar_kWh)

######Get Nevada Energy complete year hourly of consumed kWh data and store it in a 8760x4 array
AC_data = []
def read_NVEnergy_data():
    kwh = 0
    if_file = nvenergy_file + ".csv" # NV Energy data file
    inputFile = open(if_file, 'r', newline='')
    rr = csv.reader(inputFile, dialect='excel')
    i = 0
    for irow in rr:  # reads a line at a time  NVenergy data
        i += 1
        if i == 1: continue # skip header
        data_date = datetime.strptime(irow[0], '%m/%d/%Y').date()
        data_time = datetime.strptime(irow[1], '%H:%M:%S').time()
        kwhf = float(irow[2])
        kwh += kwhf

        # the NV Energy data file provides kWh energy every 15 minutes.
        # we add these 4 values for each hour to be consistent with the PVwatts hourly data
        if (i + 3) % 4 == 0:
            AC_data.append([data_date.month, data_date.day, data_time.hour, kwh])
            kwh = 0

# =============bill_calcculation for s0larnd time of use (TOU) rates===========

def bill_calcculation_solar_TOU(peak_rate,off_peak_rate,DEAA,ONTR,usage_total_kwh,solar_total_kwh,usage_peak_kwh,\
                      solar_peak_kwh) :
   #usage_total_kwh - totol electricity used for the period, peak and off-peak per month)
   #usage_peak_kwh - peak kwh used for the perion in question
   usage_off_peak_kwh = usage_total_kwh - usage_peak_kwh
   # calculate NV Energy solar+TOU bill using the companey's billig algorithm
   B = ((TRED+REPR+EE+NDPP)*usage_total_kwh + basic_charge)*(1+gov_tax) + UEC*usage_total_kwh
   if usage_peak_kwh >= solar_peak_kwh : # electricity usage during peak >= solar energy generate during peak
        credit_factor = 1
        tax_factor = 1 + gov_tax  # gov_tax = 5%
   else :  # electricity usage during peak is < than solar energy generate during peak
        credit_factor = 0.75 #customer get 75% credit for excess energy delivered to the grid
        tax_factor = 1   #no tak on solar generated electricity
   A = credit_factor * tax_factor * (DEAA + ONTR + peak_rate) * (usage_peak_kwh - solar_peak_kwh)

   if usage_off_peak_kwh >= solar_off_peak_kwh: # electricity usage during off-peak is >= solar energy generate during off-peak
        credit_factor = 1
        tax_factor = 1 + gov_tax
   else: # electricity usage during off-peak is < than solar energy generate during off-peak, gets 75% credit
        credit_factor = 0.75
        tax_factor = 1
     # if A is negative, we have credit to customer
   A +=  credit_factor * tax_factor*(DEAA+ONTR + off_peak_rate) * (usage_off_peak_kwh - solar_off_peak_kwh)
   return A+B
#=============end bill_calcculation_solar_TOU===========

read_NVEnergy_data()
