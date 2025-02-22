import os
import geoip2.database
import logging
from config import GEOIP_DATABASE_PATH

log_dir = os.path.join('data', 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(filename=os.path.join(log_dir, 'search_logs.log'), level=logging.INFO)

def log_search(query, ip_address):
    if ip_address in ("127.0.0.1", "::1"):
        ip_address = "8.8.8.8"  
    reader = geoip2.database.Reader(GEOIP_DATABASE_PATH)
    try:
        response = reader.city(ip_address)
        country = response.country.name
    except Exception as e:
        country = "Unknown"
        logging.error(f"Error retrieving geolocation: {e}")
    logging.info(f"Search Query: {query}, Country: {country}")
