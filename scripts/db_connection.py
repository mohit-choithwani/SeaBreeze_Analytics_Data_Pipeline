import psycopg2
from psycopg2 import sql, errors
from logger import create_logger
import os
from time import sleep

# Configure logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logger = create_logger()

def create_tables_and_indexes(cursor):
    """
    Creates tables and indexes in the database.
    Args:
        cursor: Database cursor object.
    """
    try:
        CREATE_DATA_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS preprocessed_data (
            measurement_id VARCHAR(255) PRIMARY KEY,
            station_name VARCHAR(255) NOT NULL,
            measurement_timestamp TIMESTAMP NOT NULL,
            date DATE NOT NULL,
            time TIME NOT NULL,
            air_temperature FLOAT,
            wet_bulb_temperature FLOAT,
            humidity FLOAT,
            rain_intensity FLOAT,
            interval_rain FLOAT,
            total_rain FLOAT,
            precipitation_type FLOAT,
            wind_direction FLOAT,
            wind_speed FLOAT,
            max_wind_speed FLOAT,
            barometric_pressure FLOAT,
            solar_radiation FLOAT,
            heading FLOAT,
            battery_life FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );"""
        
        CREATE_INDEX_PROC_DATA_STATION = """CREATE INDEX IF NOT EXISTS idx_preprocessed_station_name 
                                            ON preprocessed_data (station_name);"""
        
        CREATE_INDEX_PROC_DATA_TIME = """CREATE INDEX IF NOT EXISTS idx_preprocessed_timestamp 
                                    ON preprocessed_data (date, time);"""
        
        CREATE_AGG_DATA_TABLE = """
        CREATE TABLE IF NOT EXISTS aggregated_data (
            station_name VARCHAR(255) NOT NULL,
            file_name VARCHAR(255),
            air_temperature_min FLOAT,
            air_temperature_max FLOAT,
            air_temperature_mean FLOAT,
            air_temperature_std FLOAT,
            -- (similar fields omitted for brevity)
            PRIMARY KEY (station_name, file_name)
        );"""
        
        CREATE_INDEX_AGG_DATA_STATION = """CREATE INDEX IF NOT EXISTS idx_agg_station_name 
                                    ON aggregated_data (station_name);"""
        
        CREATE_INDEX_AGG_DATA_FILE_NAME = """CREATE INDEX IF NOT EXISTS idx_agg_file_name
                                                ON aggregated_data (file_name);"""
        
        cursor.execute(CREATE_DATA_TABLE_SQL)
        cursor.execute(CREATE_INDEX_PROC_DATA_STATION)
        cursor.execute(CREATE_INDEX_PROC_DATA_TIME)
        cursor.execute(CREATE_AGG_DATA_TABLE)
        cursor.execute(CREATE_INDEX_AGG_DATA_STATION)
        cursor.execute(CREATE_INDEX_AGG_DATA_FILE_NAME)
        logger.info("Tables and indexes created successfully!")
    
    except Exception as error:
        logger.error(f"Error creating tables and indexes: {error}")

def connect_to_postgresql():
    try:
        conn = psycopg2.connect(
                dbname='SeaBreeze',
                user='SeaBreeze',
                password='SeaBreeze',
                host='localhost',
                port=5432
            )
        cursor = conn.cursor()
        logger.info("Connected to PostgreSQL database.")
        return conn, cursor
    
    except Exception as error:
        logger.error(f"Failed to connect to the database. Error: {error}")
        return None, None

def insert_processed_data(cursor, conn, data):
    """
    Inserts data into the specified table with error handling.
    """
    try: 
        for _, row in data.iterrows():
            insert_script = """INSERT INTO preprocessed_data (
                            measurement_id, station_name, measurement_timestamp,
                            date, time, 
                            air_temperature, wet_bulb_temperature , humidity,
                            rain_intensity ,interval_rain ,total_rain ,
                            precipitation_type ,wind_direction ,wind_speed ,
                            max_wind_speed ,barometric_pressure ,solar_radiation ,
                            heading , battery_life ) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s)
                            ON CONFLICT (measurement_id) DO NOTHING;"""
            
            insert_values = (row['Measurement ID'], row['Station Name'], row['Measurement Timestamp'], 
                             row['date'], row['time'],
                             row['Air Temperature'], row['Wet Bulb Temperature'], row['Humidity'],
                             row['Rain Intensity'], row['Interval Rain'], row['Total Rain'],
                             row['Precipitation Type'], row['Wind Direction'], row['Wind Speed'],
                            row['Maximum Wind Speed'], row['Barometric Pressure'], row['Solar Radiation'],
                            row['Heading'], row['Battery Life']
                             )
      
            
            cursor.execute(insert_script, insert_values)
            
    except errors.UniqueViolation as unique_error:
            logger.error(f"Duplicate entry skipped. Row: {row}. Error: {unique_error}")
            # conn.rollback()  # Optional: Rollback only for severe cases
    except Exception as error:
            logger.error(f"Error inserting row: {row}. Error: {error}")
            # conn.rollback()  # Optional: Rollback only for severe cases
            
    finally:
        conn.commit()
        logger.info("Data inserted successfully into preprocessed_data table.")

def insert_aggregated_data(cursor, conn, agg_data):
    """
    Inserts data into the agg_data table with error handling.
    """
    try: 
        for _, row in agg_data.iterrows():
            insert_script = """INSERT INTO aggregated_data (
                    station_name, file_name,
                    air_temperature_min, air_temperature_max, air_temperature_mean, air_temperature_std, 
                    wet_bulb_temperature_min, wet_bulb_temperature_max, wet_bulb_temperature_mean, wet_bulb_temperature_std,
                    humidity_min, humidity_max, humidity_mean, humidity_std, 
                    rain_intensity_min, rain_intensity_max, rain_intensity_mean, rain_intensity_std, 
                    interval_rain_min, interval_rain_max, interval_rain_mean, interval_rain_std,
                    total_rain_min, total_rain_max, total_rain_mean, total_rain_std,
                    precipitation_type_min, precipitation_type_max, precipitation_type_mean, precipitation_type_std,
                    wind_direction_min, wind_direction_max, wind_direction_mean, wind_direction_std,
                    wind_speed_min, wind_speed_max, wind_speed_mean, wind_speed_std,
                    max_wind_speed_min, max_wind_speed_max, max_wind_speed_mean, max_wind_speed_std,
                    barometric_pressure_min, barometric_pressure_max, barometric_pressure_mean, barometric_pressure_std,
                    solar_radiation_min, solar_radiation_max, solar_radiation_mean, solar_radiation_std,
                    heading_min, heading_max, heading_mean, heading_std,
                    battery_life_min, battery_life_max, battery_life_mean, battery_life_std
                ) VALUES (%s, %s, 
                          %s, %s, %s, %s, 
                          %s, %s, %s, %s,
                          %s, %s, %s, %s, 
                          %s, %s, %s, %s,
                          %s, %s, %s, %s, 
                          %s, %s, %s, %s, 
                          %s, %s, %s, %s,
                          %s, %s, %s, %s, 
                          %s, %s, %s, %s, 
                          %s, %s, %s, %s,
                          %s, %s, %s, %s, 
                          %s, %s, %s, %s, 
                          %s, %s, %s, %s,
                          %s, %s, %s, %s)
                          ON CONFLICT (station_name, file_name) DO NOTHING;"""
            
            insert_values = (
                row['data_source'], row['file_name'], 
                row['Air Temperature_min'], row['Air Temperature_max'], row['Air Temperature_mean'], row['Air Temperature_std'],
                row['Wet Bulb Temperature_min'], row['Wet Bulb Temperature_max'], row['Wet Bulb Temperature_mean'], row['Wet Bulb Temperature_std'], 
                row['Humidity_min'], row['Humidity_max'], row['Humidity_mean'], row['Humidity_std'],
                row['Rain Intensity_min'], row['Rain Intensity_max'], row['Rain Intensity_mean'], row['Rain Intensity_std'], 
                row['Interval Rain_min'], row['Interval Rain_max'], row['Interval Rain_mean'], row['Interval Rain_std'],
                row['Total Rain_min'], row['Total Rain_max'], row['Total Rain_mean'], row['Total Rain_std'],
                row['Precipitation Type_min'], row['Precipitation Type_max'], row['Precipitation Type_mean'], row['Precipitation Type_std'], 
                row['Wind Direction_min'], row['Wind Direction_max'], row['Wind Direction_mean'], row['Wind Direction_std'],
                row['Wind Speed_min'], row['Wind Speed_max'], row['Wind Speed_mean'], row['Wind Speed_std'],
                row['Maximum Wind Speed_min'], row['Maximum Wind Speed_max'], row['Maximum Wind Speed_mean'], row['Maximum Wind Speed_std'], 
                row['Barometric Pressure_min'], row['Barometric Pressure_max'], row['Barometric Pressure_mean'], row['Barometric Pressure_std'],
                row['Solar Radiation_min'], row['Solar Radiation_max'], row['Solar Radiation_mean'], row['Solar Radiation_std'],
                row['Heading_min'], row['Heading_max'], row['Heading_mean'], row['Heading_std'],
                row['Battery Life_min'], row['Battery Life_max'], row['Battery Life_mean'], row['Battery Life_std']          
            )
            
            cursor.execute(insert_script, insert_values)
            
    except errors.UniqueViolation as unique_error:
            logger.error(f"Duplicate entry skipped. Row: {row}. Error: {unique_error}")
            # conn.rollback()  # Optional: Rollback only for severe cases
    except Exception as error:
            logger.error(f"Error inserting row: {row}. Error: {error}")
            # conn.rollback()  # Optional: Rollback only for severe cases
            
    finally:
        conn.commit()
        logger.info("Data inserted successfully into aggregated_data table.")

def send_data_postgresql(preprocessed_data, agg_data):
    conn, cursor = None, None
    try:
        conn, cursor = connect_to_postgresql()
        create_tables_and_indexes(cursor)
        
        insert_processed_data(cursor, conn, preprocessed_data)
        insert_aggregated_data(cursor, conn, agg_data)
    except Exception as error:
        logger.error(f"Fatal error in main workflow: {error}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("Database connection closed.")