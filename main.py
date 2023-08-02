import logging
import os, datetime
import pandas as pd

from aiogram import Bot, Dispatcher, types
import asyncio
# from os.path import getctime

# Импортируем класс инспекция
from ex_ex import InspectionsData

# Импортируем токен
import config

# Включаем логирование, чтобы не пропустить важные сообщения

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

logging.basicConfig(level=logging.INFO)

# Объект бота

bot = Bot(token=config.inspection_bot_token, parse_mode='HTML')

# Диспетчер

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

sep_by_disc = {'___ОБЩЕСТРОЙ___': ['civil', 'coating', 'structural'], '___МЕХАНИКА___': ['mechanical'],
               '___ЭЛЕКТРИКА___': ['electrical'], '___АВТОМАТИЗАЦИЯ___': ['instrument']}

content = os.listdir(config.path)
dir_files = []
for file in content:  # В цикле планируется сортировать файлы по дате, дабы открывать последний
    if os.path.isfile(os.path.join(config.path, file)) and file.endswith('.xlsx'):
        dir_files.append(file)


inspections_file = pd.read_excel(dir_files[0], header=4)
gen_inspections_df = inspections_file.iloc[:, 0:11]
df_len = len(gen_inspections_df)
discipline_types = gen_inspections_df['Дисциплина'].str.lower().unique()
print(discipline_types)
print(df_len)
unread_dataframes = {}
readed_dataframes = {}

for discipline in discipline_types:
    unread_dataframes[discipline] = gen_inspections_df[gen_inspections_df['Дисциплина'].str.lower() == discipline]


# Хэндлер на команду /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.answer("Привет! В этом канале админ публикует шаблоны дневных инспекций МОФ-3"
                         "Print \n"
                         "/start to start \n"
                         "/inspect to receive list of inspections")
    await message.answer(f'Твой ID: {message.from_user.id}')


# Хэндлер на команду /inspect
@dp.message_handler(commands=["inspect"])
async def inspect_command(message: types.Message):
    insp_date = gen_inspections_df.iloc[0, 1]
    # Set timeout of message in according to chat type and length of inspections list.
    mess_time_out = 3
    if message.chat.type == 'private':
        mess_time_out = 1
    elif df_len < 9:
        mess_time_out = 0.5

    await message.answer(insp_date)  # print current inspection date and make timeout before sending all message
    await asyncio.sleep(mess_time_out)

    for k, v in sep_by_disc.items():
        if list(set(v) & set(discipline_types)):
            print(k)
            await message.answer(f'<b>{k} : </b>')
            await asyncio.sleep(mess_time_out)
            for discipline_type in list(set(v) & set(discipline_types)):  # set the discipline types from current RFI
                cur_df_len = len(unread_dataframes[discipline_type])
                await message.answer(f'{discipline_type} : {cur_df_len}')
                inspections_df = unread_dataframes[discipline_type]
                for current_inspection in range(cur_df_len):
                    message_inspections = InspectionsData(current_inspection, inspections_df)
                    await message.answer(
                        f'{message_inspections.insp_order_number}. Время: {message_inspections.insp_time.strftime("%H.%M")}')
                    await asyncio.sleep(mess_time_out)
                    await message.answer(
                        f'Инспекция {message_inspections.insp_number[message_inspections.insp_number.rfind("-") + 1:]}.\n'
                        f'<i>{message_inspections.insp_object}.</i>\n{message_inspections.insp_description}.\n\n'
                        f'СМР {message_inspections.insp_smr[0:message_inspections.fndt_smr - 1]}, '
                        f'КиОК {message_inspections.insp_kiok[0:message_inspections.fndt_kiok - 1]}')
                    await asyncio.sleep(mess_time_out)
                readed_dataframes[discipline_type] = unread_dataframes[discipline_type]
                unread_dataframes.pop(discipline_type, None)
    if unread_dataframes:
        for i, j in unread_dataframes.items():
            print("Другие дисциплины", i)
            print(j)
    await message.answer(
        "Be careful on inspections.\nPrint \n/start to start \n/inspect to receive list of inspections")
    now = datetime.datetime.now()
    print(f'Раздача окончена в {now}')

if __name__ == "__main__":
    executor.start_polling(dp)
