import pandas as pd
import datetime

d = {
    'timestamp': [],
    'user': [],
    'chat': [],
}


def is_unnecessary_chat(line: str) -> bool:
    """실제 채팅 내용이 아닌 것들 확인"""
    if "님이 나갔습니다." in line:
        return True
    elif "님이 들어왔습니다." in line:
        return True
    elif "채팅방 관리자가 메시지를 가렸습니다." in line:
        return True
    elif "사진" == line:
        return True
    else:
        return False


with open("./chat.txt", "r", encoding="utf-8") as f:
    content = f.read()
    lines = content.split("2023년 ")  # 한 대화에 \n이 여러번 들어간 것들이 있어서 일단 요걸로 split

    for line in lines[1:]:
        if line == '':
            continue
        elif is_unnecessary_chat(line):
            continue

        try:
            timestamp, user_chat = line.split(", ", 1)
            user, chat = user_chat.split(" : ", 1)
        except ValueError as e:
            print(e, line)
            continue

        timestamp = "2023년 " + timestamp
        d['timestamp'].append(timestamp)
        d['user'].append(user)
        d['chat'].append(chat[:-1])


df = pd.DataFrame(data=d)

df['timestamp'] = df['timestamp'].str.replace('오전', 'AM')
df['timestamp'] = df['timestamp'].str.replace('오후', 'PM')

df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y년 %m월 %d일 %p %I:%M")
df['prev_timestamp'] = df['timestamp'].shift(1)
df['timedelta'] = df['timestamp']-df['prev_timestamp']

thld_5min = []
thld_10min = []
thld_15min = []
thld_20min = []

# 클러스터링 기준 번호. 0부터 시작
thld_5min_cnt = 0
thld_10min_cnt = 0
thld_15min_cnt = 0
thld_20min_cnt = 0

for i, row in df[['timedelta']].iterrows():
    if row['timedelta'] > datetime.timedelta(minutes=5):
        thld_5min_cnt += 1
    if row['timedelta'] > datetime.timedelta(minutes=10):
        thld_10min_cnt += 1
    if row['timedelta'] > datetime.timedelta(minutes=15):
        thld_15min_cnt += 1
    if row['timedelta'] > datetime.timedelta(minutes=20):
        thld_20min_cnt += 1

    thld_5min.append(thld_5min_cnt)
    thld_10min.append(thld_10min_cnt)
    thld_15min.append(thld_15min_cnt)
    thld_20min.append(thld_20min_cnt)

df['thld_5min'] = thld_5min
df['thld_10min'] = thld_10min
df['thld_15min'] = thld_15min
df['thld_20min'] = thld_20min

print(df)
df.to_excel("result.xlsx")