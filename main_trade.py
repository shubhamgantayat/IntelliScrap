from SeleniumHandler import GoogleNewsScrapper, DuckDuckGoNewsScrapper
from intelligent_scraper import IntelliScrap
from SeleniumHandler import SeleniumHandler
from selenium.webdriver.common.by import By
import pandas as pd
import re
from bs4 import BeautifulSoup
import numpy as np
from tqdm import tqdm
import time
from urllib.request import quote
from intelligent_scraper import IntelliScrap
from RAG import RAG, split, get_dict_from_json
import streamlit as st


st.title('Daily Stocks News')


# df = pd.read_csv("Nifty_50.csv")

tqdm.pandas()

def get_news(link):
    iscrap = IntelliScrap()
    text, result = iscrap.get_structured_text(link, include_images=False, include_links=False)
    # return text
    split_texts = split(text, chunk_size=1024, chunk_overlap=128)
    if len(split_texts) == 1:
        return None
    # print(len(split_texts))
    prompt = lambda text, summary: f"""Following is the previous output:

### Previous Output: {summary}

Refine the above output based on the text below:

### Text: {text}

### Output: """

    summary = ""
    for split_text in tqdm(split_texts):
        summary = RAG.get_response(prompt(split_text, summary), f"Extract latest news and detailed performance analysis in the json below.")
    return summary


def assign_summary_to_stock(summary):
    prompt = f"""### Text: {summary}

### Instructions: Fill the json below with all the different stock and sectors present in the text and append them in the list of json- 
```json
[{{
    "stock/sector": Name of stock of sector,
    "news": News of the respective sector.
}}]
```

If no news about any stock/sector is present in the text, return an json with empty list.

### Output: """
    return RAG.get_response(prompt)


def get_sentiment(text):
    prompt = f"""### News: {text}


### Question: Choose whether this news is positive / neutral / negative ? Only output the choice. 


### Choice: """
    return RAG.get_response(prompt)


def load_data():
    gns = DuckDuckGoNewsScrapper()
    links = gns.scrap("latest stock news india")
    stocks = []
    visited_links = 0
    for link in links:
        if visited_links == 3:
            break
        summary = get_news(link)
        if summary is None:
            continue
        resp = assign_summary_to_stock(summary)
        try:
            news = list(filter(lambda x: x["news"] is not None and x["news"].strip() != "", get_dict_from_json(resp)))
            for each_news in news:
                each_news["sentiment"] = get_sentiment(each_news["news"])
                each_news["link"] = link
            stocks.extend(news)
            visited_links += 1
        except:
            pass

    stocks_df = pd.DataFrame.from_records(stocks)
    return stocks_df


data_load_state = st.text('Loading latest news...')
data = load_data()
data_load_state.text("Done! Loaded latest news")
# st.subheader('Raw data')
st.dataframe(data, column_config={
    "news": st.column_config.TextColumn("news", width="medium"),
    "link": st.column_config.LinkColumn("link")
})
# st.write(data)