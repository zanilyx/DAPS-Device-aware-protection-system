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
            timeout=10
        )

        data = response.json()

        return (
            float(data["iss_position"]["latitude"]),
            float(data["iss_position"]["longitude"])
        )

    except Exception as e:

        print(
            "ISS fetch failed:",
            e
        )

        return 0.0, 0.0


# ==========================================================
# MERCURY POSITION
#
# Replace later with real ephemeris API
# ==========================================================

def get_mercury_position():

    planets = load("de421.bsp")

    earth = planets["earth"]
    mercury = planets["mercury"]

    ts = load.timescale()
    t = ts.now()

    position = (
        earth
        .at(t)
        .observe(mercury)
        .position
        .km
    )

    x, y, z = position

    return x, y, z


# ==========================================================
# PHOBOS POSITION
#
# Replace later with real ephemeris API
# ==========================================================

def get_pluto_position():
    planets = load("de421.bsp")

    earth = planets["earth"]
    pluto = planets["PLUTO BARYCENTER"]

    ts = load.timescale()
    t = ts.now()

    position = (
        earth
        .at(t)
        .observe(pluto)
        .position
        .km
    )

    x, y, z = position

    return x, y, z 


# ==========================================================
# GENERATE METADATA
# ==========================================================

def build_metadata():

    iss_lat, iss_lon = get_iss_position()

    mercury_x, mercury_y, mercury_z = (
        get_mercury_position()
    )

    pluto_x, pluto_y, pluto_z = (
        get_pluto_position()
    )

    utc = datetime.utcnow().isoformat()

    metadata = {

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

    return metadata


# ==========================================================
# GENERATE AES-128 KEY
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
    print(material)
    digest = hashlib.sha256(
        material.encode()
    ).digest()

    aes_key = digest[:16]

    return aes_key


# ==========================================================
# SAVE METADATA
# ==========================================================

def save_metadata(metadata):

    with open(
        "encryption_metadata.json",
        "w"
    ) as f:

        json.dump(
            metadata,
            f,
            indent=4
        )


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    metadata = build_metadata()

    key = generate_key(
        metadata
    )

    save_metadata(
        metadata
    )

    print(
        "\nGenerated AES-128 Key:\n"
    )

    print(
        key.hex()
    )

    print(
        "\nMetadata saved to encryption_metadata.json"
    )