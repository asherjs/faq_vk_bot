from vkbottle.bot import Bot, Message
import logging
import similarity
import json

logging.basicConfig(filename="logs/bot.log", level=logging.INFO, format='%(asctime)s  %(name)s  %(levelname)s: %(message)s')

with open("config.json") as f:
    config = json.load(f)

# ! Insert your group token instead of 'config["token"]'. Recommended to use separate config file with your token without including it to VCS !
bot = Bot(config["token"], debug="DEBUG")

@bot.on.message_handler(commands=["help"])
async def wrapper(ans: Message):
    await ans('Список вопросов, на которые я знаю ответ можно посмотреть по команде /list\n'
              'Чтобы загрузить свой список вопросов введите команду /upload и прикрепите файл csv со своими \n'
              'вопросами в формате \"вопрос1__eou__вопрос2...\",\"ответ\"')

@bot.on.message_handler(commands=["list"])
async def wrapper(ans: Message):
    await ans('Список вопросов, на которые я знаю ответ: \n• ' + '\n• '.join(similarity.questions.columns[0]))

@bot.on.chat_invite()
async def wrapper(ans: Message):
    await ans("Привет, друзья! У меня вы можете спросить что-нибудь про поступление в ДВФУ."
              "\nДля моего функционирования в общем чате необходимо дать мне доступ к переписке в настройках беседы."
              "\nДоступные командны:"
              "\n/help – помощь"
              "\n/list – вопросы, на которые я знаю ответ")

@bot.on.message_handler(text="<text>", lower=True)
async def wrapper(ans: Message, text):
    await ans(similarity.get_answer(text))

bot.run_polling()
