from transformers import AutoTokenizer
from nltk import PunktSentenceTokenizer
import numpy as np
import re
import json


tokenizer = AutoTokenizer.from_pretrained("stabilityai/stablelm-2-1_6b")


def split(text, chunk_size=512, chunk_overlap=0):
    # print("Splitting")
    input_ids = tokenizer(text).input_ids
    # print("###################################################################")
    if len(input_ids) > chunk_size:
        pst = PunktSentenceTokenizer()
        split_texts_og = pst.tokenize(text)
        split_input_ids_og = tokenizer(split_texts_og).input_ids
        # print("+++++++++++++++++++++++++++++++++++++++")
        split_texts = []
        split_input_ids = []
        # print(len(split_texts_og))
        for split_text, split_input_id in zip(split_texts_og, split_input_ids_og):
            if len(split_input_id) < chunk_size:
                split_texts.append(split_text)
                split_input_ids.append(split_input_id)
        str_lens = list(map(len, split_input_ids))
        count = chunk_size
        start = 0
        final_texts = []
        # print("+++++++++++++++++++++++++++++++++++++++")
        # print(str_lens)
        while True:
            cum_sum = np.cumsum(str_lens[start:])

            end = np.nonzero(cum_sum < count)[0].max()
            reverse_cum_sum = np.cumsum(str_lens[start: start + end + 1][::-1])
            overlap_res = np.nonzero(reverse_cum_sum < chunk_overlap)[0]
            if len(overlap_res) == 0:
                overlap_end = 0
            else:
                if start + end + 1 < len(str_lens):
                    # print(str_lens[start + end + 1])
                    pass
                if start + end + 1 < len(str_lens) and str_lens[start + end + 1] < chunk_size - chunk_overlap:
                    overlap_end = overlap_res.max() + 1

                else:
                    overlap_end = 0
            # print(cum_sum)
            # print(reverse_cum_sum)
            # print(end)
            # print(overlap_res)
            # print(overlap_end)
            # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            final_texts.append(" ".join(split_texts[start: start + end + 1]))
            start += end + 1
            if start >= len(str_lens):
                break
            start -= overlap_end
            # print(start)
        return final_texts
    else:
        return [text]


def get_dict_from_json(res):
    start = re.search("```json", res).span()[1]
    stop = re.search("```(?!json)", res).span()[0]
    res = res[start: stop]
    last_comma = re.search(",(?=[\n]*})", res)
    if last_comma is not None:
        res = res[:last_comma.span()[0]] + res[last_comma.span()[1]:]
    # print()
    # return json.loads(res.strip())
    return json.loads(re.sub(r"[^\x20-\x7E]", "", res.strip()))