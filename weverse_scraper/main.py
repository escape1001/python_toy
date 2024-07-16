# 3.10.11 64bit에서 작동
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager  # 크롬드라이버 자동업데이트
import time
import pandas as pd


chrome_path = "/Applications/Google"
service = Service(executable_path=chrome_path)
browser = webdriver.Chrome(ChromeDriverManager().install())

# 크롤링할 사이트 접속 - 20초 내로 로그인 해줄 것
browser.get("https://weverse.io/onf/live")
time.sleep(20)

#### 무한 스크롤 반복문 : 필요시 주석 해제하여 사용
"""
before_h = browser.execute_script("return window.scrollY")
while True:
    browser.find_element(By.CSS_SELECTOR, "body").send_keys(Keys.END)
    time.sleep(1) # 스크롤 사이 페이지 로딩시간
    after_h = browser.execute_script("return window.scrollY")

    if after_h == before_h:
        break
    before_h = after_h  # 스크롤 후 높이가 다르면 before_h를 업데이트
"""

# 표 column 각각 리스트로 만들기
no, titles, urls, thumbnails, playtimes, dates, members, tags = ([] for _ in range(8))

# html에서 컨텐츠 카드 크롤링
items = browser.find_elements(By.CSS_SELECTOR, ".LiveListView_live_list__MzGxX a")

i = 1
for item in items:
    title = item.find_element(By.CSS_SELECTOR, "strong").text
    link = item.get_attribute("href")

    try:
        thumbnail = item.find_element(By.CSS_SELECTOR, "div>div img").get_attribute(
            "src"
        )
    except:
        thumbnail = ""

    playtime = item.find_element(
        By.CSS_SELECTOR, "div>div:last-child>div:last-child>div:last-child em"
    ).text
    date = item.find_element(
        By.CSS_SELECTOR, 'div[class*="LiveArtistProfileView_info__"]'
    ).text
    member = item.find_element(By.CSS_SELECTOR, "div>div:last-child ul").text

    # .badge 객체 있으면 fanship = true, 없으면 false
    try:
        blind_elements = item.find_elements(By.CSS_SELECTOR, ".blind")
        fanship_badge = any(element.text == "membership" for element in blind_elements)
    except:
        fanship_badge = False

    # 받아온 데이터 가공
    playtime_fix = playtime.replace("playtime", "").replace("\n", "")
    date_split = date.split(". ")

    if date_split[0] != "2023":
        date_split = ["2024"] + date_split[::]

    date_fix = f"{'/'.join(date_split[0:3])} {date_split[-1]}:00"

    # 각 list에 넣어주기
    no.append(i)
    titles.append(title)
    urls.append(link)
    thumbnails.append(thumbnail)
    playtimes.append(playtime_fix)
    dates.append(date_fix)
    members.append(f'["{member}"]')
    tags.append(f'["팬십"]' if fanship_badge else "")

    i += 1

# list 순서 뒤집기(최신순 -> 오래된순)
for column in [no, titles, playtimes, dates, urls, thumbnails, members, tags]:
    column.reverse()

# 표로 만들어 csv로 저장
subject = pd.DataFrame(
    {
        "SubNo": no,
        "Title": titles,
        "Playtime": playtimes,
        "Date": dates,
        "Url": urls,
        "Thumbnail": thumbnails,
        "Member": members,
        "Tag": tags,
    }
)
subject.to_csv(
    "/Users/es.choi/Downloads/weverse_scrap/live_list.csv",
    encoding="utf-8-sig",
    index=False,
)