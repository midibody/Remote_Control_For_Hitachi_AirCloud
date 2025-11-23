This project is a lightweight Python tool that controls Hitachi AirCloud Go compatible heat pumps through the official cloud API.
It uses the API of the official Hitachi Aircloud Go  App.
This is a non official piece of code, with zero guarantee of maintenability, and certainly bugs.
It runs but this is still WIP !

It retrieves detailed RAC data (power, mode, temperatures, fan settings…), detects changes, logs them, and sends real commands to the cloud.
Examples of device states and changes come directly from the API data and logs in the project .
I initially created it becuse I was upset by the fact teh when using the Weekly timer/ scheduler based on the schedules defined in the Aircloud App, each time the scheduler changes the settings, the fan moves back to AUTO mode, and overwrites the previous fan speed.
This is really painfull.
I also tried to see if the Hitachi server could accept 'schedule delete' APIs, because the Aircloud App is not capable of deleting a schedule entry it has created. I dont understand how the developers could miss that fundamental and basic feature...
But I couldn'd find a working message, by testing multiple different queries format to the server./

What the program does overall:
- Reads full unit status for multiple RACs.
- Fixes unwanted AUTO fan behavior with custom rules: when change to AUTO detected, moves back to your previous fan speed setup.
- Detects any change between 2 measures (temperature, fan, mode…) and logs it.
- Sends commands: ON/OFF, temperature, mode, fan speed, swing.
- basic functions to manage Weekly Timer schedules (read, update, push).
- create a VSC file to then exploit in Excel or PowerBI the informations on RACs

**Exemples of file output:

_RACs status:

[ 2025-11-23 22:08:01 ]  = RACs Details =
[ 2025-11-23 22:08:06 ]  Id=96438  - RDC Est-Salon troubadour       > Power = OFF  mode = HEATING  fanSpeed = LV3   fanSwing = OFF        roomTemp = 21.0  setpointTemp = 20.0  scheduletype = SCHEDULE_DISABLED
[ 2025-11-23 22:08:06 ]  Id=96442  - RDC Est-Chambre                > Power = OFF  mode = HEATING  fanSpeed = LV2   fanSwing = OFF        roomTemp = 20.0  setpointTemp = 20.0  scheduletype = WEEKLY_TIMER_ENABLED

_Schedules list:

[WEEKLY TIMER for bedroom (4 entries) :
[ 2025-11-23 22:08:06 ]  THU   22:00:00  temp -> 18.5    power ON    HEATING
[ 2025-11-23 22:08:06 ]  THU   22:59:00  temp -> 18.0    power ON    HEATING
[ 2025-11-23 22:08:06 ]  FRI   10:46:00  temp -> 18.0    power ON    HEATING
[ 2025-11-23 22:08:06 ]  FRI   17:35:00  temp -> 17.0    power ON    HEATING

_Detecting updates:

[ 2025-11-23 21:00:32 ]  >>> Values changed for RDC Ouest-Chambre :
[ 2025-11-23 21:00:32 ]    - '>>> User or scheduler updated 'fanSpeed' ' : LV1 -> AUTO
[ 2025-11-23 21:00:32 ]    - 'roomTemperature sensor' : 22.0 -> 22.5
[ 2025-11-23 21:00:32 ]    - '>>> User or scheduler updated 'iduTemperature' ' : 21.0 -> 22.0
[ 2025-11-23 21:00:32 ]  >>> Values changed for RDC Ouest-Salon :
[ 2025-11-23 21:00:32 ]    - 'roomTemperature sensor' : 22.0 -> 22.5
[ 2025-11-23 21:00:32 ]  >> FanSpeed AUTO detected on RAC: RDC Ouest-Chambre. Forced switch back to LV1

_CSV lOG:

timestamp	id	name	power	mode	fanSpeed	fanSwing	roomTemperature	setpointTemperature	scheduletype
22/11/2025 14:27	96438	RDC Est-Salon troubadour	ON	HEATING	LV4	VERTICAL	22.5	20.0	SCHEDULE_DISABLED
22/11/2025 14:27	96442	RDC Est-Chambre	OFF	HEATING	LV2	OFF	20.0	19.5	WEEKLY_TIMER_ENABLED
22/11/2025 14:27	101601	RDC Ouest-Chambre	ON	HEATING	LV2	OFF	21.0	20.0	WEEKLY_TIMER_ENABLED
22/11/2025 14:27	101603	RDC Ouest-Salon	ON	HEATING	LV3	VERTICAL	23.0	22.0	WEEKLY_TIMER_ENABLED
