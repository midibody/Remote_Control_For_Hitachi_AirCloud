#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import json
import sys
import time
import uuid
import subprocess

import requests

# ======================= VARIABLES =======================

# Fichier de log (facultatif, ici on ne l’utilise pas vraiment)
LOGFILE = "/var/www/html/plugins/script/data/log/aircloud.log"

# Identifiants Hitachi
# Remplace les 2 chaînes ci-dessous par tes valeurs base64
HITACHI_USER_B64 = "<replace with your Hitachi's account email in base64>"
HITACHI_PASS_B64 = "<replace with your Hitachi's account password in base64>"

hitachiuser = base64.b64decode(HITACHI_USER_B64).decode("utf-8")
hitachipassword = base64.b64decode(HITACHI_PASS_B64).decode("utf-8")

# Chemin vers websocat (à adapter pour Windows/Linux)
WEBSOCAT_BINARY = "/home/jeedom/.cargo/bin/websocat"

WSS_AIRCLOUD = "wss://notification-global-prod.aircloudhome.com/rac-notifications/websocket"
PING_TIMEOUT = "5"  # en secondes, laissé en texte pour websocat

API_URL = "https://api-global-prod.aircloudhome.com"

MAX_ATTEMPTS = 6

# Variables globales équivalentes au script bash
token = None
familyId = None
cloudIds = None
connectandsub = None
json_data = ""
roomId = None

powerstatus = None
mode = None
temperature = None
idutemperature = None
fanSpeed = None
fanSwing = None
roomhumidity = None
powerstatusbymode = None
fanSpeedstatus = None
fanSwingstatus = None
scheduletypestatus = None
holidaymodestatus = None
errorstatus = None
onlinestatus = None
idufrostwashstatus = None
relativetemperature = None
specialoperationstatus = None


# ======================= FONCTIONS =======================

def get_info():
    """Authentification et initialisation (token, familyId, connectandsub)."""
    global token, familyId, cloudIds, connectandsub

    # Authentification
    headers_auth = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=UTF-8",
        "User-Agent": "okhttp/4.2.2",
    }
    payload_auth = {
        "email": hitachiuser,
        "password": hitachipassword,
    }
    r = requests.post(f"{API_URL}/iam/auth/sign-in",
                      headers=headers_auth,
                      json=payload_auth)
    r.raise_for_status()
    token = r.json().get("token")

    # who-am-i pour récupérer familyId
    headers_auth_bearer = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "okhttp/4.2.2",
    }
    r = requests.get(f"{API_URL}/iam/user/v2/who-am-i",
                     headers=headers_auth_bearer)
    r.raise_for_status()
    familyId = r.json().get("familyId")

    # cloudIds (non utilisé, mais on reste fidèle au script)
    r = requests.get(f"{API_URL}/rac/ownership/groups/cloudIds/{familyId}",
                     headers=headers_auth_bearer)
    if r.ok:
        cloudIds = r.json()

    # Préparation du payload STOMP CONNECT + SUBSCRIBE (comme dans le bash)
    my_uuid = str(uuid.uuid1())
    stomp_payload = (
        "CONNECT\n"
        "accept-version:1.1,1.2\n"
        "heart-beat:10000,10000\n"
        f"Authorization:Bearer {token}\n"
        "\n\0\n"
        "SUBSCRIBE\n"
        f"id:{my_uuid}\n"
        f"destination:/notification/{familyId}/{familyId}\n"
        "ack:auto\n"
        "\n\0"
    )
    # Encodage base64 comme dans le script bash
    connectandsub_bytes = stomp_payload.encode("utf-8")
    connectandsub_b64 = base64.b64encode(connectandsub_bytes).decode("ascii")
    connectandsub = connectandsub_b64


def websocat_request(room_name: str):
    """
    Lance websocat avec le payload STOMP encodé en base64
    et récupère la trame JSON contenant 'HITACHI'.
    """
    global json_data

    json_data = ""
    attempt = 0

    while not json_data and attempt < MAX_ATTEMPTS:
        try:
            # Commande équivalente à :
            # echo $connectandsub | websocat -b --base64 --ping-timeout=5 -q -n wss://...
            proc = subprocess.run(
                [
                    WEBSOCAT_BINARY,
                    "-b",
                    "--base64",
                    f"--ping-timeout={PING_TIMEOUT}",
                    "-q",
                    "-n",
                    WSS_AIRCLOUD,
                ],
                input=(connectandsub + "\n").encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            out = proc.stdout.decode("utf-8", errors="ignore")

            # Équivalent de: grep -a HITACHI | tr -d "\n" | tr -d "\0"
            lines = [line for line in out.splitlines() if "HITACHI" in line]
            combined = "".join(lines)
            combined = combined.replace("\x00", "").replace("\n", "")

            if combined:
                json_data = combined

        except Exception:
            json_data = ""

        if not json_data:
            time.sleep(5)
            attempt += 1


def _get_room_entry():
    """Retourne l'entrée JSON correspondant au roomId courant."""
    if not json_data:
        return None
    try:
        payload = json.loads(json_data)
    except json.JSONDecodeError:
        return None

    data = payload.get("data", [])
    for item in data:
        if str(item.get("id", "")).startswith(str(roomId)):
            return item
    return None


def get_roomid(room_name: str):
    """Trouve le roomId correspondant au nom de pièce."""
    global roomId

    if not json_data:
        raise RuntimeError("json_data vide, impossible de déterminer le roomId")

    try:
        payload = json.loads(json_data)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"json_data invalide: {e}") from e

    for item in payload.get("data", []):
        if item.get("name") == room_name:
            # Le script bash tronque à 5 caractères
            rid = str(item.get("id", ""))
            roomId = rid[:5]
            return

    raise RuntimeError(f"Pièce '{room_name}' introuvable dans les données AirCloud.")


def get_powerstatus():
    global powerstatus
    entry = _get_room_entry()
    powerstatus = entry.get("power") if entry else None


def get_temperature():
    global temperature
    entry = _get_room_entry()
    temperature = entry.get("roomTemperature") if entry else None


def get_idutemperature():
    global idutemperature
    entry = _get_room_entry()
    idutemperature = entry.get("iduTemperature") if entry else None


def get_mode():
    global mode
    entry = _get_room_entry()
    mode = entry.get("mode") if entry else None


def get_fanSpeed():
    global fanSpeed
    entry = _get_room_entry()
    fanSpeed = entry.get("fanSpeed") if entry else None


def get_fanSwing():
    global fanSwing
    entry = _get_room_entry()
    fanSwing = entry.get("fanSwing") if entry else None


def get_humidity():
    global roomhumidity
    entry = _get_room_entry()
    roomhumidity = entry.get("humidity") if entry else None


def get_powerstatusbymode():
    global powerstatusbymode
    # La version bash a une syntaxe jq un peu bancale, on approximera:
    entry = _get_room_entry()
    if entry and entry.get("mode") == mode:
        powerstatusbymode = entry.get("power")
    else:
        powerstatusbymode = None


def get_fanSpeedstatus():
    global fanSpeedstatus
    entry = _get_room_entry()
    fanSpeedstatus = entry.get("fanSpeed") if entry else None


def get_fanSwingstatus():
    global fanSwingstatus
    entry = _get_room_entry()
    fanSwingstatus = entry.get("fanSwing") if entry else None


def get_scheduletypestatus():
    global scheduletypestatus
    entry = _get_room_entry()
    scheduletypestatus = entry.get("scheduletype") if entry else None


def get_holidaymodestatus():
    global holidaymodestatus
    entry = _get_room_entry()
    val = entry.get("holidayModeStatus", {}).get("active") if entry else None
    holidaymodestatus = val


def get_errorstatus():
    global errorstatus
    entry = _get_room_entry()
    errorstatus = entry.get("errorStatus", {}).get("errorCode") if entry else None


def get_onlinestatus():
    global onlinestatus
    entry = _get_room_entry()
    onlinestatus = entry.get("online") if entry else None


def get_idufrostwashstatus():
    global idufrostwashstatus
    entry = _get_room_entry()
    idufrostwashstatus = entry.get("iduFrostWashStatus", {}).get("active") if entry else None


def get_relativetemperature():
    global relativetemperature
    entry = _get_room_entry()
    relativetemperature = entry.get("relativeTemperature") if entry else None


def get_specialoperationstatus():
    global specialoperationstatus
    entry = _get_room_entry()
    specialoperationstatus = entry.get("specialOperationStatus", {}).get("active") if entry else None


def headers_bearer():
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "okhttp/4.2.2",
    }


# ======================= MAIN =======================

def main():
    if len(sys.argv) < 3:
        # Comme le script bash : il faut au moins action et nom de pièce
        # 1er argument : action (on, off, powerstatus, etc.)
        # 2e argument : nom de la PAC / pièce
        print("Paramètres insuffisants.")
        sys.exit(0)

    action = sys.argv[1]
    room_name = sys.argv[2]

    # Initialisation API + websocket
    get_info()
    websocat_request(room_name)
    get_roomid(room_name)

    # Vérification onlinestatus
    get_onlinestatus()
    if str(onlinestatus).lower() != "true":
        if action == "onlinestatus":
            print("FALSE")
            sys.exit(0)
        sys.exit(0)

    # Dispatch des actions
    if action == "on":
        # on nom_pac mode temperature fanspeed swingmode
        if len(sys.argv) < 7:
            sys.exit(0)

        wanted_mode = sys.argv[3]
        wanted_temp = sys.argv[4]
        wanted_fanSpeed = sys.argv[5]
        wanted_fanSwing = sys.argv[6]

        get_powerstatus()
        get_mode()
        get_idutemperature()
        get_fanSpeed()
        get_fanSwing()

        attempt = 0
        while (
            (
                powerstatus != "ON"
                or mode != wanted_mode
                or (mode != "FAN" and str(idutemperature) != str(wanted_temp))
                or str(fanSpeed) != str(wanted_fanSpeed)
                or str(fanSwing) != str(wanted_fanSwing)
            )
            and attempt < MAX_ATTEMPTS
        ):
            body = {
                "fanSpeed": wanted_fanSpeed,
                "fanSwing": wanted_fanSwing,
                "humidity": "0",
                "id": int(roomId),
                "iduTemperature": wanted_temp,
                "mode": wanted_mode,
                "power": "ON",
            }
            requests.put(
                f"{API_URL}/rac/basic-idu-control/general-control-command/{roomId}?familyId={familyId}",
                headers=headers_bearer(),
                data=json.dumps(body),
            )
            time.sleep(20)
            websocat_request(room_name)
            get_powerstatus()
            get_mode()
            get_idutemperature()
            get_fanSpeed()
            get_fanSwing()
            attempt += 1

    elif action == "off":
        get_powerstatus()
        if powerstatus == "OFF":
            sys.exit(0)

        get_idutemperature()
        get_fanSpeed()
        get_fanSwing()
        get_mode()

        if mode == "FAN":
            # aligné sur le script bash
            idutemperature_local = 0
        else:
            idutemperature_local = idutemperature

        attempt = 0
        while powerstatus != "OFF" and attempt < MAX_ATTEMPTS:
            body = {
                "fanSpeed": fanSpeed,
                "fanSwing": fanSwing,
                "humidity": "0",
                "id": int(roomId),
                "iduTemperature": idutemperature_local,
                "mode": mode,
                "power": "OFF",
            }
            requests.put(
                f"{API_URL}/rac/basic-idu-control/general-control-command/{roomId}?familyId={familyId}",
                headers=headers_bearer(),
                data=json.dumps(body),
            )
            time.sleep(20)
            websocat_request(room_name)
            get_powerstatus()
            attempt += 1

    elif action == "powerstatus":
        get_powerstatus()
        print(powerstatus)

    elif action == "modestatus":
        get_mode()
        print(mode)

    elif action == "roomtemperature":
        get_temperature()
        print(temperature)

    elif action == "idutemperature":
        get_idutemperature()
        print(idutemperature)

    elif action == "websocatdebug":
        # équivalent 'echo $connectandsub | websocat ... | grep HITACHI | jq'
        proc = subprocess.run(
            [
                WEBSOCAT_BINARY,
                "-b",
                "--base64",
                f"--ping-timeout={PING_TIMEOUT}",
                "-q",
                "-n",
                WSS_AIRCLOUD,
            ],
            input=(connectandsub + "\n").encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        out = proc.stdout.decode("utf-8", errors="ignore")
        lines = [line for line in out.splitlines() if "HITACHI" in line]
        combined = "".join(lines).replace("\x00", "")
        try:
            parsed = json.loads(combined)
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
        except Exception:
            print(combined)

    elif action == "websocatdebug2":
        proc = subprocess.run(
            [
                WEBSOCAT_BINARY,
                "-b",
                "--base64",
                f"--ping-timeout={PING_TIMEOUT}",
                "-q",
                "-n",
                WSS_AIRCLOUD,
            ],
            input=(connectandsub + "\n").encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        print(proc.stdout.decode("utf-8", errors="ignore"))

    elif action == "fanSpeedstatus":
        get_fanSpeedstatus()
        print(fanSpeedstatus)

    elif action == "fanSwingstatus":
        get_fanSwingstatus()
        print(fanSwingstatus)

    elif action == "scheduletypestatus":
        get_scheduletypestatus()
        if scheduletypestatus == "SCHEDULE_DISABLED":
            print("DISABLE")
        elif scheduletypestatus in ("ON_OFF_TIMER_ENABLED", "ON_TIMER_ENABLED", "OFF_TIMER_ENABLED"):
            print("SIMPLE")
        elif scheduletypestatus == "WEEKLY_TIMER_ENABLED":
            print("WEEKLY")
        elif scheduletypestatus == "HOLIDAY_MODE_ENABLED":
            print("HOLIDAY")
        else:
            print(scheduletypestatus)

    elif action == "holidaymodestatus":
        get_holidaymodestatus()
        print(str(holidaymodestatus).upper())

    elif action == "errorstatus":
        get_errorstatus()
        if errorstatus is None or errorstatus == "null":
            print("FALSE")
        else:
            print(str(errorstatus).upper())

    elif action == "onlinestatus":
        get_onlinestatus()
        print(str(onlinestatus).upper())

    elif action == "idufrostwashstatus":
        get_idufrostwashstatus()
        print(str(idufrostwashstatus).upper())

    else:
        print('Paramètres incorrects : "action" "nom_pièce" (si action on : "mode" "temperature" "fanspeed" "fanSwing")')

    sys.exit(0)


if __name__ == "__main__":
    main()
