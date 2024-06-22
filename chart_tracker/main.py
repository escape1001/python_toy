import functions_framework
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pytz import timezone
import time
import base64
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json


# 현재 시각이 오후 6시 47분이라면 18:00을 time_now로 지정
date_now = datetime.now(timezone("Asia/Seoul")).strftime('%y-%m-%d')
time_now = datetime.now(timezone("Asia/Seoul")).strftime("%H:00")
print(f"현재시긱:{time_now}")

# 멜론, 지니 헤더 필요
h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"}

# 곡 정보, sid 모음
target_song_title = "ABCD"
melon_sid = "37633631"
genie_sid = "106884911"
bugs_sid = "33206960"

# 시트 정보
google_doc_id="188qFe8m8ouX1LM_ThYVyaeQ85TqiUO1Xy5JAj5pYQQ4"
google_sheet_id = 1707328637

def getMelon():
    melon_url_100 = "https://www.melon.com/chart/hot100/index.htm?chartType=D100"
    melon_url_30 = "https://www.melon.com/chart/hot100/index.htm?chartType=D30"
    melon_like_url = f"https://www.melon.com/commonlike/getSongLike.json?contsIds={melon_sid}"

    melon_data = {
        "rank_100" : None,
        "rank_30" : None,
        "like_cnt" : None
    }

    response_melon_100 = requests.get(melon_url_100, headers=h)
    soup_melon_100 = BeautifulSoup(response_melon_100.text, 'html.parser')

    # 시간이 현재 시간과 맞는지 체크하고, 안맞으면 10초 기다리기 반복
    melon_time_now = soup_melon_100.select(".hhmm .hour")[0].text

    while time_now != melon_time_now :
        print(f"멜론 발매 지연중.. {melon_time_now}")
        time.sleep(10)
        response_melon_100 = requests.get(melon_url_100, headers=h)
        soup_melon_100 = BeautifulSoup(response_melon_100.text, 'html.parser')
        melon_time_now = soup_melon_100.select(".hhmm .hour")[0].text

    response_melon_30 = requests.get(melon_url_30, headers=h)
    soup_melon_30 = BeautifulSoup(response_melon_30.text, 'html.parser')

    # song_title과 일치하는 row 찾아서 현재 순위, 변동폭 저장
    tr_list_100 = soup_melon_100.select("#tb_list tr")[1::]
    tr_list_30 = soup_melon_30.select("#tb_list tr")[1::]

    # print(f"{melon_time_now}시")
    # print("[멜론 Top 100 - 100일]")
    for item in tr_list_100 :
        if target_song_title in item.select(".wrap_song_info")[0].text :
            곡명 = item.select('.wrap_song_info a')[0].text
            아티스트 = item.select('.wrap_song_info a')[1].text
            순위 = item.select('.rank')[0].text
            변동 = item.select('.rank_wrap')[0].attrs['title']

            # print(f"{곡명} - {아티스트} / {순위}위 ({변동})")

            melon_data["rank_100"] = int(순위)
            # melon_data["rank_100_change"] = 변동

    # print("[멜론 Top 100 - 30일]")
    for item in tr_list_30 :
        if target_song_title in item.select(".wrap_song_info")[0].text :
            곡명 = item.select('.wrap_song_info a')[0].text
            아티스트 = item.select('.wrap_song_info a')[1].text
            순위 = item.select('.rank')[0].text
            변동 = item.select('.rank_wrap')[0].attrs['title']

            # print(f"{곡명} - {아티스트} / {순위}위 ({변동})")

            melon_data["rank_30"] = int(순위)
            # melon_data["rank_30_change"] = 변동

    # 하트 갯수 받아오기
    response_melon_like = requests.get(melon_like_url, headers=h)
    json_melon_like = response_melon_like.json()
    melon_like_cnt = json_melon_like['contsLike'][0]['SUMMCNT']
    melon_data["like_cnt"] = int(melon_like_cnt)

    return melon_data
    
def getGenie():
    genie_url = "https://genie.co.kr/chart/top200?pg=" # pg 1~5까지
    genie_detail_url = "https://genie.co.kr/detail/songInfo?xgnm="

    genie_data = {
        "rank" : None,
        "like_cnt" : None,
        "listener_cnt" : None,
        "play_cnt" : None
    }

    # 시간이 현재 시간과 맞는지 체크
    response = requests.get(f'{genie_url}1', headers=h)
    genie_time_soup = BeautifulSoup(response.text, 'html.parser')
    genie_time_now = genie_time_soup.select("#strHH")[0].attrs['value']+":00"

    # 00시에 01:00으로 들어오는 에러에 임시대응
    if time_now == "00:00" and genie_time_now == "01:00" :
        genie_time_now = "00:00"

    while time_now != genie_time_now :
        print(f"지니 발매 지연중... {genie_time_now}")
        time.sleep(10)
        response = requests.get(f'{genie_url}1', headers=h)
        genie_time_soup = BeautifulSoup(response.text, 'html.parser')
        genie_time_now = genie_time_soup.select("#strHH")[0].attrs['value']+":00"

        if time_now == "00:00" and genie_time_now == "01:00" :
            genie_time_now = "00:00"

    # song_title과 일치하는 row 찾아서 현재 순위, 변동폭 저장
    soup_list = []

    for i in range(1,6):
        response = requests.get(f'{genie_url}{i}', headers=h)
        soup_list.append(BeautifulSoup(response.text, 'html.parser'))

    table_list = sum([soup.select(".music-list-wrap") for soup in soup_list], [])
    rank_list = sum([table.select("tbody tr") for table in table_list], [])

    # print(f"{genie_time_now} [지니 Top 200]")
    for item in rank_list :
        if target_song_title in item.select(".title")[0].text :
            곡명 = item.select('.info .title')[0].text.replace("\n", "").strip()
            아티스트 = item.select('.info .artist')[0].text.replace("\n", "").strip()
            순위태그 = str(item.select('.number')[0])
            순위시작 = 순위태그.index(">") + 1
            순위끝 = 순위태그.index("<span")
            순위 = 순위태그[순위시작:순위끝].strip()
            변동 = item.select('.rank')[0].text.replace("\n", "")

            # print(f"{곡명} - {아티스트} / {순위}위 ({변동})")

            genie_data["rank"] = int(순위)
            # genie_data["rank_change"] = 변동

    # 곡 상세 페이지 들어가서 전체 청취자수, 전체 재생수, 좋아요 수 저장
    detail_res = requests.get(f'{genie_detail_url}{genie_sid}', headers=h)
    detail_soup = BeautifulSoup(detail_res.text, 'html.parser')

    like_cnt = detail_soup.select(".song-main-infos .like #emLikeCount")[0].text.replace(",", "")
    listener_cnt = detail_soup.select(".daily-chart .total p")[0].text.replace(",", "" )
    play_cnt = detail_soup.select(".daily-chart .total p")[1].text.replace(",", "" )
    # print(f"좋아요:{like_cnt} / 청취자수:{listener_cnt} / 재생수:{play_cnt}")

    genie_data["like_cnt"] = int(like_cnt)
    genie_data["listener_cnt"] = int(listener_cnt)
    genie_data["play_cnt"] = int(play_cnt)

    return genie_data

def getBugs():
    bugs_url = "https://music.bugs.co.kr/chart"
    bugs_detail = "https://music.bugs.co.kr/track/"

    bugs_data = {
        "rank" : None,
        "like_cnt" : None
    }

    # 시간이 현재 시간과 맞는지 체크
    bugs_response = requests.get(bugs_url, headers=h)
    bugs_soup = BeautifulSoup(bugs_response.text, 'html.parser')
    bugs_time_now = bugs_soup.select("time em")[0].text

    while time_now != bugs_time_now :
        print(f"벅스 발매 지연중... {bugs_time_now}")
        time.sleep(10)
        bugs_response = requests.get(bugs_url, headers=h)
        bugs_soup = BeautifulSoup(bugs_response.text, 'html.parser')
        bugs_time_now = bugs_soup.select("time em")[0].text

    # song_title과 일치하는 row 찾아서 현재 순위, 변동폭 저장
    song_list = bugs_soup.select("table.byChart tr")

    for item in song_list :
        if target_song_title in item.select(".title")[0].text :
            곡명 = item.select('.title')[0].text.replace("\n", "")
            아티스트 = item.select('.artist')[0].text.replace("\n", "")
            순위 = item.select('.ranking strong')[0].text.replace("\n", "")
            변동 = item.select('.ranking p')[0].text.replace("\n", "").strip()

            # print(f"{bugs_time_now}시 벅스 순위")
            # print(f"{곡명} - {아티스트} / {순위}위 ({변동})")

            bugs_data["rank"] = int(순위)
            # bugs_data["rank_change"] = 변동

    # 곡 상세 페이지 들어가서 하트 수 저장
    detail_respose = requests.get(f'{bugs_detail}{bugs_sid}', headers=h)
    detail_soup = BeautifulSoup(detail_respose.text, 'html.parser')

    like_cnt = detail_soup.select('.etcInfo .likeBtn em')[0].text.replace(",", "")
    bugs_data["like_cnt"] = int(like_cnt)

    return bugs_data

@functions_framework.http
def track_chart(request):
    import os
    print("start")
    google_json_key_base64 = os.environ.get("GOOGLE_JSON_KEY", "Specified environment variable is not set.")
    google_json_key = base64.b64decode(google_json_key_base64).decode('utf-8')
    credentials_dict = json.loads(google_json_key)

    # 자격 증명 객체를 JSON 문자열로 변환하여 임시 파일로 저장
    with open('credentials.json', 'w') as json_file:
        json.dump(credentials_dict, json_file)

    # Google Sheets API에 연결
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)

    # 스프레드시트 열고 선택
    spreadsheet = client.open_by_key(google_doc_id)
    sheet = spreadsheet.get_worksheet_by_id(google_sheet_id)

    # 차트 데이터
    melon_data = getMelon()
    genie_data = getGenie()
    bugs_data = getBugs()
    date = date_now if time_now == "00:00" else None

    sheet.append_row([date, time_now] + list(melon_data.values()) + list(genie_data.values()) + list(bugs_data.values()))

    # 임시 파일 삭제 (선택 사항)
    os.remove('credentials.json')

    return f"{time_now}시 업데이트 완료"