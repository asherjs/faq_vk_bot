from sentence_transformers import SentenceTransformer
from scipy import spatial
import pandas as pd
import numpy as np
import pickle
import time
import os

THRESHOLD = 0.7
MAX_CORPUS_SIZE = 1000

log = open('logs/queries_history.log', 'a')

used_embedder = 'xlm-r-40langs-bert-base-nli-stsb-mean-tokens'
embedder = SentenceTransformer(used_embedder)

data = pd.read_csv('data/data.csv')
raw_questions = data["questions"].str.split("__eou__", expand=True)
num_columns = raw_questions.columns.shape[0]
questions = raw_questions.iloc[:, 0]
for col_num in range(1, num_columns):
    questions = pd.concat([questions, raw_questions.iloc[:, col_num]])
# for col_num in range(num_columns):
#     questions = pd.concat([questions.iloc[:, 0], raw_questions.iloc[:, col_num]])
questions = pd.DataFrame(questions, columns=["question"]).dropna().reset_index()
answers = data["answers"]

embedding_cache_path = 'question_embeddings.pkl'
if not os.path.exists(embedding_cache_path):
    print("Encode the corpus. This might take a while")
    embeddings = embedder.encode(questions["question"], show_progress_bar=True)
    print("Store file on disc")
    with open(embedding_cache_path, "wb") as fout:
        pickle.dump({'embedding': embeddings}, fout)
else:
    print("Load embeddings from disc")
    with open(embedding_cache_path, "rb") as fin:
        cache_data = pickle.load(fin)
        embeddings = cache_data['embedding'][0:MAX_CORPUS_SIZE]
    print(f"Corpus loaded with {len(embeddings)} sentences / embeddings")

def get_scores(query):
    query_embedding = embedder.encode(query)
    cos_scores = spatial.distance.cdist(query_embedding, embeddings, "cosine")[0]
    questions['score'] = cos_scores
    return questions.sort_values(by=['score'])
    #results = zip(range(len(cos_scores)), answer_indices, cos_scores)
    #return sorted(results, key=lambda x: x[2])

def get_answer(query):
    start_time = time.time()
    scored_questions = get_scores(query)
    end_time = time.time()
    log_info = (
        f'\n======================\nTime: {end_time-start_time}\nQuery: {query} \nModel: {used_embedder}'
        f'\nTop 3 most similar queries in corpus:')
    log.write(log_info)
    print(log_info)
    number_top_matches = 3
    top_matches = scored_questions.iloc[0:number_top_matches, 1:3]
    top_matches['score'] = 1 - top_matches['score']

    print(top_matches.to_string(float_format="{:.5f}".format))
    # for score in scored_questions[0:number_top_matches]:
    #     output = questions.iloc[score[0], :].to_string(na_rep=" ", index=False) + "(Cosine Score: %.4f)" % (1 - score[1])
    #     # output = questions.columns[0][score[0]].strip() + "(Cosine Score: %.4f)" % (1 - score[1])
    #     log.write(output + '\n')
    #     print(output)

    #idx = np.argmin(cos_scores)
    #top_score = scores
    idx = top_matches.first_valid_index()
    top_score = top_matches['score'].iloc[0]

    cos_score = 1 - top_score
    if cos_score > THRESHOLD:
        log.write('Unknown query\n')
        log.flush()
        return 'Пожалуйста, переформулируйте вопрос'
    else:
        log.flush()
        return answers[idx]