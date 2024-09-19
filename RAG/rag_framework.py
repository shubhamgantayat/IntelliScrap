from typing import List
from openai import OpenAI
from dotenv import find_dotenv, load_dotenv
import pandas as pd
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from datasets import Dataset

envs = load_dotenv(find_dotenv())
OPENAI_CLIENT = OpenAI()
EMBEDDING_MODEL = SentenceTransformer("BAAI/bge-m3")
tqdm.pandas()


class RAG:

    def __init__(self, texts: List):
        self.client = OpenAI()
        self.texts = texts
        self.texts_encoded = EMBEDDING_MODEL.encode(self.texts)
        self.embeddings_dataset = Dataset.from_dict({
            "embeddings": self.texts_encoded,
            "texts": self.texts
        })
        self.embeddings_dataset.add_faiss_index(column="embeddings")
        self.qa_prompt = lambda text, question: f"""### Text: {text}

### Question: {question}

### Answer: """

    def get_answers(self, question: str, top_k=5, return_single_answer=True):
        question_embedding = EMBEDDING_MODEL.encode([question])
        scores, samples = self.embeddings_dataset.get_nearest_examples(
            "embeddings", question_embedding, k=top_k
        )
        samples_df = pd.DataFrame.from_dict(samples)
        samples_df["scores"] = scores
        samples_df.sort_values("scores", ascending=False, inplace=True)
        return self.chain_all_texts(question, samples_df["texts"].tolist())
        # samples_df["answer"] = samples_df["texts"].progress_apply(
        #     lambda x: self.get_response(self.qa_prompt(x, question)))
        # if return_single_answer:
        #     return self.chain_all_answers(question, samples_df["answer"].tolist())
        # else:
        #     return samples_df

    def chain_all_texts(self, question, texts):
        text = ""
        for i, text_str in enumerate(texts):
            text += f"### Text {i + 1}: {text_str}\n\n"

        text += f"""### Question: Give detailed answer for the following question using the above texts: {question}

### Answer: """
        return self.get_response(text)

    @staticmethod
    def chain_all_answers(question, answers, instructions="Give detailed answer for the following question using the above text"):
        text = "### Text: "
        for i, answer in enumerate(answers):
            text += f"{answer}\n\n"

        text += f"""### Question: {question}

### Instructions: {instructions}

### Answer: """
        return RAG.get_response(text)

    @staticmethod
    def get_response(text, system_content="You are a helpful assistant."):
        response = OPENAI_CLIENT.chat.completions.create(
            # model="gpt-4o-mini",
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": system_content},
                {"role": "user", "content": text}
            ],
            temperature=0.0
        )
        return response.choices[0].message.content
