import token
import requests

from utilities import *

API_URL = "https://api-global-prod.aircloudhome.com"

#************************************
def enable_disable_scheduler(token: str, family_id: int, rac_id: int, scheduler_type: str):
#************************************
#    scheduler_type = "SCHEDULE_ENABLED" ou "SCHEDULE_DISABLED"

    url = f"{API_URL}/rac/scheduled-operations/racs/schedules/enableDisable/{rac_id}"

    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    params = {
        "familyId": family_id
    }

    payload = {
        "schedulerType": scheduler_type
    }

    print(f"[enable_disable_scheduler] POST {url} params={params}")
    print(f"[enable_disable_scheduler] payload={payload}")

    r = requests.post(url, headers=headers, params=params, json=payload)
    print("[enable_disable_scheduler] HTTP", r.status_code)
    print("[enable_disable_scheduler] response:", r.text)

    r.raise_for_status()

    try:
        return r.json()
    except ValueError:
        return None



#************************************
def get_schedules(token: str, family_id: int,rac_id: int, rac_name: str):
#************************************
#    Gets schedules for a specific RAC  
#   GET /rac/scheduled-operations/weekly-timer/racs/{racId}/schedules?familyId={familyId}
    
    url = f"{API_URL}/rac/scheduled-operations/weekly-timer/racs/{rac_id}/schedules"

    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    params = {
        "familyId": family_id
    }

    #print(f"[get_schedules] GET {url} params={params}")

    r = requests.get(url, headers=headers, params=params)
    #r.raise_for_status() BUG: AJOUTER GESTION ERREUR!!!!

    schedules = r.json()
    log (f"\n[WEEKLY TIMER for {rac_name} ({len(schedules)} entries) :")

    # --- affichage détaillé, 1 ligne par schedule ---
    for sch in schedules:
        log (
           
            f"{str(sch.get('day', '')):<4}  "
            f"{str(sch.get('startsAt', '')):<8}  "
            f"temp -> {str(sch.get('temperature', '')):<6}  "
            f"power {str(sch.get('power', '')):<4}  "
            f"{str(sch.get('mode', '')):<10}  "
            #f"racId = {str(sch.get('racId', '')):<6}  "
            #f"Scheduleid = {str(sch.get('id', '')):<8}  "
            #f"zoneIndexValues valeur={str(sch.get('zoneIndexValues', '')):<20}"
        )
    return schedules

#*********************************************
def update_schedule(
#*********************************************
    token: str,
    family_id: int,
    rac_id: int,
    schedule_id: int,
    power: str,
    mode: str,
    temperature: int,
    day: str,
    starts_at: str,
    zone_index_values=None,
):
    """
    Met à jour un créneau du weekly timer (requête PUT).
    
    {
      "power" : "ON",
      "day" : "WED",
      "startsAt" : "22:00:00",
      "temperature" : 18,
      "zoneIndexValues" : [],
      "racId" : 101603,
      "mode" : "HEATING",
      "id" : 1381926
    }
    """
    if zone_index_values is None:
        zone_index_values = []

    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    params = {
        "familyId": family_id,
    }
    # test to check if we can force a fanSpeed in the schedule... no way apparently. No error returned but nothing updated on hte server.
    payload = {
        
        "power": power,
        "day": day,
        "startsAt": starts_at,
        "temperature": temperature,
        "zoneIndexValues": zone_index_values,
        "racId": rac_id,
        "mode": mode,
        "id": schedule_id,
        }

    url = f"{API_URL}/rac/scheduled-operations/weekly-timer/racs/schedules"

    print(f"[update_schedule] PUT {url} params={params}")
    print(f"[update_schedule] payload = {payload}")

    r = requests.put(url, headers=headers, params=params, json=payload)

    print("=== DEBUG HTTP ===")
    print("URL :", url)
    print("Status :", r.status_code)
    print("Réponse Body :", r.text)

    #r.raise_for_status()

    try:
        resp_json = r.json()
        print("[update_schedule] JSON Response:", resp_json)
        return resp_json
    except ValueError:
        print("[update_schedule] 200/201 recieved, but non JSON found")
        return None

#*********************************************
def delete_schedule(
#delete schedule does not eexist in Aircloud App; several tries to see if the server cudl handle it, but.... no way to know the proper request, so, made several unsuccessfull tries
#*********************************************
    token: str,
    family_id: int,
    rac_id: int,
    schedule_id: int):

    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    params = {        "familyId": family_id,}

    #url = f"{API_URL}/rac/scheduled-operations/weekly-timer/racs/schedules/delete/{schedule_id}"
    #404 r = requests.post(url, headers=headers, params=params)
    #404 r = requests.post(url, headers=headers, params=params)

    #url = f"{API_URL}/rac/scheduled-operations/weekly-timer/racs/schedules/remove/{schedule_id}"
    # 404: url = f"{API_URL}/rac/scheduled-operations/weekly-timer/racs/{rac_id}/delete-schedules" #PUT or Post
    #r = requests.post(url, headers=headers, params=params)
    #url = f"{API_URL}/rac/scheduled-operations/weekly-timer/racs/{rac_id}/delete" #PUT or Post
    url = f"{API_URL}/rac/scheduled-operations/weekly-timer/racs/{rac_id}/delete" #PUT or Post

    r = requests.post (url, headers=headers, params=params)

    print("=== DEBUG HTTP ===")
    print("URL :", url)
    print("Status :", r.status_code)
    print("Réponse Body :", r.text)

    #r.raise_for_status()

    # Certains endpoints renvoient un body vide, on gère les deux cas.
    try:
        resp_json = r.json()
        print("[delete_schedule] JSON response:", resp_json)
        return resp_json
    except ValueError:
        print("[delete_schedule] 200/201 received, but no JSON found")
        return None
