from flask import Flask,request,jsonify
import os
import zipfile
import pprint
from pathlib import Path
import pandas
from datetime import datetime
import sys
import math
from collections import defaultdict
app = Flask(__name__)

@app.route("/get-report")
def get_report():
  startTime=int(request.args.get("start"));
  endTime=int(request.args.get("end"));
  return read_csv(startTime,endTime)
  


def read_csv(startTime,endTime):
  with zipfile.ZipFile("NU-raw-location-dump.zip", 'r') as zip_ref:
    zip_ref.extractall("extractedFiles")
  vehicleFilesCsv = os.listdir("extractedFiles/EOL-dump")
  tripFile = pandas.read_csv('Trip-Info.csv')
  speedDict=defaultdict(list)
  #iterate through all the files in the directory
  for vPlate in vehicleFilesCsv:
    #fetch file panda object
    if(not vPlate.endswith('.csv')):
        continue
    plateNo=vPlate.split('.')[0] 
    listTry=[plateNo]
    options = [] 
    options.append(plateNo)
   
    vPlateFile = pandas.read_csv("extractedFiles/EOL-dump/"+vPlate)
    #print(type(plateNo))
    #filter trip file for vehicle and start and end time
    tripFile.style.format({"date_time": lambda t: t.strftime("%Y%m%d%H%M%S")})
    filteredTripFile = tripFile.loc[(tripFile['vehicle_number'].isin(options)&(tripFile['date_time'] <=endTime)& (tripFile['date_time']>=startTime))]
    # filter vehicle file for values between start and end time
    vPlateFile=vPlateFile[(vPlateFile.tis >=startTime) & (vPlateFile.tis<=endTime)]
    #sort the file as we need to have all the time in ascending order
    vPlateFile.sort_values(by=['tis'],ascending=True, inplace=True)
    #remove all nan valued spd
    vPlateFile=vPlateFile[vPlateFile['spd'].notna()]
    prevTime=-1
    prevSpeed=-1
    dist=0
    violation=0
    tripNo=len(filteredTripFile["trip_id"].unique())
    arr=filteredTripFile["transporter_name"].unique()
    transportList = arr.tolist()
    #print("transportList "+str(transportList))
    timeOne=float(vPlateFile.tail(1)['tis'])
    timetwo=float(vPlateFile.head(1)['tis'])
    totalTime=timeOne-timetwo
    #iterate through each row of vehicle 
    #calculating distance by subtraction t2-t1*speed
    for index, row in vPlateFile.iterrows():
        if(prevTime !=-1 and prevSpeed != -1):
            dist=dist+((row['tis']-prevTime)*prevSpeed)
        prevTime=row['tis']
        prevSpeed=row['spd']
        if(row['osf'] is not False):
            violation=violation+1
    
    averageSpeed=dist/totalTime
    speedDict[plateNo]=[]
    speedDict[plateNo].append(dist)
    speedDict[plateNo].append(tripNo)
    speedDict[plateNo].append(averageSpeed)
    speedDict[plateNo].append(transportList)
    speedDict[plateNo].append(violation)
    df = pandas.DataFrame({'License plate number':pandas.Series(speedDict).index, 'values':pandas.Series(speedDict).values})
    df2=pandas.DataFrame(df["values"].to_list(), columns=['distance', 'trips','avgspeed','transporter','violation'])
    df2.insert(0, "License plate number", pandas.Series(speedDict).index, True)
    file_name = 'report_numadics.xlsx'
     # saving the excel
    print(df2.to_excel(file_name))
  return "written to "+file_name


# # app name 
# @app.errorhandler(404) 
# def not_found(e): 
#   return render_template("404.html") 

if __name__ == "__main__":
  app.run(debug=True)

