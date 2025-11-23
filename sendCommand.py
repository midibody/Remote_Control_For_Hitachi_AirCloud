import requests
import json

API_URL = "https://api-global-prod.aircloudhome.com"

HEADERS_COMMON = {
    "Accept": "application/json",
    "Content-Type": "application/json; charset=UTF-8",
    "User-Agent": "okhttp/4.2.2",
    "Host": "api-global-prod.aircloudhome.com",
}

#****************************
"""
Parameters command settings:

mode: "HEATING", "COOLING", "AUTO", "DRY", "FAN"
fanSpeed "AUTO", "LV1" à "LV5"
fanSwing (TBC): "OFF","VERTICAL" pour RAK-DJ25RHAE, "AUTO","UP" (depends on model),"CENTER" (depends on model),"DOWN" (depends on model), 
power: "ON", "OFF"
iduTemperature 16–30 usually
"""
def sendGeneralControlCommand(tokenSecu: str,
                  family_id: str,
                  room_id: int,
                  mode: str,
                  setTemperature: int,
                  relativeTemperature: int,
                  fan_speed: str = "LV2",
                  fan_swing: str = "OFF", 
                  power: str = "ON"):
    url = f"{API_URL}/rac/basic-idu-control/general-control-command/{room_id}?familyId={family_id}"

    payload = {
        "fanSpeed": fan_speed,
        "fanSwing": fan_swing,
        "id": room_id,
        "iduTemperature": setTemperature,
        "relativeTemperature": relativeTemperature,
        "mode": mode,       # ex: "HEATING", "COOLING", "AUTO"
        "power": power,      # "ON" / "OFF"
    }
    print (payload)
    
    headers = {
        **HEADERS_COMMON,
        "Authorization": f"Bearer {tokenSecu}",
    }

    r = requests.put(url, headers=headers, json=payload)
    
    if (r.status_code == 200):
        print ("✅ Commande accepted by the server")
    else:
        print(f"\n⛔ERREUR retourned by Hitachi server = {r.status_code}" )

    #print("=== DEBUG HTTP ===")
    #print("URL :", url)
    #print("Status :", r.status_code)
    #print("Réponse Body :", r.text)

    #r.raise_for_status()
