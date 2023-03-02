import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

import datetime as dt
from dateutil.relativedelta import relativedelta


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///./Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station   

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

#Landing Page

@app.route("/")
def welcome():

    return(
        f"This is a Flask API for Climate Analysis .<br/><br/><br/>"
        f"The following are the available routes for this API, ENJOY!!!<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/start/end<br/>"
    )

#Precipitation Page
@app.route("/api/v1.0/precipitation")
def precipitation():

    session = Session(engine)

    final_data_point_tuple = session.query(
        Measurement.date).order_by(Measurement.date.desc()).first()
    (latest_date, ) = final_data_point_tuple
    latest_date = dt.datetime.strptime(latest_date, '%Y-%m-%d')
    latest_date = latest_date.date()
    date_year_ago = latest_date - relativedelta(years=1)

    last_year_data = session.query(Measurement.date, Measurement.prcp).filter(
        Measurement.date >= date_year_ago).all()
    
    session.close()

#Transformation of data so it can be displayed on the webpage
    all_precipitation = []
    for date, prcp in last_year_data:
        if prcp != None:
            precip_dict = {}
            precip_dict[date] = prcp
            all_precipitation.append(precip_dict)

#JSON returned
    return jsonify(all_precipitation)

#Station Page
@app.route("/api/v1.0/stations")
def stations():

#SQL queries for station data
    session = Session(engine)

    stations = session.query(Station.station, Station.name, Station.latitude,
                             Station.longitude, Station.elevation).all()
    
    session.close()

#Data Transformation for display on the web page
    station_data = []
    for station, name, latitude, longitude, elevation in stations:
        all_stations_dict = {}
        all_stations_dict['station'] = station
        all_stations_dict['name'] = name
        all_stations_dict['latitude'] = latitude
        all_stations_dict['longitude'] = longitude
        all_stations_dict['elevation'] = elevation
        station_data.append(all_stations_dict)

#JSON returned
    return jsonify(station_data)

#Tobs Page    
@app.route("/api/v1.0/tobs")
def tobs():

#Query to find only data relevant to the most active station during the last year of the data.
    session = Session(engine)

    final_data_point_tuple = session.query(
        Measurement.date).order_by(Measurement.date.desc()).first()
    (latest_date, ) = final_data_point_tuple
    latest_date = dt.datetime.strptime(latest_date, '%Y-%m-%d')
    latest_date = latest_date.date()
    date_year_ago = latest_date - relativedelta(years=1)

#Data collection query following creation of the date/time window
    most_active_station = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count().desc()).\
        first()
    
    (most_active_station_id, ) = most_active_station
    print(
        f'The station id of the most active station is {most_active_station_id}.')
    
    previous_year_station_data = session.query(Measurement.date, Measurement.tobs).filter(
        Measurement.station == most_active_station_id).filter(Measurement.date >= date_year_ago).all()

    session.close()

#Data preparation for display on the webpage
    all_temperatures = []
    for date, temp in previous_year_station_data:
        if temp != None:
            temp_dict = {}
            temp_dict[date] = temp
            all_temperatures.append(temp_dict)

#JSON returned
    return jsonify(all_temperatures)

#Start and Start/End Page, both are constructed using the same code
@app.route('/api/v1.0/<start>', defaults={'end': None})
@app.route("/api/v1.0/<start>/<end>")
def determine_temp_for_date_range(start, end):

    session = Session(engine)

#Start and end date available
    if end != None:
        temperature_data = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).filter(Measurement.date <= end).all()
#Only start date available        
    else:
        temperature_data = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).all()
        
    session.close()

#Query conversion to a list
    temperatures_list = []
    no_temperature_data = False
    for min_temp, avg_temp, max_temp in temperature_data:
        if min_temp == None or avg_temp == None or max_temp == None:
            no_temperature_data = True
        temperatures_list.append(min_temp)
        temperatures_list.append(avg_temp)
        temperatures_list.append(max_temp)
#Return JSON for the dictionary
    if no_temperature_data == True:
        return f'No data available for the given range. Please try another range.'
    else:
        return jsonify(temperatures_list)
    
if __name__ == '__main__':
    app.run(debug=True)