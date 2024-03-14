from fastapi import FastAPI, HTTPException
import uvicorn
import time, os
import random
import redis
import requests

#Controller database connexion setup
redis_host=""
redis_port=6379
r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

left_blinkers = ""
right_blinkers = ""
break_status = ""
speed_profile = 0
speed_limit = 0


platoon_instructions = {
         "leader_instructions":"",
         "follower_1_instructions":"",
         "follower_2_instructions":"",
         "queue_instrucions":""
     }
def lead_processing(data: dict):
    global left_blinkers, right_blinkers, break_status, speed_profile, speed_limit
    speed_profile = data["lead"]["speed"]
    speed_limit = int(r.get("zone_speed"))
    instruction = {
        "acceleration":"",
        "steering":"",
        "current_zone_speed_limit":speed_limit,
    }

    #acceleration
    if data["lead"]["front"] >= 10:
      if data["lead"]["speed"] > speed_limit+5:
         instruction["acceleration"] = "slow_down"
      elif data["lead"]["speed"] < speed_limit-10:
         instruction["acceleration"] = "speed_up"
    else:
        instruction["acceleration"] = "break"
        break_status = "on"

    #streering
    left = [data["lead"]["left"], data["follower_1"]["left"], 
            data["follower_2"]["left"], data["queue"]["left"]]
    right = [data["lead"]["right"], data["follower_1"]["right"], 
            data["follower_2"]["right"], data["queue"]["right"]]
    a = random.randint(1,5)
    if a == 5:
      #steer left
        if min(left) >= 0.5:
            instruction["steering"] = "steer free"
            left_blinkers = "on"
        else:
            instruction["steering"] = "don't steer"
            left_blinkers = "off"
      #steer right
    elif a == 1:
        if min(right) >= 1.5:
            instruction["steering"] = "steer free"
            right_blinkers = "on"

        else:
            instruction["steering"] = "don't steer"
            right_blinkers = "off"
    else:
        instruction["steering"] = "None"
        right_blinkers = "off"
        left_blinkers = "off"

    return instruction
        

   
def follower_processing(data: dict):
    global speed_profile, left_blinkers, right_blinkers
    instruction ={
        "acceleration":"",
        "string_action":"",
        "left_blinker":"",
        "right_blinker":"",

    }

    instruction["left_blinker"] = left_blinkers
    instruction["right_blinker"] = right_blinkers

    #string stability
    if data["front"] > 14:
        instruction["string_action"] = "lower_IV_distance"
    else:
        instruction["string_action"] = "Keep_IV_disatnce"

    #acceleration
    if break_status != 'on':
      if data["speed"] < speed_profile +2:
         instruction["acceleration"] = "slow_down"
      else:
         instruction["acceleration"] = "keep allure"
    else:
        instruction["acceleration"] = "brake"

    return instruction

app = FastAPI()

@app.post("/real_time")
async def store_data(data: dict):
     global platoon_instructions
     global i
     try: 
      platoon_instructions["leader_instructions"] = lead_processing(data)
      platoon_instructions["follower_1_instructions"] = follower_processing(data["follower_1"])
      platoon_instructions["follower_2_instructions"] = follower_processing(data["follower_2"])
      platoon_instructions["queue_instructions"] = follower_processing(data["queue"])
      print(f"Sendind instructions: {platoon_instructions}")
      return platoon_instructions
     except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@app.post("/init")
async def set_service_endpoint(data: dict):
    global redis_host, r
    redis_host = data["db_endpoint"] 
    print(f"Endpoints initialisation Done")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
    print("server running")