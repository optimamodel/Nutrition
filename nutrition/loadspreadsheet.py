import os
import play
from copy import deepcopy as dcp
from pandas import ExcelFile, read_excel, notnull
import settings

class DefaultParams(object):
    def __init__(self):
        self.settings = settings.Settings()
        self.inputs = '../applications/master/data/national/master_settings.xlsx'
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
        self.or_bf_prog = None
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
        self.get_bo_progs()
        self.get_bo_risks()
        self.get_correct_bf()
        self.iycf_effects()

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

    def get_bo_progs(self):
        progs = self.read_sheet('Programs birth outcomes', [0,1], 'index')
        newprogs = {}
        for program in progs.keys():
            if not newprogs.get(program[0]):
                newprogs[program[0]] = {}
            newprogs[program[0]][program[1]] = progs[program]
        self.bo_progs = newprogs

    def get_correct_bf(self):
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

    def get_bo_risks(self):
        bo_sheet = self.read_sheet('Birth outcome risks', [0,1], skiprows=[0])
        ors = bo_sheet.loc['Odds ratios for conditions'].to_dict('index')
        self.or_cond_bo['Stunting'] = ors['Stunting (HAZ-score < -2)']
        self.or_cond_bo['MAM'] = ors['MAM (WHZ-score between -3 and -2)']
        self.or_cond_bo['SAM'] = ors['SAM (WHZ-score < -3)']
        self.rr_age_order = bo_sheet.loc['Relative risk by birth age and order'].to_dict('index')
        self.rr_interval = bo_sheet.loc['Relative risk by birth interval'].to_dict('index')
        self.rr_death['Birth outcomes'] = bo_sheet.loc['Relative risks of neonatal causes of death'].to_dict('index')

    def iycf_effects(self):
        packages = self.define_iycf()
        effects = self.read_sheet('IYCF odds ratios', [0,1,2])
        bf_effects = effects.loc['Odds ratio for correct breastfeeding']
        stunt_effects = effects.loc['Odds ratio for stunting']
        self.or_bf_prog = self.create_iycf(bf_effects, packages)
        self.or_stunting_prog.update(self.create_iycf(stunt_effects, packages))

    def create_iycf(self, effects, packages):
        """ Creates IYCF packages based on user input in 'IYCFpackages' """
        # non-empty cells denote program combination
        # get package combinations
        # create new program
        newPrograms = {}
        ORs = {}
        for key, item in packages.items():
            if newPrograms.get(key) is None:
                newPrograms[key] = {}
            for age in self.settings.child_ages:
                ORs[age] = 1.
                for pop, mode in item:
                    row = effects.loc[pop, mode]
                    thisOR = row[age]
                    ORs[age] *= thisOR
            newPrograms[key].update(ORs)
        return newPrograms

    def define_iycf(self):
        """ Returns a dict with values as a list of two tuples (age, modality)."""
        IYCFpackages = read_excel(self.inputs, sheet='IYCF packages', index_col=[0,1])
        packagesDict = {}
        for packageName, package in IYCFpackages.groupby(level=[0, 1]):
            if packageName[0] not in packagesDict:
                packagesDict[packageName[0]] = []
            for mode in package:
                col = package[mode]
                if col.notnull()[0]:
                    if mode == 'Mass media':
                        ageModeTuple = [(pop, mode) for pop in self.child_ages[:-1]] # exclude 24-59 months
                    else:
                        ageModeTuple = [(packageName[1], mode)]
                    packagesDict[packageName[0]] += ageModeTuple
        return packagesDict

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
    """ Container for all the region-specific data (prevalences, mortality rates etc) read in from spreadsheet"""
    def __init__(self, spreadsheet):
        self.spreadsheet = ExcelFile(spreadsheet)
        self.demo = None
        self.proj = {}
        self.death_dist = None
        self.risk_dist = {}
        self.causes_death = None
        self.time_trends = None
        self.birth_age = None
        self.birth_int = None
        self.prog_target = None
        self.famplan_methods = None
        self.incidences = {}

        self.get_demo()
        self.get_proj()
        self.get_risk_dist()
        self.get_death_dist()
        self.get_time_trends()
        self.get_fertility_risks()
        self.get_prog_target()
        self.get_famplan_methods()
        self.get_incidences()

    ## DEMOGRAPHICS ##

    def get_demo(self):
        baseline = self.read_sheet('Baseline year population inputs', [0,1])
        demo = {}
        # the fields that group the data in spreadsheet
        fields = ['Population data', 'Food', 'Age distribution of pregnant women', 'Mortality', 'Other risks']
        for field in fields:
            demo.update(baseline.loc[field].to_dict('index'))
        self.demo = {key: item['Data'] for key, item in demo.iteritems()}
        self.demo['Birth outcome distribution'] = baseline.loc['Birth outcome distribution'].to_dict()['Data']

    def get_proj(self):
        proj = self.read_sheet('Demographic projections', [0])
        # dict of lists to support indexing
        for column in proj:
            self.proj[column] = proj[column].tolist()

    def get_risk_dist(self):
        dist = self.read_sheet('Nutritional status distribution', [0,1])
        # dist = dist.drop(dist.index[[1]])
        riskDist = {}
        for field in ['Stunting (height-for-age)', 'Wasting (weight-for-height)']:
            riskDist[field.split(' ',1)[0]] = dist.loc[field].dropna(axis=1, how='all').to_dict('dict')
        # fix key refs (surprisingly hard to do in Pandas)
        for outer, ageCat in riskDist.iteritems():
            self.risk_dist[outer] = {}
            for age, catValue in ageCat.iteritems():
                self.risk_dist[outer][age] = {}
                for cat, value in catValue.iteritems():
                    newCat = cat.split(' ',1)[0]
                    self.risk_dist[outer][age][newCat] = value
        # get anaemia
        dist = self.read_sheet('Nutritional status distribution', [0,1], skiprows=12)
        self.risk_dist['Anaemia'] = {}
        anaem = dist.loc['Anaemia', 'Prevalence of iron deficiency anaemia'].to_dict()
        for age, prev in anaem.iteritems():
            self.risk_dist['Anaemia'][age] = {}
            self.risk_dist['Anaemia'][age]['Anaemic'] = prev
            self.risk_dist['Anaemia'][age]['Not anaemic'] = 1.-prev
        # get breastfeeding dist
        dist = self.read_sheet('Breastfeeding distribution', [0,1])
        self.risk_dist['Breastfeeding'] = dist.loc['Breastfeeding'].to_dict()

    def get_time_trends(self):
        trends = self.spreadsheet.parse('Time trends', index_col=[0,1])
        self.time_trends = {level: trends.xs(level).to_dict('index') for level in trends.index.levels[0]}

    def get_fertility_risks(self):
        fert = self.read_sheet('Fertility risks', [0,1])
        self.birth_age = fert.loc['Birth age and order'].to_dict()['Percentage of births in category']
        self.birth_int = fert.loc['Birth intervals'].to_dict()['Percentage of births in category']

    def get_incidences(self):
        self.incidences = self.read_sheet('Incidence of conditions', [0], 'dict')

    ### MORTALITY ###

    def get_death_dist(self):
        self.death_dist = self.read_sheet('Causes of death', [0], 'index')
        self.causes_death = self.death_dist.keys()

    ### PROGRAMS ###

    def get_prog_target(self):
        targetPopSheet = self.read_sheet('Programs target population', [0,1])
        targetPop = {}
        for pop in ['Children', 'Pregnant women', 'Non-pregnant WRA', 'General population']:
            targetPop.update(targetPopSheet.loc[pop].to_dict(orient='index'))
        self.prog_target = targetPop

    def get_famplan_methods(self):
        self.famplan_methods = self.read_sheet('Programs family planning', [0], 'index')

    def read_sheet(self, name, cols, dict_orient=None, skiprows=None):
        df = self.spreadsheet.parse(name, index_col=cols, skiprows=skiprows).dropna(how='all')
        if dict_orient:
            df = df.to_dict(dict_orient)
        return df

class UserSettings(object):
    """Stores all the settings for each project, defined by the user"""
    def __init__(self):
        self.settings = settings.Settings()
        # self.spreadsheet = ExcelFile(spreadsheet)
        # TODO: temp
        self.input = '../applications/master/data/national/master_input.xlsx'
        self.spreadsheet = ExcelFile('../applications/master/data/national/master_settings.xlsx')
        self.prog_set = []
        self.ref_progs = []
        self.prog_deps = None
        self.prog_annual_spend = {}
        self.prog_info = None

        # load data
        self.get_prog_set()
        self.get_prog_deps()
        self.get_ref_progs()
        self.get_prog_annual()
        self.get_prog_info()
        packages = self.define_iycf()
        self.get_iycf_target(packages)
        self.get_iycf_cost(packages) # TODO: don't forget to add in Programs

    def get_prog_set(self):
        prog_sheet = self.read_sheet('Programs to include', [0])
        prog_sheet = prog_sheet[notnull(prog_sheet)]
        for program, value in prog_sheet.iterrows():
            self.prog_set.append(program)

    def get_ref_progs(self):
        reference = self.spreadsheet.parse('Reference programs', index_col=[0])
        self.ref_progs = list(reference.index)

    def get_prog_deps(self):
        deps = self.read_sheet('Program dependencies', [0])
        programDep = {}
        for program, dependency in deps.iterrows():
            programDep[program] = {}
            for dependType, value in dependency.iteritems():
                if isinstance(value, unicode): # cell not empty
                    programDep[program][dependType] = value.replace(", ", ",").split(',') # assumes programs separated by ", "
                else:
                    programDep[program][dependType] = []
        # pad the remaining programs
        missingProgs = list(set(self.prog_set) - set(programDep.keys()))
        for program in missingProgs:
            programDep[program] = {}
            for field in deps.columns:
                programDep[program][field] = []
        self.prog_deps = programDep

    def get_prog_info(self):
        self.prog_info = self.read_sheet('Programs cost and coverage', [0], 'dict')

    def get_prog_annual(self):
        spending = self.spreadsheet.parse('Programs annual spending', index_col=[0,1])
        # when no values specified, program is removed. In this case assume baseline coverage constant
        for programType, yearValue in spending.iterrows():
            if self.prog_annual_spend.get(programType[0]) is None:
                self.prog_annual_spend[programType[0]] = {}
            self.prog_annual_spend[programType[0]][programType[1]] = [list(yearValue.index), yearValue.tolist()]

    def define_iycf(self):
        """ Returns a dict with values as a list of two tuples (age, modality)."""
        IYCFpackages = self.read_sheet('IYCF packages', [0,1])
        packagesDict = {}
        for packageName, package in IYCFpackages.groupby(level=[0, 1]):
            if packageName[0] not in packagesDict:
                packagesDict[packageName[0]] = []
            for mode in package:
                col = package[mode]
                if col.notnull()[0]:
                    if mode == 'Mass media':
                        ageModeTuple = [(pop, mode) for pop in self.child_ages[:-1]] # exclude 24-59 months
                    else:
                        ageModeTuple = [(packageName[1], mode)]
                    packagesDict[packageName[0]] += ageModeTuple
        return packagesDict

    def get_iycf_target(self, package_modes):
        """ Creates the frac of pop targeted by each IYCF package.
        Note that frac in community and mass media assumed to be 1.
        Note also this fraction can exceed 1, and is adjusted for the target pop calculations of the Programs class """
        pop_data = read_excel(self.input, sheet='Baseline year population inputs', index_col=[0,1]).loc['Population data']
        frac_pw = float(pop_data.loc['Percentage of pregnant women attending health facility'])
        frac_child = float(pop_data.loc['Percentage of children attending health facility'])
        # target pop is the sum of fractions exposed to modality in each age band
        target = {}
        for name, package in package_modes.iteritems():
            target[name] = {}
            for pop, mode in package:
                if target[name].get(pop) is None:
                    target[name][pop] = 0.
                if mode == 'Health facility':
                    if 'month' in pop: # children
                        target[name][pop] += frac_child
                    else: # pregnant women
                        target[name][pop] += frac_pw
                else: # community or mass media
                    target[name][pop] += 1
        # convert pw to age bands and set missing children to 0
        new_target = dcp(target)
        for name in target.iterkeys():
            if 'Pregnant women' in target[name]:
                new_target[name].update({age:target[name]['Pregnant women'] for age in self.settings.pw_ages})
                new_target[name].pop('Pregnant women')
            for age in self.settings.child_ages:
                if age not in target[name]:
                    new_target[name].update({age:0})

    def get_iycf_cost(self, package_modes):
        iycf_cost = self.read_sheet('IYCF cost', [0,1]).loc['Field'].to_dict('index')
        package_cost = {}
        for name, package in package_modes.iteritems():
            cost = 0.
            for pop, mode in package:
                cost += iycf_cost[pop][mode]
            package_cost[name] = cost
        self.prog_info['unit cost'].update(package_cost)

    def create_age_bands(self, my_dict, keys, ages, pop):
        for key in keys:  # could be program, ages
            subDict = my_dict[key].pop(pop, None)
            newAgeGroups = {age:subDict for age in ages if subDict is not None}
            my_dict[key].update(newAgeGroups)
        return my_dict

    def read_sheet(self, name, cols, dict_orient=None, skiprows=None):
        df = self.spreadsheet.parse(name, index_col=cols, skiprows=skiprows).dropna(how='all')
        if dict_orient:
            df = df.to_dict(dict_orient)
        return df

if __name__ == "__main__":
    InputData('../applications/master/data/national/master_input.xlsx')
    DefaultParams()

