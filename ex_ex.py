import pandas as pd
import os
import config


class InspectionsData:
    def __init__(self, ins_pos, insp_df):
        self.insp_order_number = insp_df.iloc[ins_pos, 0]
        self.insp_time = insp_df.iloc[ins_pos, 2]
        self.insp_number = insp_df.iloc[ins_pos, 3]
        self.insp_object = insp_df.iloc[ins_pos, 6]
        self.insp_description = insp_df.iloc[ins_pos, 7]
        self.insp_smr = insp_df.iloc[ins_pos, 9]
        self.insp_kiok = insp_df.iloc[ins_pos, 10]
        self.fndt_smr = self.insp_smr.find("+")
        self.fndt_kiok = self.insp_kiok.find("+")
        self.insp_discipline = insp_df.iloc[ins_pos, 5]


def refresh_inspections_file():  # Функция получения дата фрейма с инспекциями.
    content = os.listdir(config.path)
    dir_files = []
    for file in content:  # В цикле планируется сортировать файлы по дате, дабы открывать последний
        if os.path.isfile(os.path.join(config.path, file)) and file.endswith('.xlsx'):
            dir_files.append(file)
    inspections_file = pd.read_excel(dir_files[0], header=4)
    gen_in_df = inspections_file.iloc[:, 0:11]
    return gen_in_df


def get_discipline_types():  # Функция получения списка дисциплин, по которым есть инспекции
    ins_df = refresh_inspections_file()
    disc_types = ins_df['Дисциплина'].str.lower().unique()
    return disc_types


def get_df_len():  # Функция получения длины дата фрейма для определения количества инспекций
    data_fr = refresh_inspections_file()
    dframe_len = len(data_fr)
    return dframe_len
