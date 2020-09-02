from sentence_transformers import SentenceTransformer
from scipy import spatial
import pandas as pd
import pickle
import time
import os

THRESHOLD = 0.6
MAX_CORPUS_SIZE = 1000
DB_DELIMITER = "__eou__"

log = open('logs/queries_history.log', 'a')

used_embedder = 'xlm-r-40langs-bert-base-nli-stsb-mean-tokens'
embedder = SentenceTransformer(used_embedder)

def prepare_data(path):
    data = pd.read_csv(path)
    answers = data["answers"]
    if DB_DELIMITER == "":
        raw_questions = data["questions"]
        questions = raw_questions.to_frame("question").reset_index()
        return questions, answers
    else:
        # transform DataFrame's question columns into Series without NaN values
        raw_questions = data["questions"].str.split(DB_DELIMITER, expand=True)
        num_columns = raw_questions.columns.shape[0]
        questions = raw_questions.iloc[:, 0]
        for col_num in range(1, num_columns):
            questions = pd.concat([questions, raw_questions.iloc[:, col_num]])
        questions = pd.DataFrame(questions, columns=["question"]).dropna().reset_index()
        return questions, answers

def calculate_embeddings(questions, path: str = "question_embeddings.pkl", ):
    embedding_cache_path = path
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
    return embeddings

def get_scores(query):
    query_embedding = embedder.encode(query)
    cos_scores = spatial.distance.cdist(query_embedding, embeddings, "cosine")[0]
    questions['score'] = cos_scores
    return questions.sort_values(by=['score'])

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
    top_matches = scored_questions.iloc[0:number_top_matches, 0:3]
    top_matches['score'] = 1 - top_matches['score']
    print(top_matches.to_string(float_format="{:.5f}".format))

    idx = top_matches['index'].iloc[0]
    top_score = top_matches['score'].iloc[0]

    if top_score < THRESHOLD:
        log.write('Unknown query\n')
        log.flush()
        return 'Пожалуйста, переформулируйте вопрос'
    else:
        log.flush()
        return answers[idx]

questions, answers = prepare_data('data/questions.csv')
embeddings = calculate_embeddings(questions)
