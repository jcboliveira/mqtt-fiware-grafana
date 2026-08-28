#!/usr/bin/env python3

"""Fetch one FIWARE station and publish its values to the original MQTT topics."""

import json
import os
import time
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

import paho.mqtt.client as mqtt
import requests
from dateutil import parser


FIWARE_URL = os.getenv("FIWARE_URL", "https://broker.fiware.urbanplatform.portodigital.pt/v2/entities")
MQTT_HOST = os.getenv("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
KIND = os.environ["STATION_KIND"]
STATION_ID = os.environ["STATION_ID"]
STATION_NAME = os.environ["STATION_NAME"]
ENTITY_ID = os.environ["ENTITY_ID"]
BASE = f"fiware/{KIND}/{STATION_ID}"


def get_value(entity, field):
    attribute = entity.get(field)
    return attribute.get("value") if isinstance(attribute, dict) and "value" in attribute else None


def aqi(value, breakpoints):
    for low, high, aqi_low, aqi_high in breakpoints:
        if low <= value <= high:
            return round((aqi_high - aqi_low) / (high - low) * (value - low) + aqi_low)
    return None


def compute_aqi(entity):
    definitions = {
        "pm25": [(0, 12, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150), (55.5, 150.4, 151, 200)],
        "pm10": [(0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150)],
        "o3": [(0, 100, 0, 100), (101, 160, 101, 150)],
        "no2": [(0, 100, 0, 100), (101, 200, 101, 150)],
    }
    values = {field: aqi(get_value(entity, field), points) for field, points in definitions.items() if get_value(entity, field) is not None}
    values = {field: value for field, value in values.items() if value is not None}
    return (max(values.values()), max(values, key=values.get)) if values else (None, "unknown")


def publish_discovery(client):
    fields = {
        "weather": [("temperature", "Temperatura", "°C", "temperature"), ("relativeHumidity", "Humidade", "%", "humidity"), ("windSpeed", "Velocidade do vento", "km/h", None), ("precipitation", "Precipitação", "mm", None), ("uVIndexMax", "Índice UV", None, None), ("latitude", "Latitude", None, None), ("longitude", "Longitude", None, None)],
        "airquality": [("pm25", "PM2.5", "µg/m³", None), ("pm10", "PM10", "µg/m³", None), ("no2", "NO₂", "µg/m³", None), ("o3", "O₃", "µg/m³", None), ("co", "CO", "µg/m³", None), ("aqi", "AQI", None, None), ("main_pollutant", "Poluente Principal", None, None), ("latitude", "Latitude", None, None), ("longitude", "Longitude", None, None)],
        "noise": [("LAeq", "Nível sonoro equivalente", "dB", None), ("latitude", "Latitude", None, None), ("longitude", "Longitude", None, None)],
    }[KIND]
    for field, name, unit, device_class in fields:
        payload = {"name": name, "unique_id": f"{KIND}_{STATION_ID}_{field}", "state_topic": f"{BASE}/{field}", "device": {"identifiers": [f"fiware_{KIND}_{STATION_ID}"], "name": STATION_NAME, "manufacturer": "Porto Digital", "model": "FIWARE"}}
        if unit:
            payload["unit_of_measurement"] = unit
        if device_class:
            payload["device_class"] = device_class
        client.publish(f"homeassistant/sensor/{payload['unique_id']}/config", json.dumps(payload), retain=True)


def fetch_entity():
    response = requests.get(f"{FIWARE_URL}/{quote(ENTITY_ID, safe='')}", timeout=20)
    response.raise_for_status()
    return response.json()


def publish_entity(client, entity):
    if KIND == "weather":
        fields = ("precipitation", "temperature", "windSpeed", "relativeHumidity", "uVIndexMax", "uv_index")
    elif KIND == "airquality":
        fields = ("co", "no2", "o3", "pm1", "pm10", "pm25", "temperature")
    else:
        fields = ("LAeq",)
    for field in fields:
        value = get_value(entity, field)
        if value is None:
            continue
        if field == "relativeHumidity" and value <= 1:
            value = round(value * 100, 1)
        if field == "windSpeed":
            value = round(value * 3.6, 1)
        client.publish(f"{BASE}/{field}", value, retain=True)
    coordinates = get_value(entity, "location")
    if coordinates and coordinates.get("coordinates"):
        lon, lat = coordinates["coordinates"]
        client.publish(f"{BASE}/latitude", lat, retain=True)
        client.publish(f"{BASE}/longitude", lon, retain=True)
    client.publish(f"{BASE}/local", STATION_NAME, retain=True)
    for field in ("dateObserved",):
        value = get_value(entity, field)
        if value is not None:
            client.publish(f"{BASE}/{field}", value, retain=True)
    if KIND == "airquality":
        current_aqi, pollutant = compute_aqi(entity)
        if current_aqi is not None:
            client.publish(f"{BASE}/aqi", current_aqi, retain=True)
        client.publish(f"{BASE}/main_pollutant", pollutant, retain=True)
    client.publish(f"{BASE}/last_mqtt_update", datetime.now(timezone.utc).isoformat(), retain=True)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, 60)
            client.loop_start()
            publish_discovery(client)
            while True:
                entity = fetch_entity()
                observed = get_value(entity, "dateObserved")
                if observed:
                    age = datetime.now(timezone.utc) - parser.parse(observed)
                    if age > timedelta(days=1):
                        print(f"WARNING: {STATION_NAME} has stale data.", flush=True)
                    else:
                        publish_entity(client, entity)
                else:
                    publish_entity(client, entity)
                time.sleep(60)
        except Exception as error:
            print(f"ERROR: Worker {STATION_NAME}: {error}; retrying in 10s", flush=True)
            time.sleep(10)


if __name__ == "__main__":
    main()