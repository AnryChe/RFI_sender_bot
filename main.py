import datetime
import logging
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

# Импортируем конфигурационные данные, токен, дисциплины, телеграм группы, свой телеграм ID и учетные данные почты.
import config

# Импортируем класс инспекции, а также функции получения инспекций
from ex_ex import InspectionsData, refresh_inspections_file, get_discipline_types, get_df_len

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Объект бота
bot = Bot(token=config.inspection_bot_token, parse_mode='HTML')

# Диспетчер
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Получаем стартовые данные инспекций
work_types = get_discipline_types()  # список типов
print(work_types)  # тестовая печать в консоль, чтобы понимать, что нас ждет в раздаче.
gen_inspections_df = refresh_inspections_file()  # генерируем датафрейм с инспекциями
df_len = get_df_len()  # считаем длину датафрейма, общее количество инспекций
print(df_len)
unread_dataframes = {}
readed_dataframes = {}


@dp.message_handler(commands=["start"])  # Хэндлер на команду /start
async def start_command(message: types.Message):
    await message.answer("Привет! В этом канале админ публикует шаблоны дневных инспекций МОФ-3\n"
                         "Print \n"
                         "/start to start \n"
                         "/refresh to refresh inspections list \n"
                         "/inspect to receive list of inspections")
    await message.answer(f'Твой ID: {message.chat.id}')  # Запрос для получения ID группы и добавления в конфиг


@dp.message_handler(commands=["refresh"])  # Хэндлер на команду /refresh. Обновляет данные об инспекциях из файла
async def refresh_command(message: types.Message):
    global gen_inspections_df
    gen_inspections_df = refresh_inspections_file()
    global work_types
    work_types = get_discipline_types()
    global df_len
    df_len = get_df_len()
    await message.answer("Инспекции обновлены\n"
                         "Print\n"
                         "/start to start\n"
                         "/refresh to refresh inspections list\n"
                         "/inspect to receive list of inspections")
    # insp_date = gen_inspections_df.iloc[0, 1]  # иногда дату присылают в виде даты, а не текста)))
    print(df_len)


@dp.message_handler(commands=["inspect"])  # Хэндлер на команду /inspect. Рассылка по каналам шаблонов инспекций
async def inspect_command(message: types.Message):
    for discipline in work_types:  # Добавляем инспекции в словарь не прочтенных инспекций
        unread_dataframes[discipline] = gen_inspections_df[gen_inspections_df['Дисциплина'].str.lower() == discipline]
    insp_date = gen_inspections_df.iloc[0, 1]  # Получаем дату инспекций
    mess_time_out = 3  # устанавливаем таймаут для отправки сообщений в группе (итого не более 20 сообщений в минуту)

    for k, v in config.sep_by_disc.items():  # Перебираем дисциплины в разбивке (приведена в конфигурационном файле)
        if list(set(v) & set(work_types)):  # Проверяем для каждой дисциплины, есть ли в инспекциях виды работ,
            print(k)  # относящиеся к данной дисциплине, если есть, выводим в консоль название текущей дисциплины

            await bot.send_message(text=insp_date, chat_id=config.group_id_list[k])  # Выдаем дату инспекций
            await asyncio.sleep(mess_time_out)

            for work_type in list(set(v) & set(work_types)):  # перебираем виды работ с RFI в дисциплине
                cur_df_len = len(unread_dataframes[work_type])  # длина текущего фрейма вида работ
                await bot.send_message(text=f'<b>{work_type.upper()} : {cur_df_len} инсп.</b>',
                                       chat_id=config.group_id_list[k])  # заголовок вида работ с их количеством
                inspections_df = unread_dataframes[work_type]  # выбираем не прочтенные инспекции по типу работ
                await asyncio.sleep(mess_time_out)

                await message_sender(cur_df_len, inspections_df, mess_time_out, k)  # запускаем функцию шаблонов RFI
                readed_dataframes[work_type] = unread_dataframes[work_type]  # переносим отправленные инспекции из
                unread_dataframes.pop(work_type, None)  # нечитанных в прочитанные
                await asyncio.sleep(mess_time_out)
            await bot.send_message(text='Be careful on inspections!', chat_id=config.group_id_list[k])
            await asyncio.sleep(mess_time_out)

    if unread_dataframes:  # если остались непрочитанные инспекции
        await bot.send_message(text=f"Другие дисциплины, не попавшие в раздачу:", chat_id=config.group_id_list["my_id"])
        for i, j in unread_dataframes.items():  # перебираем их и шлем себе в личку.
            await bot.send_message(text=f"{i}", chat_id=config.group_id_list["my_id"])
            err_df_len = len(unread_dataframes[i])
            if df_len < 9:  # если инспекций меньше 9, снижаем ограничения по скорости выдачи сообщений в чат
                mess_time_out = 0.5
            await message_sender(err_df_len, j, mess_time_out, "my_id")
    now = datetime.datetime.now()
    await asyncio.sleep(mess_time_out)
    await bot.send_message(text=f"Раздача окончена в {now}\n"
                                "Print\n"
                                "/start to start\n"
                                "/refresh to refresh inspections list\n"
                                "/inspect to receive list of inspections", chat_id=config.group_id_list["my_id"])
    print(f'Раздача окончена в {now}')  # семафорим себе в консоль об окончании раздачи.


async def message_sender(cur_df_len, inspections_df, mess_time_out, k):  # функция шаблонов RFI
    for current_inspection in range(cur_df_len):  # Перебираем строки в датафрейме текущего вида работ
        message_inspections = InspectionsData(current_inspection, inspections_df)  # Экз. класса инспекции
        # на основании экземпляра класса инспекции отправляем в группу шаблон ответа по инспекции:
        await bot.send_message(text=f'{message_inspections.insp_order_number}. Время: '  # № и время
                                    f'{message_inspections.insp_time.strftime("%H.%M")}',
                               chat_id=config.group_id_list[k])
        await asyncio.sleep(mess_time_out)
        await bot.send_message(  # шаблон ответа (номер, объект, описание, ответственные
            text=f'Инспекция {message_inspections.insp_number[message_inspections.insp_number.rfind("-") + 1:]}.\n'
                 f'<i>{message_inspections.insp_object}.</i>\n{message_inspections.insp_description}.\n\n'
                 f'СМР {message_inspections.insp_smr[0:message_inspections.fndt_smr - 1]}, '
                 f'КиОК {message_inspections.insp_kiok[0:message_inspections.fndt_kiok - 1]}',
            chat_id=config.group_id_list[k])
        await asyncio.sleep(mess_time_out)


if __name__ == "__main__":
    executor.start_polling(dp)
