import hashlib
import requests
from datetime import datetime
from skyfield.api import load
import json


# ==========================================================
# ISS POSITION
# ==========================================================

def get_iss_position():
    try:
        response = requests.get(
            "http://api.open-notify.org/iss-now.json",
            timeout=3
        )

        data = response.json()
        lat = float(data["iss_position"]["latitude"])
        lon = float(data["iss_position"]["longitude"])
        return lat, lon

    except Exception as e:
        print("ISS fetch failed:", e)
        return 0.0, 0.0


# ==========================================================
# PLANET POSITIONS
# (loads the ephemeris file once and reuses it for both
# Mercury and Pluto, instead of loading it twice)
# ==========================================================

def get_planet_positions():
    planets = load("de421.bsp")
    earth = planets["earth"]

    ts = load.timescale()
    t = ts.now()

    mercury_position = earth.at(t).observe(planets["mercury"]).position.km
    pluto_position = earth.at(t).observe(planets["PLUTO BARYCENTER"]).position.km

    return tuple(mercury_position), tuple(pluto_position)


def build_metadata():
    iss_lat, iss_lon = get_iss_position()

    mercury_x, mercury_y, mercury_z = None, None, None
    pluto_x, pluto_y, pluto_z = None, None, None

    (mercury_x, mercury_y, mercury_z), (pluto_x, pluto_y, pluto_z) = get_planet_positions()

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