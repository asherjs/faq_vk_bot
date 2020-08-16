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
questions = data["questions"]
answers = data["answers"]

embedding_cache_path = 'question_embeddings.pkl'
if not os.path.exists(embedding_cache_path):
    print("Encode the corpus. This might take a while")
    question_embeddings = embedder.encode(questions, show_progress_bar=True)

    print("Store file on disc")
    with open(embedding_cache_path, "wb") as fout:
        pickle.dump({'embeddings': question_embeddings}, fout)
else:
    print("Load embeddings from disc")
    with open(embedding_cache_path, "rb") as fin:
        cache_data = pickle.load(fin)
        question_embeddings = cache_data['embeddings'][0:MAX_CORPUS_SIZE]

print(f"Corpus loaded with {len(question_embeddings)} sentences / embeddings")

def get_answer(query):
    query_embedding = embedder.encode(query)

    start_time = time.time()
    cos_scores = spatial.distance.cdist(query_embedding, question_embeddings, "cosine")[0]
    results = zip(range(len(cos_scores)), cos_scores)
    results = sorted(results, key=lambda x: x[1])
    end_time = time.time()

    log_info = (
        f'\n======================\nTime: {end_time-start_time}\nQuery: {query} \nModel: {used_embedder}'
        f'\nTop 3 most similar queries in corpus:')
    log.write(log_info)
    print(log_info)

    number_top_matches = 3
    for idx, score in results[0:number_top_matches]:
        output = questions[idx].strip() + "(Cosine Score: %.4f)" % (1 - score)
        log.write(output + '\n')
        print(output)

    idx = np.argmin(cos_scores)
    top_score = cos_scores[idx]

    cos_score = 1 - top_score
    if cos_score < THRESHOLD:
        log.write('Unknown query\n')
        log.flush()
        return 'Пожалуйста, переформулируйте вопрос'
    else:
        log.flush()
        return answers[idx]