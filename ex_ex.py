
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
