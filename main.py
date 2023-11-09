import math
import json

from typing import NoReturn, List


def digit_to_hour_min(number: int, new_start_time: int) -> int:
    hours = number // 100
    minutes = number % 100
    if minutes > 59:
        hours += 1
        minutes -= 60
        new_start_time += 60        
        digit_to_hour_min(new_start_time, new_start_time)

    return hours * 100 + minutes


def haversine_distance(latA: float, lonA: float, latB: float, lonB: float) -> float:
    ra = 6378140
    rb = 6356755
    flatten = (ra - rb) / ra
    
    radLatA = math.radians(latA)
    radLonA = math.radians(lonA)
    radLatB = math.radians(latB)
    radLonB = math.radians(lonB)

    pA = math.atan(rb / ra * math.tan(radLatA))
    pB = math.atan(rb / ra * math.tan(radLatB))
    x = math.acos(math.sin(pA) * math.sin(pB) + math.cos(pA) * math.cos(pB) * math.cos(radLonA - radLonB))
    c1 = (math.sin(x) - x) * (math.sin(pA) + math.sin(pB)) ** 2 / math.cos(x / 2) ** 2
    
    if (math.sin(x / 2) == 0):        
        return 0
    
    c2 = (math.sin(x) + x) * (math.sin(pA) - math.sin(pB)) ** 2 / math.sin(x / 2) ** 2
    dr = flatten / 8 * (c1 - c2)
    distance = ra * (x + dr)
    distance = round(distance / 1000, 4)

    return distance


def json_file_to_array(json_file: str) -> list:
    with open(json_file) as f:
        data = json.load(f)
    return data


def insert_agent_activity(arr: list) -> NoReturn:
    new_arr = []
    new_start_time = arr[0]['Start time']
    new_start_time = digit_to_hour_min(arr[0]['Start time'], new_start_time)

    for a_index, _ in enumerate(arr):
        cur_lat = arr[a_index]['lat']
        cur_log = arr[a_index]['log']
        cur_activity = arr[a_index]['Activity']
        cur_place = arr[a_index]['Place']
        cur_transportation = arr[a_index]['Transportation']        
        cur_duration = arr[a_index]['End time'] - arr[a_index]['Start time']
    
        if (a_index + 1) == len(arr):
            tmp = arr[-1]
            new_arr.append({
                'Activity': tmp['Activity'],                
                'Place': tmp['Place'],
                'Start time': digit_to_hour_min(new_start_time, new_start_time),
                'End time': tmp['End time'],
                'Transportation': tmp['Transportation'],
                'log': tmp['log'],
                'lat': tmp['lat'],
            })
            break

        next_lat = arr[a_index + 1]['lat']
        next_log = arr[a_index + 1]['log']
        distance = haversine_distance(cur_lat, cur_log, next_lat, next_log)

        new_arr.append({
            'Activity': cur_activity,
            'Place': cur_place,
            'Start time': digit_to_hour_min(new_start_time, new_start_time),
            'End time': digit_to_hour_min(new_start_time + cur_duration, new_start_time),
            'Transportation': cur_transportation,
            'log': cur_log,
            'lat': cur_lat,                        
        })

        new_start_time += cur_duration

        if (distance <= 1.3):
            if (distance == 0):            
                print('staying ...')
                continue

            # walking_duration unit: min
            print('walking ...')
            walking_duration = int(distance / 5 * 60)
            new_arr.append({
                'Activity': 'Walking',
                'DurationMinute': walking_duration,
                'Place': 'None',
                'Start time': digit_to_hour_min(new_start_time, new_start_time),
                'End time': digit_to_hour_min(new_start_time + walking_duration, new_start_time),
                'Transportation': 'Walk',
                'log': 'None',
                'lat': 'None',
            })

            new_start_time += walking_duration

        elif (distance > 1.3):
            print('driving ...')
            driving_duration = int(distance / 50 * 60)
            new_arr.append({
                'Activity': 'Driving',
                'DurationMinute': int(driving_duration),
                'Place': 'None',
                'Start time': digit_to_hour_min(new_start_time, new_start_time),
                'End time': digit_to_hour_min(new_start_time + driving_duration, new_start_time),
                'Transportation': 'Car',
                'log': 'None',
                'lat': 'None',
            })    

            new_start_time += driving_duration      

    with open('newItineraries.json', 'w') as f:
        json.dump(new_arr, f, indent=2)


if __name__ == '__main__':
    arr = json_file_to_array('itineraries.json')
    insert_agent_activity(arr)