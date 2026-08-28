#!/usr/bin/env python3

"""Discover FIWARE stations and manage one MQTT worker per station."""

import os
import time
import unicodedata
import re

import docker
import requests


FIWARE_URL = os.getenv(
    "FIWARE_URL", "https://broker.fiware.urbanplatform.portodigital.pt/v2/entities"
)
MQTT_HOST = os.getenv("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
WORKER_IMAGE = os.getenv("WORKER_IMAGE", "fiware-mqtt-station:local")
WORKER_PREFIX = os.getenv("WORKER_PREFIX", "fiware-station")
POLL_SECONDS = int(os.getenv("DISCOVERY_INTERVAL", "60"))


def normalize_station_name(name):
    normalized = unicodedata.normalize("NFD", name)
    normalized = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", normalized.lower()).strip("_") or "unknown"


def fetch_entities(type_name):
    response = requests.get(FIWARE_URL, params={"type": type_name}, timeout=20)
    response.raise_for_status()
    return response.json()


def station_specs():
    specs = []
    for entity_type, kind in (("WeatherObserved", "weather"), ("AirQualityObserved", "airquality")):
        entities = fetch_entities(entity_type)
        names = {}
        for entity in entities:
            name = entity.get("name", {}).get("value", "").strip()
            entity_id = entity.get("id")
            if not name or not entity_id:
                print(f"WARNING: Ignoring {entity_type} entity without name/id: {entity}", flush=True)
                continue
            safe_name = normalize_station_name(name)
            names[safe_name] = names.get(safe_name, 0) + 1
            station_id = f"{safe_name}_{names[safe_name]}" if names[safe_name] > 1 else safe_name
            specs.append({
                "key": f"{kind}-{station_id}",
                "kind": kind,
                "entity_id": entity_id,
                "station_id": station_id,
                "station_name": name,
            })
    return specs


def worker_name(spec):
    return f"{WORKER_PREFIX}-{spec['key']}"


def ensure_worker(client, spec):
    name = worker_name(spec)
    environment = {
        "FIWARE_URL": FIWARE_URL,
        "MQTT_HOST": MQTT_HOST,
        "MQTT_PORT": str(MQTT_PORT),
        "STATION_KIND": spec["kind"],
        "STATION_ID": spec["station_id"],
        "STATION_NAME": spec["station_name"],
        "ENTITY_ID": spec["entity_id"],
    }
    try:
        container = client.containers.get(name)
        configured = dict(
            item.split("=", 1)
            for item in container.attrs.get("Config", {}).get("Env", [])
            if "=" in item
        )
        if any(configured.get(key) != value for key, value in environment.items()):
            print(f"INFO: Updating worker {name}", flush=True)
            container.remove(force=True)
        else:
            if container.status != "running":
                container.start()
                print(f"INFO: Started worker {name}", flush=True)
            return
    except docker.errors.NotFound:
        pass

    client.containers.run(
        WORKER_IMAGE,
        name=name,
        detach=True,
        restart_policy={"Name": "unless-stopped"},
        network_mode="host",
        environment=environment,
        labels={"fiware-mqtt.managed": "true", "fiware-mqtt.station": spec["key"]},
    )
    print(f"INFO: Created worker {name}", flush=True)


def remove_missing_workers(client, active_keys):
    for container in client.containers.list(all=True, filters={"label": "fiware-mqtt.managed=true"}):
        station_key = container.labels.get("fiware-mqtt.station")
        if station_key not in active_keys:
            print(f"INFO: Removing unavailable worker {container.name}", flush=True)
            container.remove(force=True)


def main():
    client = docker.from_env()
    while True:
        try:
            specs = station_specs()
            active_keys = {spec["key"] for spec in specs}
            for spec in specs:
                ensure_worker(client, spec)
            remove_missing_workers(client, active_keys)
            print(f"INFO: Managing {len(specs)} station workers.", flush=True)
        except Exception as error:
            print(f"ERROR: Station discovery failed: {error}", flush=True)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()