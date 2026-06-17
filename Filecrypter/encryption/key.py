import hashlib
import requests
from datetime import datetime
from skyfield.api import load
import json
import time


def show_progress(stage, steps=20, delay=0.05):
    print(f"\n{stage}")
    for i in range(steps + 1):
        percent = int((i / steps) * 100)
        bar = "#" * i + "-" * (steps - i)
        print(f"\r[{bar}] {percent}%", end="", flush=True)
        time.sleep(delay)
    print()


# ==========================================================
# ISS POSITION
# ==========================================================

def get_iss_position():
    try:
        show_progress("Waiting for ISS API data...")

        response = requests.get(
            "http://api.open-notify.org/iss-now.json",
            timeout=10
        )

        data = response.json()
        lat = float(data["iss_position"]["latitude"])
        lon = float(data["iss_position"]["longitude"])
        print(f"ISS Position: Lat {lat}, Lon {lon}")
        return lat, lon

    except Exception as e:
        print("ISS fetch failed:", e)
        return 0.0, 0.0


def get_mercury_position():
    planets = load("de421.bsp")
    earth = planets["earth"]
    mercury = planets["mercury"]

    ts = load.timescale()
    t = ts.now()

    position = earth.at(t).observe(mercury).position.km
    return tuple(position)


def get_pluto_position():
    planets = load("de421.bsp")
    earth = planets["earth"]
    pluto = planets["PLUTO BARYCENTER"]

    ts = load.timescale()
    t = ts.now()

    position = earth.at(t).observe(pluto).position.km
    return tuple(position)


def build_metadata():
    iss_lat, iss_lon = get_iss_position()

    show_progress("Processing astronomical data...")
    
    mercury_x, mercury_y, mercury_z = get_mercury_position()
    pluto_x, pluto_y, pluto_z = get_pluto_position()
    print(f"Mercury Position (km): X {mercury_x}, Y {mercury_y}, Z {mercury_z}")
    print(f"Pluto Position (km): X {pluto_x}, Y {pluto_y}, Z {pluto_z}")
    utc = datetime.utcnow().isoformat()

    return {
        "iss_lat": iss_lat,
        "iss_lon": iss_lon,
        "mercury_x": mercury_x,
        "mercury_y": mercury_y,
        "mercury_z": mercury_z,
        "pluto_x": pluto_x,
        "pluto_y": pluto_y,
        "pluto_z": pluto_z,
        "utc": utc
    }


# ==========================================================
# GENERATE AES-256 KEY (32 bytes / 256 bits)
# ==========================================================

def generate_key(metadata):
    material = (
        str(metadata["iss_lat"])
        + str(metadata["iss_lon"])
        + str(metadata["mercury_x"])
        + str(metadata["mercury_y"])
        + str(metadata["mercury_z"])
        + str(metadata["pluto_x"])
        + str(metadata["pluto_y"])
        + str(metadata["pluto_z"])
        + metadata["utc"]
    )

    show_progress("Generating AES-256 key...")
    
    aes256_key = hashlib.sha256(
        material.encode()
    ).digest()  # full 32-byte SHA256 digest

    return aes256_key


def save_metadata(metadata):
    with open("encryption_metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)


if __name__ == "__main__":
    metadata = build_metadata()

    key = generate_key(metadata)

    save_metadata(metadata)

    print("\nGenerated AES-256 Key:\n")
    print(key.hex())

    print("\nMetadata saved to encryption_metadata.json")
