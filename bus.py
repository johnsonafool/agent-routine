import requests
import json
import pandas as pd
import numpy as np

# res = requests.get('https://tdx.transportdata.tw/api/basic/v2/Bus/Shape/City/Taipei?%24format=JSON')

# print((res.text))

with open ('./data.json', 'r') as f:
    data = json.load(f)


def _split(linestr:str) -> str:
    if linestr[:10] == 'LINESTRING':
        linestr = linestr[10:]
    else:
        linestr = linestr[15:]

    linestr = linestr.replace(',', ' ')
    linestr = linestr.replace('(', ' ')
    linestr = linestr.replace(')', ' ')
    linestr = [i for i in linestr.split() if i != '']
    _len = len(linestr) if len(linestr)%2==0 else len(linestr) -1
    tmp = []
    for i in range(0, _len, 2):
        tmp.append([float(linestr[i]), float(linestr[i+1][:-1])])
    
    return len(tmp), str(tmp)    

records = []
for RoadGeometry in data:
    if len(RoadGeometry['SubRouteName']) == 0:
        Count, tmp = _split(RoadGeometry['Geometry'])
                        
        records.append((Count))
        records.append((Count))
        # 2 possible
    else:
        Count, tmp = _split(RoadGeometry['Geometry'])
        records.append((Count))

print(records)

# for d in data:
#     print(d['Geometry'])
#     break