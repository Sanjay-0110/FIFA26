# import requests
# import json
# from bs4 import BeautifulSoup

# def get_official_team_rating(url :str) -> dict:
#     headers = {
#                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
#         }
#     response = requests.get(url, headers=headers)
#     if response.status_code == 200 and response.text.strip():
#         data = response.text
#         soup = BeautifulSoup(data, "html.parser")

#         tables = soup.find_all('table')
#         for i, table in enumerate(tables):
#             print(f"Table {i}: {table.find('tr').get_text(strip=True)[:80]}")


# get_official_team_rating("https://inside.fifa.com/fifa-rankings/futsal-world-ranking/men")

import requests
import pandas as pd

def get_fifa_futsal_rankings(date_id="id15103men"):
    url = "https://inside.fifa.com/api/ranking-overview"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://inside.fifa.com/fifa-rankings/futsal-world-ranking/men"
    }
    
    params = {
        "locale": "en",
        "dateId": date_id,
        "rankingType": "futsal"
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    print("Status:", response.status_code)
    print("Content-Type:", response.headers.get("Content-Type"))
    
    data = response.json()
    print("Top-level keys:", data.keys())
    print(data)  # inspect raw structure first
    return data

data = get_fifa_futsal_rankings()
lst = []
for i in range(len(data['rankings'])):
    rank = data['rankings'][i]['rankingItem']['rank']
    team_name = data['rankings'][i]['rankingItem']['name']
    points = data['rankings'][i]['rankingItem']['totalPoints']
    previous_rank = data['rankings'][i]['rankingItem']['previousRank']
    country_code = data['rankings'][i]['rankingItem']['countryCode']
    lst.append((rank, team_name, points, previous_rank, country_code))

df = pd.DataFrame(lst, columns=['Rank', 'Team Name', 'Points', 'Previous Rank', 'Country Code'])
df.to_csv("result/fifa_rankings.csv", index=False)
# print ("Data keys:", data.keys())