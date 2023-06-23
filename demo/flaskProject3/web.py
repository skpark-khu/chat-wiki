from flask import Flask, request, redirect, url_for, render_template, flash
import os
import subprocess
import time
import pandas as pd
import re
import datetime
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import nltk
import torch
import csv
from dotenv import dotenv_values
from notion_client import Client
import requests
from pprint import pprint
from konlpy.tag import Okt
from bs4 import BeautifulSoup
import locale
import numpy as np
import itertools
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


okt = Okt()
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.secret_key = "your_secret_key"


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            flash("선택된 파일이 없습니다.", "error")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("선택된 파일이 없습니다.", "error")
            return redirect(request.url)
    
    if request.method == 'POST':
        file = request.files['file']
        filename = file.filename
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        with open(save_path, "r", encoding="utf-8") as file:
            content = file.read()
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
            elif "이모티콘" in line:
                return True
            elif "삭제된 메시지입니다." in line:
                return True
            elif "부탁드립니" in line:
                return True
            elif "안녕하세" in line:
                return True
            elif "선착순 선물에 당첨되었어요" in line:
                return True
            else:
                return False

        if content[:4] == 202:
            a = 0
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
            df['timedelta'] = df['timestamp'] - df['prev_timestamp']

        else:
            lines = content.split("--------------- ")  # 한 대화에 \n이 여러번 들어간 것들이 있어서 일단 요걸로 split
            # 텍스트 파일의 맨 윗부분, 대화 내용에 2023년이 들어간 경우 삭제함.

            end_characters = '월요일,화요일,수요일,목요일,금요일,토요일,일요일'
            pattern = r'\] \[오'

            for text in lines[1:]:
                for end_character in end_characters:
                    if end_character in text:
                        end_index = text.index(end_character) + 1
                        extracted_text = text[:end_index]
                text1 = re.split(pattern, text)
                for text2 in text1[1:]:
                    if text2 == '':
                        continue
                    elif is_unnecessary_chat(text2):
                        continue

                    try:
                        timestamp, user_chat = text2.split("]", 1)
                        chat, user = user_chat.split("[", 1)
                    except ValueError as e:
                        # print(e, line)
                        continue

                    timestamp = extracted_text + " 오" + timestamp
                    d['timestamp'].append(timestamp)
                    d['user'].append(user)
                    d['chat'].append(chat)

            df = pd.DataFrame(data=d)

            df['timestamp'] = df['timestamp'].astype(str)
            df['timestamp'] = df['timestamp'].str.replace('오전', 'AM')
            df['timestamp'] = df['timestamp'].str.replace('오후', 'PM')

            df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y년 %m월 %d일 %p %I:%M")
            df['prev_timestamp'] = df['timestamp'].shift(1)
            df['timedelta'] = df['timestamp'] - df['prev_timestamp']

        thld_5min = []
        thld_10min = []
        thld_15min = []
        thld_20min = []

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

        df_grouped_5 = df.groupby('thld_5min').agg({'chat': ' '.join})
        df_5 = df_grouped_5
        df_grouped_10 = df.groupby('thld_10min').agg({'chat': ' '.join})
        df_10 = df_grouped_10
        df_grouped_15 = df.groupby('thld_15min').agg({'chat': ' '.join})
        df_15 = df_grouped_15
        df_grouped_20 = df.groupby('thld_20min').agg({'chat': ' '.join})
        df_20 = df_grouped_20

        new_rows = []
        for index, row in df_5.iterrows():
            chat_text = row["chat"]
            split_texts = chat_text.split("반갑습니다")
            new_rows.append({"chat": split_texts[0].strip()})
            if split_texts[1:]:
                new_rows.append({"chat": "반갑습니다"})
            for text in split_texts[1:]:
                new_rows.append({"chat": text.strip()})

        new_df_5 = pd.DataFrame(new_rows)
        df_5 = new_df_5

        new_rows = []
        for index, row in df_5.iterrows():
            chat_text = row["chat"]
            split_texts = chat_text.split("감사합니다")
            new_rows.append({"chat": split_texts[0].strip()})
            if split_texts[1:]:
                new_rows.append({"chat": "감사합니다"})
            for text in split_texts[1:]:
                new_rows.append({"chat": text.strip()})

        new_df_5 = pd.DataFrame(new_rows)


        # Reset the index of the DataFrame
        new_df_5.reset_index(drop=True, inplace=True)

        # Create a boolean mask for rows where the length of 'chat' is less than 20
        mask = new_df_5['chat'].str.len() < 50

        # Apply the mask to filter the DataFrame and keep rows where the condition is True
        filtered_df = new_df_5[~mask]

        # Print the filtered DataFrame
        df_5 = filtered_df

        model_dir = "lcw99/t5-base-korean-text-summary"
        tokenizer = AutoTokenizer.from_pretrained(model_dir)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_dir)

        max_input_length = 512

        summary_data = pd.DataFrame(columns=['text', 'summary', 'url', 'url_title', 'url_desc'])
        #df to df_5, df_10, df_15, df_20
        summary_data['text'] = df_5['chat']

        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')


        count = 0

        for index, row in summary_data.iterrows():
            # find URLs in 'text' column
            urls = re.findall(url_pattern, row['text'])

            if urls:
                summary_data.at[index, 'url'] = urls
                urls_info_list = []
                headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

                for url in urls:
                    try:
                        data = requests.get(url,headers=headers)
                        soup = BeautifulSoup(data.text, 'html.parser')

                        try:
                            title = soup.select_one('meta[property="og:title"]')['content']
                        except:
                            title = 'No Title'

                        try:
                            desc = soup.select_one('meta[property="og:description"]')['content']
                        except:
                            desc = 'No desc'

                        urls_info = {}
                        urls_info['title'] = title
                        urls_info['desc'] = desc
                        urls_info_list.append(urls_info)
                    except:
                        summary_data.at[index, 'url_info'] = "BLANK"

                    summary_data.at[index, 'url_title'] = title
                    summary_data.at[index, 'url_desc'] = desc
            else:
                summary_data.at[index, 'url'] = "BLANK"
                summary_data.at[index, 'url_title'] = "BLANK"
                summary_data.at[index, 'url_desc'] = "BLANK"

            # if urls:
            #     summary_data.at[index, 'url'] = urls[0]
            # else:
            #     summary_data.at[index, 'url'] = "BLANK"
            count +=1
            if count > 100:
               break
        summary_data.head(25)


        count = 0

        for index, row in df_5.iterrows():
            count += 1
            text = row['chat']

            inputs = ["summarize: " + text]

            inputs = tokenizer(inputs, max_length=max_input_length, truncation=True, return_tensors="pt")
            output = model.generate(**inputs, num_beams=8, do_sample=True, min_length=10, max_length=256)
            decoded_output = tokenizer.batch_decode(output, skip_special_tokens=True)[0]
            predicted_title = nltk.sent_tokenize(decoded_output.strip())[0]

            summary_data.loc[index, 'summary'] = predicted_title
            if count > 100:
                break

        # 새로운 DataFrame을 CSV 파일로 저장
        summary_data.to_csv('uploads/chat_test.csv', index=False)

        def getpreferredencoding(do_setlocale = True):
            return "UTF-8"
        locale.getpreferredencoding = getpreferredencoding




        config = dotenv_values(".env")
        notion_secret = config.get('NOTION_TOKEN')
        notion = Client(auth=notion_secret)

        notion_api_key = "secret_Yp03AO7khgzix5l73o66WLWAIoQAJP8YPsu5y0RjWKV"
        database_id = "91455b80ed624b3cbfcd23af027740f4"

        headers = {
            "Authorization": f"Bearer {notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

        url = f"https://api.notion.com/v1/pages/"
        text_data = summary_data
        count = 0

        for index, row in text_data.iterrows():
            count += 1
            doc = row['summary']
            text = row['text']
            text_url = row['url']
            url_title = row['url_title']
            url_desc = row['url_desc']

            if (len(doc)>len(text)):
                doc = text


            tokenized_doc = okt.pos(str(doc))

            nouns = [word[0] for word in tokenized_doc if (word[1] == 'Noun' or word[1] == 'Alpha') and len(word[1]) > 2]

            unique_words = list(set(nouns))
            word_list = []

            for line in unique_words:
                if len(line) > 2 and line != 'nan':
                    word_list.append(line)

            tag_list = []
            for word in word_list:
                tag_list.append({"name": word})

            data = {
                "parent": {"database_id": database_id},
                "properties": {
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": doc
                                }
                            }
                        ]
                    },
                    # Add a multi-select property for tags
                    "Tags": {
                        "multi_select": tag_list
                    },
                    "Text": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": text
                                }
                            }
                        ]
                    },
                    "URL": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": text_url
                                }
                            }
                        ]
                    },
                    "Title": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": url_title
                                }
                            }
                        ]
                    },
                    "Desc": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": url_desc
                                }
                            }
                        ]
                    },
                    "Index": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": str(count)
                                }
                            }
                        ]
                    },
                }
            }

            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            if count > 100:
                break

        return render_template("loading.html")

    return render_template('home.html')

@app.route("/redirect", methods=["GET"])
def redirect_to_notion():
    time.sleep(5)  # Wait for 5 seconds
    return redirect(
        "https://www.notion.so/laonm/DEMO-e3d05fa645c344018bdb5dd056a770e0"
    )



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
