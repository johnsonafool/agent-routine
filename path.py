import networkx as nx
import osmnx as ox
import json
import numpy as np

import math
import os
from typing import NoReturn


##############################################
# utils
##############################################
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
    x = math.acos(
        math.sin(pA) * math.sin(pB)
        + math.cos(pA) * math.cos(pB) * math.cos(radLonA - radLonB)
    )
    c1 = (math.sin(x) - x) * (math.sin(pA) + math.sin(pB)) ** 2 / math.cos(x / 2) ** 2

    if math.sin(x / 2) == 0:
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


##############################################
# utils end
##############################################


##############################################
# for generating newItineraries.json
##############################################
def insert_agent_activity(arr: list) -> NoReturn:
    new_arr = []
    new_start_time = arr[0]["Start time"]
    new_start_time = digit_to_hour_min(arr[0]["Start time"], new_start_time)

    for a_index, _ in enumerate(arr):
        cur_lat = arr[a_index]["lat"]
        cur_log = arr[a_index]["log"]
        cur_activity = arr[a_index]["Activity"]
        cur_place = arr[a_index]["Place"]
        cur_transportation = arr[a_index]["Transportation"]
        cur_duration = arr[a_index]["End time"] - arr[a_index]["Start time"]

        if (a_index + 1) == len(arr):
            tmp = arr[-1]
            new_arr.append(
                {
                    "Activity": tmp["Activity"],
                    "Place": tmp["Place"],
                    "Start time": digit_to_hour_min(new_start_time, new_start_time),
                    "End time": tmp["End time"],
                    "Transportation": tmp["Transportation"],
                    "log": tmp["log"],
                    "lat": tmp["lat"],
                }
            )
            break

        next_lat = arr[a_index + 1]["lat"]
        next_log = arr[a_index + 1]["log"]
        distance = haversine_distance(cur_lat, cur_log, next_lat, next_log)

        new_arr.append(
            {
                "Activity": cur_activity,
                "Place": cur_place,
                "Start time": digit_to_hour_min(new_start_time, new_start_time),
                "End time": digit_to_hour_min(
                    new_start_time + cur_duration, new_start_time
                ),
                "Transportation": cur_transportation,
                "log": cur_log,
                "lat": cur_lat,
            }
        )

        new_start_time += cur_duration

        if distance <= 1.3:
            if distance == 0:
                print("staying ...")
                continue

            # walking_duration unit: min
            print("walking ...")
            walking_duration = int(distance / 5 * 60)
            new_arr.append(
                {
                    "Activity": "Walking",
                    "DurationMinute": walking_duration,
                    "Place": "None",
                    "Start time": digit_to_hour_min(new_start_time, new_start_time),
                    "End time": digit_to_hour_min(
                        new_start_time + walking_duration, new_start_time
                    ),
                    "Transportation": "Walk",
                    "log": "None",
                    "lat": "None",
                }
            )

            new_start_time += walking_duration

        elif distance > 1.3:
            print("driving ...")
            driving_duration = int(distance / 50 * 60)
            new_arr.append(
                {
                    "Activity": "Driving",
                    "DurationMinute": int(driving_duration),
                    "Place": "None",
                    "Start time": digit_to_hour_min(new_start_time, new_start_time),
                    "End time": digit_to_hour_min(
                        new_start_time + driving_duration, new_start_time
                    ),
                    "Transportation": "Car",
                    "log": "None",
                    "lat": "None",
                }
            )

            new_start_time += driving_duration

    with open("newItineraries.json", "w") as f:
        json.dump(new_arr, f, indent=2)


##############################################
# for generating newPath.json
##############################################
def new_shortest_path_algor(graph, mock_data):
    res = {"path": [], "timestamp": []}

    for b_index, behavior in enumerate(mock_data):
        ac = behavior["Activity"]

        if ac == "Walking" or ac == "Driving":
            coords = []
            pre_lng = mock_data[b_index - 1]["log"]
            pre_lat = mock_data[b_index - 1]["lat"]

            next_lng = mock_data[b_index + 1]["log"]
            next_lat = mock_data[b_index + 1]["lat"]

            st = mock_data[b_index]["Start time"]
            ed = mock_data[b_index]["End time"]

            duration = behavior["DurationMinute"]

            origl = ox.nearest_nodes(graph, pre_lng, pre_lat)
            dest = ox.nearest_nodes(
                graph,
                next_lng,
                next_lng,
            )

            route = nx.shortest_path(graph, origl, dest, weight="travel_time")

            # TODO: handle the case that the route is empty
            # TODO: handle decimal to 60 logic
            if len(route) == 1:
                print("---------------------\n\n\n\n")
                print("---------------------")
                continue

            for _, node in nodes.loc[route].iterrows():
                coord = [node.x, node.y]
                coords.append(coord)
                # res["path"].append(coord)

            # add origin and destination coord to the path
            # add at list first postion
            coords.insert(0, [pre_lng, pre_lat])
            coords.append([next_lng, next_lat])
            res["path"] += coords
            all_dist = []

            for c_index, coord in enumerate(coords):
                if c_index == 0:
                    continue

                # count cur and pre coord distance with haversine_distance
                distance = haversine_distance(
                    res["path"][c_index - 1][0],
                    res["path"][c_index - 1][1],
                    coord[0],
                    coord[1],
                )

                all_dist.append(distance)

            weight = np.array(all_dist)
            partition_duration = weight / weight.sum() * duration
            pduraion = partition_duration.tolist()

            # process timestamp
            transportation_method = "walk" if ac == "Walking" else "car"
            res["timestamp"].append(
                {"mode": transportation_method, "time": st}
            )  # first add start time
            for p in pduraion:
                st = round(st + p, 2)
                res["timestamp"].append({"mode": transportation_method, "time": st})

    return res


if __name__ == "__main__":
    os.system("clear")

    # estabilish graph
    location = "Cambridge, MA, USA"
    graph = ox.graph_from_place(location, network_type="drive")
    nodes, edges = ox.graph_to_gdfs(graph)
    geojson = json.loads(edges.to_json())

    # load data
    data = json_file_to_array("newItineraries.json")

    rt = new_shortest_path_algor(graph, data)
    with open("newPath.json", "w") as f:
        json.dump(rt, f)

    print("done")
