import os
import play
from pandas import ExcelFile

class DefaultParams(object):
    def __init__(self):
        self.impacted_pop = None
        self.prog_areas = {}
        self.pop_areas = {}
        self.rr_death = {}
        self.or_cond = {}
        self.or_cond_bo = {}
        self.or_wasting_prog = {}
        self.rr_dia = None
        self.or_stunting_prog = None
        self.bo_progs = None
        self.correct_bf = None
        self.rr_anaem_prog = None
        self.or_anaem_prog = None
        self.child_progs = None
        self.pw_progs = None
        self.rr_age_order = None
        self.rr_interval = None
        # read data
        self.spreadsheet = ExcelFile('default_params.xlsx')
        self.read_spreadsheet()

    def read_spreadsheet(self):
        self.impact_pop()
        self.prog_risks()
        self.pop_risks()
        self.anaemia_progs()
        self.wasting_progs()
        self.relative_risks()
        self.odds_ratios()
        self.bo_progs()
        self.bo_risks()
        self.correct_bf()

    def impact_pop(self):
        sheet = self.read_sheet('Programs impacted population', [0,1])
        impacted = {}
        for pop in ['Children', 'Pregnant women', 'Non-pregnant WRA', 'General population']:
            impacted.update(sheet.loc[pop].to_dict(orient='index'))
        self.impacted_pop = impacted

    def prog_risks(self):
        areas = self.read_sheet('Program risk areas', [0])
        booleanFrame = areas.isnull()
        for program, areas in booleanFrame.iterrows():
            for risk, value in areas.iteritems():
                if self.prog_areas.get(risk) is None:
                    self.prog_areas[risk] = []
                if not value:
                    self.prog_areas[risk].append(program)

    def pop_risks(self):
        areas = self.read_sheet('Population risk areas', [0])
        booleanFrame = areas.isnull()
        for program, areas in booleanFrame.iterrows():
            for risk, value in areas.iteritems():
                if self.pop_areas.get(risk) is None:
                    self.pop_areas[risk] = []
                if not value:
                    self.pop_areas[risk].append(program)

    def relative_risks(self):
        # risk areas hidden in spreadsheet (white text)
        # stunting
        rr_sheet = self.read_sheet('Relative risks', [0,1,2], skiprows=1)
        rr = rr_sheet.loc['Stunting'].to_dict('index')
        self.rr_death['Stunting'] = self.make_dict2(rr)
        # wasting
        rr_sheet = self.read_sheet('Relative risks', [0,1,2], skiprows=28)
        rr = rr_sheet.loc['Wasting'].to_dict('index')
        self.rr_death['Wasting'] = self.make_dict2(rr)
        # anaemia
        rr_sheet = self.read_sheet('Relative risks', [0,1,2], skiprows=55).dropna(axis=1, how='all')
        rr = rr_sheet.loc['Anaemia'].to_dict('index')
        self.rr_death['Anaemia'] = self.make_dict2(rr)
        # breastfeeding
        rr_sheet = self.read_sheet('Relative risks', [0,1,2], skiprows=64)
        rr = rr_sheet.loc['Breastfeeding'].to_dict('index')
        self.rr_death['Breastfeeding'] = self.make_dict2(rr)
        # diarrhoea
        rr_sheet = self.read_sheet('Relative risks', [0,1,2], skiprows=103).dropna(axis=1, how='all')
        rr = rr_sheet.loc['Diarrhoea'].to_dict('index')
        self.rr_dia = self.make_dict2(rr)['None']

    def odds_ratios(self):
        or_sheet = self.read_sheet('Odds ratios', [0,1], skiprows=1)
        self.or_cond['Stunting'] = or_sheet.loc['Condition'].to_dict('index')
        self.or_cond['Wasting'] = or_sheet.loc['Wasting'].to_dict('index')
        self.or_cond['Anaemia'] = or_sheet.loc['Anaemia'].to_dict('index')
        self.or_stunting_prog = or_sheet.loc['By program'].to_dict('index')

    def bo_progs(self):
        progs = self.read_sheet('Programs birth outcomes', [0,1], 'index')
        newprogs = {}
        for program in progs.keys():
            if not newprogs.get(program[0]):
                newprogs[program[0]] = {}
            newprogs[program[0]][program[1]] = progs[program]
        self.bo_progs = newprogs

    def correct_bf(self):
        self.correct_bf = self.read_sheet('Appropriate breastfeeding', [0], 'dict')['Practice']

    def anaemia_progs(self):
        anaem_sheet = self.read_sheet('Programs anemia', [0,1])
        self.rr_anaem_prog = anaem_sheet.loc['Relative risks of anaemia when receiving intervention'].to_dict(orient='index')
        self.or_anaem_prog = anaem_sheet.loc['Odds ratios of being anaemic when covered by intervention'].to_dict(orient='index')

    def wasting_progs(self):
        wastingSheet = self.read_sheet('Programs wasting', [0,1])
        self.or_wasting_prog['SAM'] = wastingSheet.loc['Odds ratio of SAM when covered by program'].to_dict(orient='index')
        self.or_wasting_prog['MAM'] = wastingSheet.loc['Odds ratio of MAM when covered by program'].to_dict(orient='index')

    def child_progs(self):
        childSheet = self.read_sheet('Programs for children', [0,1,2])
        childDict = childSheet.to_dict(orient='index')
        self.child_progs = self.make_dict(childDict)

    def pw_progs(self):
        pw_sheet = self.read_sheet('Programs for PW', [0,1,2])
        pw_dict = pw_sheet.to_dict(orient='index')
        self.pw_progs = self.make_dict(pw_dict)

    def bo_risks(self):
        bo_sheet = self.read_sheet('Birth outcome risks', [0,1], skiprows=[0])
        ors = bo_sheet.loc['Odds ratios for conditions'].to_dict('index')
        self.or_cond_bo['Stunting'] = ors['Stunting (HAZ-score < -2)']
        self.or_cond_bo['MAM'] = ors['MAM (WHZ-score between -3 and -2)']
        self.or_cond_bo['SAM'] = ors['SAM (WHZ-score < -3)']
        self.rr_age_order = bo_sheet.loc['Relative risk by birth age and order'].to_dict('index')
        self.rr_interval = bo_sheet.loc['Relative risk by birth interval'].to_dict('index')
        self.rr_death['Birth outcomes'] = bo_sheet.loc['Relative risks of neonatal causes of death'].to_dict('index')

    def iycf_effects(self): # TODO: IYCF packages to be defined in Project, based on user input (packages)
        effects = self.read_sheet('IYCF odds ratios', [0,1,2])
        bf_effects = effects.loc['OR for correct breastfeeding']
        stunt_effects = effects.loc['OR for stunting']

    def create_iycf(self, input):
        return


    def read_sheet(self, name, cols, dictOrient=None, skiprows=None):
        df = self.spreadsheet.parse(name, index_col=cols, skiprows=skiprows).dropna(how='all')
        if dictOrient:
            df = df.to_dict(dictOrient)
        return df

    def make_dict(self, mydict):
        """ myDict is a spreadsheet with 3 index cols, converted to dict using orient='index' """
        res_dict = {}
        for key in mydict.keys():
            first = key[0]
            sec = key[1]
            third = key[2]
            if res_dict.get(first) is None:
                res_dict[first] = {}
                res_dict[first][sec] = {}
                res_dict[first][sec][third] = mydict[key]
            if res_dict[first].get(sec) is None:
                res_dict[first][sec] = {}
                res_dict[first][sec][third] = mydict[key]
            if res_dict[first][sec].get(third) is None:
                    res_dict[first][sec][third] = mydict[key]
        return res_dict

    def make_dict2(self, mydict):
        """ myDict is a spreadsheet with 3 index cols, converted to dict using orient='index' """

        res_dict = {}
        for key in mydict.keys():
            first = key[0]
            sec = key[1]
            if res_dict.get(first) is None:
                res_dict[first] = {}
                res_dict[first][sec] = {}
                res_dict[first][sec] = mydict[key]
            if res_dict[first].get(sec) is None:
                res_dict[first][sec] = {}
                res_dict[first][sec] = mydict[key]
        return res_dict




class InputData(object):
    def __init__(self, spreadsheet):
        self.spreadsheet = ExcelFile(spreadsheet)


class UserSettings(object):
    """Stores all the settings for each project, defined by the user"""
    def __init__(self, spreadsheet):
        self.spreadsheet = ExcelFile(spreadsheet)
        self.prog_set=None
        pass

mine = DefaultParams()


