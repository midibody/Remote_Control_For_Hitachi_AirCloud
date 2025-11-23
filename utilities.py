import os
import csv
from datetime import datetime

filename="RacsStatus.csv"

#************************************
def dateToText (dateBinary):
#************************************

    ts_ms = dateBinary 
    ts_sec = ts_ms / 1000.0    # conversion millisecondes → secondes
    dt = datetime.fromtimestamp(ts_sec)
    text = dt.strftime("%Y-%m-%d %H:%M")
    return text

#**************************************
def log(*args):
    message = " ".join(str(a) for a in args)
    
    # Timestamp AAAA-MM-JJ HH:MM:SS
    ts = datetime.now().strftime("[ %Y-%m-%d %H:%M:%S ]  ")
    
    message = ts + message
    print(message)
    message = message + "\n"

    try:
        with open("log.txt", "a", encoding="utf-8", errors="replace") as f:
            f.write(message)
    except Exception as e:

        print(f"[LOG ERROR] Impossible to write in log.txt : {e}")
        
#************************************
def logCSV(rac):
#************************************
    # CSV columns, with ; as separator (Europ)!!

    fieldnames = [
        "timestamp",
        "id",
        "name",
        "power",
        "mode",
        "fanSpeed",
        "fanSwing",
        "roomTemperature",
        "setpointTemperature",
        "scheduletype",
        "updatedAt",
        "lastOnlineUpdatedAt"
    ]

    file_exists = os.path.isfile(filename)

    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')

        if not file_exists:
            writer.writeheader()

        row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "id": rac["id"],
            "name": rac["name"],
            "power": rac["power"],
            "mode": rac["mode"],
            "fanSpeed": rac["fanSpeed"],
            "fanSwing": rac["fanSwing"],
            "roomTemperature": rac["roomTemperature"],
            "setpointTemperature": rac["iduTemperature"],
            "scheduletype": rac["scheduletype"],
            "updatedAt": dateToText (rac["updatedAt"]),
            "lastOnlineUpdatedAt": dateToText ( rac["lastOnlineUpdatedAt"])
        }

        writer.writerow(row)