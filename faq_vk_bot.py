from vkbottle.bot import Bot, Message
from vkbottle.api.uploader.doc import DocUploader
import logging
import similarity
import json

logging.basicConfig(filename="logs/bot.log", level=logging.INFO, format='%(asctime)s  %(name)s  %(levelname)s: %(message)s')

with open("config.json") as f:
    config = json.load(f)

# ! Insert your group token instead of 'config["token"]'. Recommended to use separate config file with your token without including it to VCS !
bot = Bot(config["token"], debug="DEBUG")
doc_uploader = DocUploader(bot.api, generate_attachment_strings=True)

@bot.on.message_handler(commands=["help"])
async def wrapper(ans: Message):
    await ans('Список вопросов, на которые я знаю ответ можно посмотреть по команде /list\n'
              'Чтобы загрузить свой список вопросов отправьте команду /upload с прикрепленным csv файлом со своими \n'
              'вопросами в формате \"вопрос1__eou__вопрос2...\",\"ответ\"')

@bot.on.message_handler(commands=["list"])
async def wrapper(ans: Message):
    await ans('Список вопросов, на которые я знаю ответ: \n• ' + '\n• '.join(similarity.questions.columns[0]))

@bot.on.message_handler(commands=["upload"])
async def wrapper(ans: Message):
    if ans.attachments:
        data = await doc_uploader.get_data_from_link(ans.attachments[0].doc.url)
        await ans('Ваши данные приняты')
    elif not ans.attachments:
        await ans('Вы не прикрепили файл с вашими вопросами')

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
