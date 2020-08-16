from vkbottle.bot import Bot, Message
from sentence_transformers import SentenceTransformer
from scipy import spatial
import pandas as pd
import numpy as np
import logging
import time

logging.basicConfig(filename="../logs/bot.log", level=logging.INFO, format='%(asctime)s  %(name)s  %(levelname)s: %(message)s')
log = open('../logs/queries.log', 'a')

used_model = 'xlm-r-40langs-bert-base-nli-stsb-mean-tokens'
embedder = SentenceTransformer(used_model)

data = pd.read_csv('../data/data.csv')
questions = data["questions"]
answers = data["answers"]

question_embeddings = embedder.encode(questions)

def get_answer(query):
    query_embedding = embedder.encode(query)

    start_time = time.time()

    distances = spatial.distance.cdist(query_embedding, question_embeddings, "cosine")[0]
    results = zip(range(len(distances)), distances)
    results = sorted(results, key=lambda x: x[1])

    end_time = time.time()

    log.write(
        f'\n======================\nTime: {end_time-start_time}\nQuery: ' + query + f'\nTop 3 most similar queries in corpus:\nModel: {used_model}\n')
    print(
        f'\n======================\nTime: {end_time-start_time}\nQuery: ' + query + f'\nTop 3 most similar queries in corpus:\nModel: {used_model}\n')

    number_top_matches = 3
    for idx, distance in results[0:number_top_matches]:
        output = questions[idx].strip() + "(Cosine Score: %.4f)" % (1 - distance)
        log.write(output + '\n')
        print(output)

    log.flush()

    idx = np.argmin(distances)
    distance = distances[idx]

    cos_score = 1 - distance
    if cos_score < 0.7:
        return 'Пожалуйста, переформулируйте вопрос'
    else:
        return answers[idx]

bot = Bot("37747b0988b1926299b0ce24d214fa4f1f877dbef4b3aba04e28078c2c634c4d2030043e56800b057f564", debug="DEBUG")  # Рассматриваем эту часть

@bot.on.message(commands=["help"])
async def wrapper(ans: Message):
    await ans('Я могу ответить на некоторые ваши вопросы. Для этого нужно обратиться ко мне в формате '
              '\"Бот, <ваш вопрос>\" Список вопросов, на которые я знаю ответ можно посмотреть по команде /list')

@bot.on.message(commands=["list"])
async def wrapper(ans: Message):
    await ans('Список вопросов, на которые я знаю ответ: \n• ' + '\n• '.join(questions))

@bot.on.chat_invite()
async def wrapper(ans: Message):
    await ans("Привет, друзья!")

@bot.on.message(text="Бот<text>", lower=True)
async def wrapper(ans: Message, text):
    await ans(get_answer(text))

bot.run_polling()
