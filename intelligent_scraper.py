from lxml import html, etree
from selenium.webdriver.common.by import By
from typing import List
import re
from SeleniumHandler import SeleniumHandler, download
import time
import pandas as pd
from urllib.request import quote
from tqdm import tqdm
import fitz
import uuid
import os
from RAG import RAG, split


tqdm.pandas()
TMP_DOWNLOAD_DIR = "tmp_download/"
os.makedirs(TMP_DOWNLOAD_DIR, exist_ok=True)


class IntelliScrap(SeleniumHandler):

    def __init__(self):
        self.terminal_tags = [
            "li",
            "a",
            "img",
            "p",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "br",
            "div",
            "span"
        ]
        super().__init__()

    @staticmethod
    def get_text_from_papers(filename):
        doc = fitz.open(filename)
        text = ""
        for page in doc:  # iterate the document pages
            text += "\n" + page.get_text("")
        return text

    def get_structured_text(self, url, include_links=True, include_images=True):
        if re.search("\.pdf$", url) is not None:
            filename = os.path.join(TMP_DOWNLOAD_DIR, str(uuid.uuid1()) + ".pdf")
            if download(url, filename) == 0:
                return self.get_text_from_papers(filename), []
            else:
                return "", []
        else:
            self.driver.set_page_load_timeout(20)
            try:
                self.driver.get(url)
                time.sleep(5)
                html_string = self.driver.page_source
            except:
                return "", []
            # time.sleep(10)
            # print(html_string)
            lxml_tree = html.fromstring(html_string)
            self.driver.quit()
            tree = self.get_tree(lxml_tree)
            result = []
            if "body" in tree["html"]["next_node"].keys():
                text = self.traverse_tree("body", tree["html"]["next_node"]["body"], lxml_tree, result, include_images=include_images, include_links=include_links)
                return re.sub("\n(?:([ \t]*\n)*)", "\n", text), result
            else:
                return "", result

    def traverse_tree(self, key, value, lxml_tree, result, prefix="", level=0, include_links=True, include_images=True):
        tree = etree.ElementTree(lxml_tree)
        if len(value["next_node"]) == 0:
            if key in self.terminal_tags:
                if key == "a":
                    attrs = lxml_tree.xpath(value["xpath"])[0].attrib
                    text = "".join(list(lxml_tree.xpath(value["xpath"])[0].itertext()))
                    if "href" in attrs.keys() and text is not None and include_links is True:
                        res = text + "( " + "### Link: " + lxml_tree.xpath(value["xpath"])[0].attrib["href"] + " )."
                    elif "href" in attrs.keys() and include_links is True:
                        res = "( " + "### Link: " + lxml_tree.xpath(value["xpath"])[0].attrib["href"] + " )."
                    elif text is not None:
                        res = text
                    else:
                        res = ""
                elif key == "img" and include_images is True:
                    attrs = lxml_tree.xpath(value["xpath"])[0].attrib
                    if "src" in attrs.keys():
                        res = "( ### Image: " + lxml_tree.xpath(value["xpath"])[0].attrib["src"] + " )."
                    else:
                        res = ""
                elif key == "li":
                    text = "".join(list(lxml_tree.xpath(value["xpath"])[0].itertext()))
                    if text is not None:
                        res = "> " + text
                    else:
                        res = ""
                elif key == "br":
                    res = "\n"
                else:
                    text = "".join(list(lxml_tree.xpath(value["xpath"])[0].itertext()))
                    if text is not None:
                        res = text
                    else:
                        res = ""
                result.append({
                    "text": res if res is not None else "",
                    "level": level
                })
                return res if res is not None else ""
            else:
                result.append({
                    "text": "",
                    "level": level
                })
                return ""
        else:
            val = ""
            start = 0
            try:
                main_element = tree.xpath(value["xpath"])[0]
                main_texts = list(main_element.itertext())
                for next_node_key, next_node_value in value["next_node"].items():
                    try:
                        cur_element = tree.xpath(next_node_value["xpath"])[0]
                        texts = list(cur_element.itertext())
                    except:
                        texts = []
                    idx1, idx2 = self.get_texts_in_between(main_texts, texts, start)
                    if key == "a":
                        attrs = lxml_tree.xpath(value["xpath"])[0].attrib
                        if "href" in attrs.keys() and include_links is True:
                            res = prefix + self.traverse_tree(next_node_key, next_node_value, lxml_tree, result, prefix,
                                                              level + 1, include_links, include_images) + "( " + "### Link:" + \
                                  lxml_tree.xpath(value["xpath"])[0].attrib["href"] + " )."
                            result[-1]["text"] = prefix + result[-1]["text"] + "( " + "### Link:" + \
                                                 lxml_tree.xpath(value["xpath"])[0].attrib["href"] + " )."
                        else:
                            res = prefix + self.traverse_tree(next_node_key, next_node_value, lxml_tree, result, prefix,
                                                              level + 1, include_links, include_images)
                            result[-1]["text"] = prefix + result[-1]["text"]
                    elif key == "ol" or key == "ul":
                        res = prefix + " " + self.traverse_tree(next_node_key, next_node_value, lxml_tree, result,
                                                                prefix + " ", level + 1, include_links, include_images)
                        result[-1]["text"] = prefix + " " + result[-1]["text"]
                    elif key == "li":
                        res = prefix + "> " + self.traverse_tree(next_node_key, next_node_value, lxml_tree, result,
                                                                 prefix + "> ", level + 1, include_links, include_images)
                        result[-1]["text"] = prefix + "> " + result[-1]["text"]
                    elif key == "table":
                        res = ""
                        try:
                            tables = pd.read_html(value["code"])
                            if isinstance(tables, List):
                                for table in tables:
                                    res += table.to_string()
                                    res += "\n\n"
                            else:
                                res += tables.to_string()
                            result.append({
                                "text": prefix + "\n" + res,
                                "level": level
                            })
                        except:
                            pass
                    elif key == "div":
                        res = prefix + "\n" + self.traverse_tree(next_node_key, next_node_value, lxml_tree, result,
                                                                 prefix, level + 1, include_links, include_images)
                        result[-1]["text"] = prefix + "\n" + result[-1]["text"]
                    else:
                        res = prefix + self.traverse_tree(next_node_key, next_node_value, lxml_tree, result, prefix,
                                                          level + 1, include_links, include_images)
                        result[-1]["text"] = prefix + result[-1]["text"]
                    val += prefix + "".join(main_texts[start: idx1]) + res[len(prefix):]
                    # if len(result) != 0:
                    result[-1]["text"] = result[-1]["text"][len(prefix):]
                    result.insert(-1, {
                        "text": prefix + "".join(main_texts[start: idx1]),
                        "level": level
                    })
                    start = idx2
            except Exception as e:
                print(e)
            return val

    @staticmethod
    def get_texts_in_between(l1, l2, start=0):
        step = len(l2)
        if step == 0:
            return start, start
        for i in range(start, len(l1) - step + 1, step):
            if l2 == l1[i: i + step]:
                return i, i + step
        return start, start

    def get_tree(self, lxml_tree):
        tree = etree.ElementTree(lxml_tree)
        parsed_dict = {}
        for el in lxml_tree.iter():
            # do something
            path = tree.getpath(el)
            # print(path)
            tags = list(filter(lambda x: x != "", path.split("/")))
            root = parsed_dict
            for tag in tags[:-1]:
                root = root[tag]["next_node"]
            root[tags[-1]] = {
                "next_node": {},
                "code": etree.tostring(el).decode(),
                "xpath": path
            }
        return parsed_dict


class GoogleSearch(SeleniumHandler):

    def __init__(self):
        super().__init__()

    def search(self, keyword):
        self.driver.get(self.get_google_url_for_keyword(keyword))
        elements = [element for element in self.driver.find_elements(By.CLASS_NAME, "MjjYud")]
        links = []
        for element in elements:
            a_tags = element.find_elements(By.TAG_NAME, "a")
            if len(a_tags) > 0:
                links.append(a_tags[0].get_attribute("href"))
        self.driver.quit()
        return links

    @staticmethod
    def get_google_url_for_keyword(keyword):
        return f"https://www.google.com/search?q={quote(keyword)}"


def get_text_by_level(result, level=10):
    my_text = ""
    for r in result:
        if r["level"] <= level:
            my_text += r["text"]
    return re.sub("\n(?:([ \t]*\n)*)", "\n", my_text)


def crawl(query, prompt, instructions, top_k=3):
    gs = GoogleSearch()
    links = gs.search(query)[:top_k]
    # print(links)
    links.insert(0, gs.get_google_url_for_keyword(query))
    texts = []
    for link in tqdm(links, "Scraping Links"):
        iscrap = IntelliScrap()
        text, result = iscrap.get_structured_text(link)
        texts.append(split(get_text_by_level(result, 30), chunk_size=512, chunk_overlap=64))
        # print(split_len)
    answers = []
    for text in tqdm(texts, "Generating Answers"):
    # print("Creating RAGS:")
        rag = RAG(text)
        answers.append(rag.get_answers(query))
    return RAG.chain_all_answers(prompt, answers, instructions=instructions)
    # return rag.get_answers(query)





