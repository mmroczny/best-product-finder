import requests
import csv

from requests.api import head
import b_keys_headers as bkh
import re
from loguru import logger
import redis
import json

logger.add('logi.log')

headers = {
        "Content-Type": 'application/vnd.allegro.public.v1+json',
        "Accept": 'application/vnd.allegro.public.v1+json',
        "Authorization": f"Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2MjM4NzgyNTcsInVzZXJfbmFtZSI6IjYwMjYzMDQ5IiwianRpIjoiZGZjN2VkZWItNWEyYi00NTIwLTg1YmEtYzVmYzI5ZGJmMWU5IiwiY2xpZW50X2lkIjoiNzllODM2MWZlYTUwNDIwNWE2MjM5ZGQyMGY1ZGQ2MjEiLCJzY29wZSI6WyJhbGxlZ3JvOmFwaTpvcmRlcnM6cmVhZCIsImFsbGVncm86YXBpOnByb2ZpbGU6d3JpdGUiLCJhbGxlZ3JvOmFwaTpzYWxlOm9mZmVyczp3cml0ZSIsImFsbGVncm86YXBpOmJpbGxpbmc6cmVhZCIsImFsbGVncm86YXBpOmNhbXBhaWducyIsImFsbGVncm86YXBpOmRpc3B1dGVzIiwiYWxsZWdybzphcGk6YmlkcyIsImFsbGVncm86YXBpOnNhbGU6b2ZmZXJzOnJlYWQiLCJhbGxlZ3JvOmFwaTpvcmRlcnM6d3JpdGUiLCJhbGxlZ3JvOmFwaTphZHMiLCJhbGxlZ3JvOmFwaTpwYXltZW50czp3cml0ZSIsImFsbGVncm86YXBpOnNhbGU6c2V0dGluZ3M6d3JpdGUiLCJhbGxlZ3JvOmFwaTpwcm9maWxlOnJlYWQiLCJhbGxlZ3JvOmFwaTpyYXRpbmdzIiwiYWxsZWdybzphcGk6c2FsZTpzZXR0aW5nczpyZWFkIiwiYWxsZWdybzphcGk6cGF5bWVudHM6cmVhZCJdLCJhbGxlZ3JvX2FwaSI6dHJ1ZX0.PYvMdlS74xaHaUi9-amnndTFirGXYVtflsNXfSBwd4MTbB4eNvEyzEXd41jsXqp2l8nuGwjgzUDKqPjT8zdhVbmWhxBgS9lw2ZQ1a_bHQbT-geKtmLY3vxaUk82QxPqUv_Mpv6llkE0oaiSfSwP_HyCx_vZym-P0b_H4_B3ppFBS8skJh8tkxp95bJ9bZ-y_oraDy2EgWymWokDITGSXFBXwJukdIgtrX2-ZuG7fm8YWtJWTenfsdx9Jmxw4joZwi9JP2xM_JsI1fqOgmepnpUeGHB_3FiHoPipARjESm78hUe1bRs36wshe2zmlfDzqHoyJOZ_-5XE_hwgDK905Mg"
    }


# costam = set()
with open('kamo.csv', 'r') as fout:

    for x in csv.reader(fout, delimiter = ','):
        costam.add((x[0]))

costam = ['']

with open('nazwy_zrobione.csv', 'r') as fout:
    done2 = [x for x in csv.reader(fout) if len(x) >0]


def get_prod(headers, number= '171530', name= 'FEBI'):


    params = {"phrase": number +' '+name}
    print(params)


    logger.info(f'Sprawdzanie: {number}{name}')

    prodURL = "https://api.allegro.pl/sale/products"

    prod = requests.get(prodURL, headers=headers, params= params)

    
    logger.info(prod.content)
    
    if prod.status_code >= 401 and prod.status_code <= 403:
        raise Exception('Token expired')

    prod = prod.json()


    simi = []

    if prod['products']:
        for x in prod['products']:

            stripNum = number.lstrip(' ')
            nameCheck = re.search(fr"\b{name}\b", x['name'], flags=re.IGNORECASE)
            numberCheck = re.search(fr"\b{stripNum}\b", x['name'], flags=re.IGNORECASE)
            
            if name == 'BOSCH' and not numberCheck:
                str(stripNum).replace(' ', '')
                numberCheck = re.search(fr"\b{stripNum}\b", x['name'], flags=re.IGNORECASE)



            simi.append(x)         
    else:
        logger.warning('Brak atrybutu products.')
        return

    
    if len(simi) == 1:

        itemURL = "https://api.allegro.pl/sale/products/" + str(simi[0]['id'])
        ite = requests.get(itemURL, headers=headers).json()
        logger.success(f'Dodano (1) - {ite["id"]}, {name}, {number}')
        a = open('produktyzacja.csv','a')
        a.write(f"{ite['id']},{name},{stripNum}\n")
        

    elif len(simi) > 1:

        best = 0
        curBest = ''

        for x in simi:
            itemURL = "https://api.allegro.pl/sale/products/" + str(x['id'])
            ite = requests.get(itemURL, headers=headers).json()
            

            
            try:
                if len(ite['compatibilityList']['items']) > best:
                    best = len(ite['compatibilityList']['items'])
                    curBest = ite['id']
            except Exception as e:
                if curBest == '':
                    curBest = ite['id']
                    best = 0
            
        logger.success(f'Dodano(>1):{curBest},{name},{number}')
        a = open('produktyzacja.csv','a')
        a.write(f"{curBest},{name},{stripNum}\n")




while True:
    try:
        # for x in costam:
            
        get_prod(headers= headers)
         
            
    except Exception as e:
        logger.error(e)
        logger.error("Zmiana tokena")
        r = redis.Redis(host='localhost', port=6379, db=0)
        x = r.get('punktolejowy-current').decode()
        jsonik = json.loads(x)

        headers['Authorization'] = "Bearer " + jsonik['access_token']
        



