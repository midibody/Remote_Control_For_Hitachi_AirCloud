import requests  # pip install requests
import websocket  # pip install websocket-client
import json
import uuid

import time
from datetime import datetime, time as dtime
import os
from dotenv import load_dotenv #pip install python-dotenv

from utilities import *

# ======================================
# CONSTANTES
# ======================================

API_URL = "https://api-global-prod.aircloudhome.com"
WSS_AIRCLOUD = "wss://notification-global-prod.aircloudhome.com/rac-notifications/websocket"
PING_TIMEOUT = 30
MAX_ATTEMPTS = 5

# variables globales
List_RacsDetails = []
List_PreviousRacsDetails = []

json_data = ""
roomId = None
stomp_payload=""

familyId = 0
token=""

headers_common = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=UTF-8",
        "User-Agent": "okhttp/4.2.2",
        "Host": "api-global-prod.aircloudhome.com",
    }

from utilities import *
from sendCommand import *
from schedules import *


#**************************************
def authenticate ():
#**************************************
    global familyId
    global token

    login_payload = { "email": user, "password": password }
    
    try:
        response = requests.post(
            f"{API_URL}/iam/auth/sign-in",
            json    = login_payload,
            headers = headers_common,
            timeout = 20
        )
    except Exception as e:
        log(f"ERROR  LOGIN - sending login request : {e}")
        return None   # ou continue / pass selon ton contexte

    if response.status_code != 200:
        log(f"ERROR LOGIN: status = {response.status_code}, content = {response.text}")
        return None 

    try:
        data = response.json()
    except Exception as e:
        log(f"ERROR parsing JSON authenticate(): {e}")
        return False

    # here its OK
    data = response.json()
    token = data["token"]

    return True

# ======================================
# INFOS COMPTE
# ======================================
def getGlobalInfo():
    global familyId
    global token 
    global fFirstIteration

    headers_auth = {
        **headers_common,
        "Authorization": f"Bearer {token}",
    }

    try:
        r = requests.get(
            f"{API_URL}/iam/user/v2/who-am-i",
            headers=headers_auth,
            timeout=10
        )
    except Exception as e:
        log(f"ERROR getGlobalInfo(): request code → {e}")
        return False

    if r.status_code != 200:
        log(f"ERROR getGlobalInfo(): status={r.status_code}, content={r.text}")
        return False

    try:
        whoami = r.json()
    except Exception as e:
        log(f"ERROR getGlobalInfo(): invalid JSON → {e}")
        return False

    # check essential fied
    if "familyId" not in whoami:
        log(f"ERROR getGlobalInfo(): familyId not found in answer: {whoami}")
        return False

    familyId = whoami["familyId"]
    # returns: {'familyId': xxxxx, 'firstName': 'your first name', 'lastName': 'yourlast name', 'settings': {'outOfHomeAddress': None, 'sensitiveToCold': False, 'temperatureUnit': 'degC', 'outOfHomeLongitude': xxxx.0, 'homeOnWeekdays': False, 'language': 'en', 'outOfHomeRadius': 0.0, 'homeOnWeekends': False, 'outOfHomeRemainderEnabled': False, 'outOfHomeLatitude': -xxx.0}, 'address': {'zipCode': 'xxx', 'city': 'xxx', 'street': 'xxx', 'countryCode': 'xx', 'state': "x", 'addressLine': 'xxx'}, 'phoneNumber': None, 'pictureData': None, 'familyName': 'x', 'roles': [{'level': 1, 'name': 'OWNER', 'id': 1}], 'middleName': None, 'id': xxxx, 'email': 'xxxxxxx'}
    
    if (fFirstIteration):
        info = json.dumps(whoami, indent=4, ensure_ascii=False)
        log("Informations whoami :")
        log(info)



    return True

# ======================================
# 2) WEBSOCKET / STOMP
# ======================================
def extract_json_from_stomp_frame(frame: str) -> str | None:
   
    frame = frame.replace("\x00", "")

    # separate headers / body (STOMP : headers, then empty line, then body)
    parts = frame.split("\n\n", 1)
    if len(parts) != 2:
        return None
    body = parts[1].strip()
    # check its json
    if not body.startswith("{") and not body.startswith("["):
        return None
    return body


#****************************************
def websocket_request(stomp_payload: str) -> bool:
#****************************************
# opens websocket; sends payload STOMP, and get forst body sent by hitachi server

    global json_data

    json_data=""
    attempt = 0

    while not json_data and attempt < MAX_ATTEMPTS:
        ws = None
        try:
            ws = websocket.create_connection(
                WSS_AIRCLOUD,
                timeout=PING_TIMEOUT,
            )

            # Sends CONNECT + SUBSCRIBE
            ws.send(stomp_payload)

            start = time.time()
            while time.time() - start < 30:  # timeout 30s lecture
                frame = ws.recv()

                body = extract_json_from_stomp_frame(frame)

                #print(json.dumps(body, indent=2, ensure_ascii=False))

                if body:
                    # check data parsing works
                    try:
                        _ = json.loads(body)
                        json_data = body

                        break

                    except json.JSONDecodeError:
                        # no valid json
                        pass

        except Exception as e:
            log ("ERROR websocket:", e)
            json_data = ""

        finally:
            if ws is not None:
                ws.close()

        if not json_data:
            log("\n⛔ no JSON data , new try ...")
            attempt += 1
            time.sleep(3)
    
    if (not json_data):
        return False #error
    else:
         return True #OK


#**************************************
def testCommands():
#*****************************

    enable_disable_scheduler(
    token=token,
    family_id=familyId,
    rac_id=96438,
    scheduler_type="WEEKLY_TIMER_ENABLED" # ou "WEEKLY_TIMER_ENABLED" ou SCHEDULE_DISABLED
    )
     
    #****************************
    schedules = get_schedules(
    token = token,
    family_id = familyId,
    rac_id = 96438) #salon troubadour

    print(json.dumps(schedules, indent=2))
  
    #********************************
    update_schedule(
        token=token,
        family_id=familyId,
        rac_id=96438,       # ton unité 101603= RDC Est salon, 96438= salon troubadour
        schedule_id=1361789, # id du créneau existant
        power="ON",
        mode="HEATING",
        temperature=18.5,
        day="THU",
        starts_at="22:00:00",
    )

    #*******************************
    schedules = get_schedules(
    token = token,
    family_id = familyId,
    rac_id = 96438) #salon troubadour

    print(json.dumps(schedules, indent=2))

    sendGeneralControlCommand ( token = token, 
                    family_id = familyId, 
                    room_id = 96438, 
                    mode="HEATING", 
                    setTemperature =20.5,
                    relativeTemperature = 1,
                    fan_speed = "LV2", 
                    fan_swing= "VERTICAL",
                    power = "ON")
    

#****************************
def testScheduleDeleteCommand():
#function to delete a scedule not existing in the Hitachi Aircloud App, trying different messages formats to see if it exists on the server ...
#****************************
    global token
    global familyId

    schedules = get_schedules(
    token,
    familyId,
    rac_id = 96438) #salon troubadour

    print(json.dumps(schedules, indent=2))
   
    delete_schedule(
        token,
        familyId,
        rac_id=96438,      
        schedule_id=1361789) # id of existing scheduleId
    
#***************************************
def getAllRacDetails():

    global List_RacsDetails

    my_uuid = str(uuid.uuid4()) # create a random and hopefuly inique ID

    connect_frame = (
        "CONNECT\n"
        "accept-version:1.1,1.2\n"
        "heart-beat:10000,10000\n"
        f"Authorization:Bearer {token}\n"
        "\n"
        "\x00"
    )

    subscribe_frame = (
        "SUBSCRIBE\n"
        f"id:{my_uuid}\n"
        f"destination:/notification/{familyId}/{familyId}\n"
        "ack:auto\n"
        "\n"
        "\x00"
    )

    stomp_payload = connect_frame + subscribe_frame
    if (websocket_request( stomp_payload) == True):

        # Liste all RACs
        parsed= json.loads(json_data) # raise JSONDecodeError("Expecting value", s, err.value) from None
        List_RacsDetails = parsed["data"]
        # order by ascending ID
        List_RacsDetails = sorted( List_RacsDetails, key=lambda rac: rac["id"])

        # parse each RAC
        for rac in List_RacsDetails:

            updatedAt = dateToText (rac["updatedAt"])

            lastOnlineUpdatedAt = dateToText ( rac["lastOnlineUpdatedAt"]) #dt.strftime("%Y-%m-%d %H:%M")

            # log (f'Id={rac["id"]:<6} - {rac["name"]:<30} > Power = {rac["power"]:<4} mode = {rac["mode"]:<8} fanSpeed = {rac["fanSpeed"]:<5} fanSwing = {rac["fanSwing"]:<10} roomTemp = {rac["roomTemperature"]:<5} setpointTemp = {rac["iduTemperature"]:<5} scheduletype = {rac["scheduletype"]:<21} updatedAt = {updatedAt} lastOnlineUpdatedAt = {lastOnlineUpdatedAt} ' )
            log (f'Id={rac["id"]:<6} - {rac["name"]:<30} > Power = {rac["power"]:<4} mode = {rac["mode"]:<8} fanSpeed = {rac["fanSpeed"]:<5} fanSwing = {rac["fanSwing"]:<10} roomTemp = {rac["roomTemperature"]:<5} setpointTemp = {rac["iduTemperature"]:<5} scheduletype = {rac["scheduletype"]:<21}' )
            logCSV (rac)
        return True;
    else:
        return False

#***************************************
def getAllRacsSchedules():

    global List_RacsDetails

    # parse each RAC
    for rac in List_RacsDetails:
        get_schedules(token, familyId , rac["id"], rac["name"] )

#***********************
def checkRacsChanges():
#***********************
#     
    global List_PreviousRacsDetails

    prev_by_id = {r["id"]: r for r in List_PreviousRacsDetails}

    # Fields to check
    FIELDS_TO_CHECK = (
        "power",
        "mode",
        "fanSpeed",
        "fanSwing",
        "roomTemperature",
        "iduTemperature",
        "scheduletype",
    )

    # parse each RAC
    for rac in List_RacsDetails:

        previous = prev_by_id.get(rac["id"])
        if previous is None:
            continue

        changes = []
        for field in FIELDS_TO_CHECK:
            
            old = previous.get(field)
            new = rac.get(field)
            #print (f"old= {old}, new={new}")
            if old != new:
                if (field == "roomTemperature"):
                    text= "roomTemperature sensor"
                else:
                    text = ">>> User or scheduler updated '" + field +"' "
                changes.append((text, old, new))

        if changes:
            
            log(f">>> Values changed for {rac['name']} :")
            for field, old, new in changes:
                log(f"  - '{field}' : {old} -> {new}")


#***********************
def CheckContextAndTriggerActions():
#***********************
    global List_PreviousRacsDetails

    for idx, rac in enumerate(List_RacsDetails):
        previousFanSpeed= ""

        if rac["fanSpeed"] == "AUTO" and rac["power"] == "ON": # remove fanSpeed AUTO, dont do it if power was switched off as it generates useless 'beep'
            fanSpeedTarget= "LV2" #by default

            if (List_PreviousRacsDetails): #retrieve previous fanSpeed
                previousRac = List_PreviousRacsDetails[idx]
                fanSpeedTarget = previousRac["fanSpeed"]

                if (fanSpeedTarget == "AUTO"): #if we were already in AUTO
                    fanSpeedTarget = "LV2"

            log (f'>> FanSpeed AUTO detected on RAC: {rac["name"]}. Forced switch back to {fanSpeedTarget}')
            sendGeneralControlCommand (tokenSecu = token,
                  family_id = familyId,
                  room_id = rac["id"], 
                  mode = rac["mode"], 
                  setTemperature= rac["iduTemperature"], 
                  relativeTemperature=  rac["relativeTemperature"], 
                  fan_speed =  fanSpeedTarget, 
                  fan_swing =  rac["fanSwing"], 
                  power =  rac["power"], )
            rac ["fanSpeed"] = fanSpeedTarget #trick to not detect and log again a change at the next iteration, as we forced the new value here

        # to force temp decrase by some time slot if user put too high setpoint
        reducedTemp = 22.5
        now = datetime.now().time()
        if dtime(20,45) <= now <= dtime(21,00) and rac["iduTemperature"] > reducedTemp:

            log(f'>> Too high setpoint Temperature ({rac["iduTemperature"]}) on RAC: {rac["name"]}, between time limits ({dtime(20,45)} - {dtime(21,00)}). Reduced to {reducedTemp}')
            sendGeneralControlCommand (tokenSecu = token,
                  family_id = familyId,
                  room_id = rac["id"], 
                  mode = rac["mode"], 
                  setTemperature= reducedTemp, 
                  relativeTemperature=  rac["relativeTemperature"], 
                  fan_speed =  fanSpeedTarget, 
                  fan_swing =  rac["fanSwing"], 
                  power =  rac["power"], )
            
# ======================================
# MAIN
# ======================================
if __name__ == "__main__":
    
    load_dotenv()
    user = os.getenv("HITACHI_USER")
    password = os.getenv("HITACHI_PASSWORD")

    log (">>>>>>> App Started")
    fFirstIteration = True

    while True:
        if authenticate():
    
            if getGlobalInfo():
                #log (f"FamilyId : {familyId}")
                
                log ("= RACs Details =")

                if getAllRacDetails():
                    if (fFirstIteration):
                        getAllRacsSchedules() #to log the weekly schedules details in the log file

                    checkRacsChanges()
                    CheckContextAndTriggerActions()
                    List_PreviousRacsDetails = List_RacsDetails 

                time.sleep(5*60)   # secondes
                fFirstIteration = False

    #testCommands()

    """
    for test of delecte schedule...    
    authenticate()
    getGlobalInfo()
    testScheduleDeleteCommand()
    """

    
