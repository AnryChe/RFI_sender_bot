import logging
import asyncio
import os
import pandas as pd

from aiogram import Bot, Dispatcher, types

# Импортируем класс инспекция
from ex_ex import InspectionsData

# Импортируем токен
import config

# Включаем логирование, чтобы не пропустить важные сообщения

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

logging.basicConfig(level=logging.INFO)

# Объект бота

bot = Bot(token=config.inspection_bot_token)

# Диспетчер

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

example_dir = config.path
# print(example_dir)
content = os.listdir(example_dir)
dir_files = []
for file in content:
    if os.path.isfile(os.path.join(example_dir, file)) and file.endswith('.xlsx'):
        dir_files.append(file)
inspections_file = pd.read_excel(dir_files[0], header=4)
inspections_df = inspections_file.iloc[:, 0:11]
df_len = len(inspections_df)
discipline_types = []
for i in range(df_len):
    discipline_types.append(inspections_df.iloc[i, 5])
print(set(discipline_types))
a = {'CIVIL': "   ___ОБЩЕСТРОЙ___", 'MECHANICAL': '   ___МЕХАНИКА___'}


# Хэндлер на команду /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.answer("Привет! В этом канале админ публикует шаблоны дневных инспекций МОФ-3"
                         "Print \n"
                         "/start to start \n"
                         "/inspect to receive list of inspections")


# Хэндлер на команду /inspect
@dp.message_handler(commands=["inspect"])
async def inspect_command(message: types.Message):
    insp_date = inspections_df.iloc[0, 1]
    if df_len < 10:
        mess_time_out = 1
    elif message.chat.type == 'private':
        mess_time_out = 0
    elif message.chat.type == 'group':
        mess_time_out = 3
    await message.answer(f"{insp_date}. Общее количество инспекций: {df_len}")
    await message.answer("   ___ОБЩЕСТРОЙ___")
    await asyncio.sleep(mess_time_out)
    for number in range(df_len):
        message_inspections = InspectionsData(number, inspections_df)
        if message_inspections.insp_discipline == "CIVIL":
            await message.answer(
                f'{message_inspections.insp_order_number}. Время: {message_inspections.insp_time.strftime("%H.%M")}')
            await asyncio.sleep(mess_time_out)
            await message.answer(
                f'Инспекция {message_inspections.insp_number[message_inspections.insp_number.rfind("-")+1:]}.\n'
                f'{message_inspections.insp_object}.\n{message_inspections.insp_description}.\n\n'
                f'СМР {message_inspections.insp_smr[0:message_inspections.fndt_smr - 1]}\n'
                f'КиОК {message_inspections.insp_kiok[0:message_inspections.fndt_kiok - 1]}')
            await asyncio.sleep(mess_time_out)

    await message.answer("   ___МЕХАНИКА___")
    for number in range(df_len):
        message_inspections = InspectionsData(number, inspections_df)
        if message_inspections.insp_discipline == "MECHANICAL":
            await message.answer(
                f'{message_inspections.insp_order_number}. Время: {message_inspections.insp_time.strftime("%H.%M")}')
            await asyncio.sleep(mess_time_out)
            await message.answer(
                f'Инспекция {message_inspections.insp_number[message_inspections.insp_number.rfind("-")+1:]}.\n'
                f'{message_inspections.insp_object}.\n{message_inspections.insp_description}.\n\n'
                f'СМР {message_inspections.insp_smr[0:message_inspections.fndt_smr - 1]}\n'
                f'КиОК {message_inspections.insp_kiok[0:message_inspections.fndt_kiok - 1]}')
            await asyncio.sleep(mess_time_out)
    for j in set(discipline_types):
        if j == 'CIVIL' or j == 'MECHANICAL':
            print('ok')
            continue
        else:
            print('yes')
            await message.answer(f"   ___ДРУГИЕ РАБОТЫ___: {j}")
            for item in range(df_len):
                message_inspections = InspectionsData(item, inspections_df)
                if not (message_inspections.insp_discipline == "MECHANICAL" or
                        message_inspections.insp_discipline == "CIVIL"):
                    await message.answer(
                        f'{message_inspections.insp_order_number}. Время: '
                        f'{message_inspections.insp_time.strftime("%H.%M")}')
                    await asyncio.sleep(mess_time_out)
                    await message.answer(
                        f'Инспекция {message_inspections.insp_number[message_inspections.insp_number.rfind("-")+1:]}.\n'
                        f'{message_inspections.insp_object}.\n{message_inspections.insp_description}.\n\n'
                        f'СМР {message_inspections.insp_smr[0:message_inspections.fndt_smr - 1]}\n'
                        f'КиОК {message_inspections.insp_kiok[0:message_inspections.fndt_kiok - 1]}')
                    await asyncio.sleep(mess_time_out)

    await message.answer(
        "Be careful on inspections.\nPrint \n/start to start \n/inspect to receive list of inspections")


if __name__ == "__main__":
    executor.start_polling(dp)
