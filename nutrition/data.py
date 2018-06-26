import settings, pandas, copy
import sciris.core as sc
from . import populations

class DefaultParams(object):
    def __init__(self, default_path, input_path):
        self.settings = settings.Settings()
        self.impacted_pop = None
        self.prog_areas = sc.odict()
        self.pop_areas = sc.odict()
        self.rr_death = sc.odict()
        self.or_cond = sc.odict()
        self.or_cond_bo = sc.odict()
        self.or_wasting_prog = sc.odict()
        self.rr_dia = None
        self.or_stunting_prog = None
        self.bo_progs = None
        self.rr_anaem_prog = None
        self.or_anaem_prog = None
        self.child_progs = None
        self.pw_progs = None
        self.rr_age_order = None
        self.rr_interval = None
        self.or_bf_prog = None
        self.man_mam = False
        # read data
        self.spreadsheet = pandas.ExcelFile(default_path)
        self.input_path = input_path
        self.read_spreadsheet()
        self.rem_spreadsheet()
    
    def __repr__(self):
        output  = sc.desc(self)
        return output

    def rem_spreadsheet(self):
        self.spreadsheet.close()
        self.spreadsheet = None

    def read_spreadsheet(self):
        self.extend_treatsam()
        self.impact_pop()
        self.prog_risks()
        self.pop_risks()
        self.anaemia_progs()
        self.wasting_progs()
        self.relative_risks()
        self.odds_ratios()
        self.get_child_progs()
        self.get_pw_progs()
        self.get_bo_progs()
        self.get_bo_risks()
        packages = self.define_iycf()
        self.get_iycf_effects(packages)

    def extend_treatsam(self):
        treatsam = pandas.read_excel(self.input_path, 'Treatment of SAM')
        add_man = treatsam.iloc[0]['Add extension']
        if pandas.notnull(add_man):
            self.man_mam = True

    def impact_pop(self):
        sheet = self.read_sheet('Programs impacted population', [0,1])
        impacted = sc.odict()
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
        rr = rr_sheet.loc['Stunting'].to_dict()
        self.rr_death['Stunting'] = self.make_dict2(rr)
        # wasting
        rr_sheet = self.read_sheet('Relative risks', [0,1,2], skiprows=28)
        rr = rr_sheet.loc['Wasting'].to_dict()
        self.rr_death['Wasting'] = self.make_dict2(rr)
        # anaemia
        rr_sheet = self.read_sheet('Relative risks', [0,1,2], skiprows=55).dropna(axis=1, how='all')
        rr = rr_sheet.loc['Anaemia'].to_dict()
        self.rr_death['Anaemia'] = self.make_dict2(rr)
        # currently no impact on mortality for anaemia
        self.rr_death['Anaemia'].update({age:{cat:{'Diarrhoea':1} for cat in self.settings.anaemia_list} for age in self.settings.child_ages})
        # breastfeeding
        rr_sheet = self.read_sheet('Relative risks', [0,1,2], skiprows=64)
        rr = rr_sheet.loc['Breastfeeding'].to_dict()
        self.rr_death['Breastfeeding'] = self.make_dict2(rr)
        # diarrhoea
        rr_sheet = self.read_sheet('Relative risks', [0,1,2], skiprows=103).dropna(axis=1, how='all')
        rr = rr_sheet.loc['Diarrhoea'].to_dict()
        self.rr_dia = self.make_dict3(rr)

    def odds_ratios(self):
        or_sheet = self.read_sheet('Odds ratios', [0,1], skiprows=1)
        this_or = or_sheet.loc['Condition'].to_dict('index')
        self.or_cond['Stunting'] = sc.odict()
        self.or_cond['Stunting']['Prev stunting'] = this_or['Given previous stunting (HAZ < -2 in previous age band)']
        self.or_cond['Stunting']['Diarrhoea'] = this_or['Diarrhoea (per additional episode)']
        self.or_cond['SAM'] = sc.odict()
        self.or_cond['SAM']['Diarrhoea'] = or_sheet.loc['Wasting'].to_dict('index')['For SAM per additional episode of diarrhoea']
        self.or_cond['MAM'] = sc.odict()
        self.or_cond['MAM']['Diarrhoea'] = or_sheet.loc['Wasting'].to_dict('index')['For MAM per additional episode of diarrhoea']
        self.or_cond['Anaemia'] = sc.odict()
        self.or_cond['Anaemia']['Severe diarrhoea'] = sc.odict()
        self.or_cond['Anaemia']['Severe diarrhoea'] = or_sheet.loc['Anaemia'].to_dict('index')['For anaemia per additional episode of severe diarrhoea']
        self.or_stunting_prog = or_sheet.loc['By program'].to_dict('index')

    def get_bo_progs(self):
        progs = self.read_sheet('Programs birth outcomes', [0,1], 'index')
        newprogs = sc.odict()
        for program in progs.keys():
            if not newprogs.get(program[0]):
                newprogs[program[0]] = sc.odict()
            newprogs[program[0]][program[1]] = progs[program]
        self.bo_progs = newprogs

    def anaemia_progs(self):
        anaem_sheet = self.read_sheet('Programs anemia', [0,1])
        self.rr_anaem_prog = anaem_sheet.loc['Relative risks of anaemia when receiving intervention'].to_dict(orient='index')
        self.or_anaem_prog = anaem_sheet.loc['Odds ratios of being anaemic when covered by intervention'].to_dict(orient='index')

    def wasting_progs(self):
        wastingSheet = self.read_sheet('Programs wasting', [0,1])
        treatsam = wastingSheet.loc['Odds ratio of SAM when covered by program'].to_dict(orient='index')
        manman = wastingSheet.loc['Odds ratio of MAM when covered by program'].to_dict(orient='index')
        self.or_wasting_prog['SAM'] = treatsam
        if self.man_mam:
            self.or_wasting_prog['MAM'] = {'Treatment of SAM': manman['Management of MAM'] }

    def get_child_progs(self):
        self.child_progs = self.read_sheet('Programs for children', [0,1,2], to_odict=True)

    def get_pw_progs(self):
        self.pw_progs = self.read_sheet('Programs for PW', [0,1,2], to_odict=True)

    def get_bo_risks(self):
        bo_sheet = self.read_sheet('Birth outcome risks', [0,1], skiprows=[0])
        ors = bo_sheet.loc['Odds ratios for conditions'].to_dict('index')
        self.or_cond_bo['Stunting'] = ors['Stunting (HAZ-score < -2)']
        self.or_cond_bo['MAM'] = ors['MAM (WHZ-score between -3 and -2)']
        self.or_cond_bo['SAM'] = ors['SAM (WHZ-score < -3)']
        self.rr_age_order = bo_sheet.loc['Relative risk by birth age and order'].to_dict('index')
        self.rr_interval = bo_sheet.loc['Relative risk by birth interval'].to_dict('index')
        self.rr_death['Birth outcomes'] = bo_sheet.loc['Relative risks of neonatal causes of death'].to_dict()

    def get_iycf_effects(self, iycf_packs):
        # TODO: need something that catches if iycf packages not included at all.
        effects = self.read_sheet('IYCF odds ratios', [0,1,2])
        bf_effects = effects.loc['Odds ratio for correct breastfeeding']
        stunt_effects = effects.loc['Odds ratio for stunting']
        self.or_bf_prog = self.create_iycf(bf_effects, iycf_packs)
        self.or_stunting_prog.update(self.create_iycf(stunt_effects, iycf_packs))

    def create_iycf(self, effects, packages):
        """ Creates IYCF packages based on user input in 'IYCFpackages' """
        # non-empty cells denote program combination
        # get package combinations
        # create new program
        newPrograms = sc.odict()
        ORs = sc.odict()
        for key, item in packages.items():
            if newPrograms.get(key) is None:
                newPrograms[key] = sc.odict()
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
        IYCFpackages = pandas.read_excel(self.input_path, 'IYCF packages', index_col=[0,1])
        packagesDict = sc.odict()
        for packageName, package in IYCFpackages.groupby(level=[0, 1]):
            if packageName[0] not in packagesDict:
                packagesDict[packageName[0]] = []
            for mode in package:
                col = package[mode]
                if col.notnull()[0]:
                    if mode == 'Mass media':
                        ageModeTuple = [(pop, mode) for pop in self.settings.child_ages[:-1]] # exclude 24-59 months
                    else:
                        ageModeTuple = [(packageName[1], mode)]
                    packagesDict[packageName[0]] += ageModeTuple
        return packagesDict

    def read_sheet(self, name, cols, dictOrient=None, skiprows=None, to_odict=False):
        df = self.spreadsheet.parse(name, index_col=cols, skiprows=skiprows).dropna(how='all')
        if dictOrient:
            df = df.to_dict(dictOrient)
        elif to_odict:
            df = df.to_dict(into=sc.odict)
        return df

    def make_dict(self, mydict):
        """ myDict is a spreadsheet with 3 index cols, converted to dict using orient='index' """
        result = sc.odict()
        for age, progCatTypeDict in mydict.iteritems():
            result[age] = sc.odict()
            for progCatType in progCatTypeDict.iteritems():
                keys = progCatType[0]
                val = progCatType[1]
                result[age].update({keys[0]:{keys[1]:{keys[2]:val}}})
        return result

    def make_dict2(self, mydict):
        """ creating relative risk dict """
        res_dict = sc.odict()
        for age in mydict.iterkeys():
            res_dict[age] = sc.odict()
            for condCat in mydict[age].iterkeys():
                cond = condCat[0]
                cat = condCat[1]
                if res_dict[age].get(cat) is None:
                    res_dict[age][cat] = sc.odict()
                    res_dict[age][cat][cond] = mydict[age][condCat]
                elif res_dict[age][cat].get(cond) is None:
                    res_dict[age][cat][cond] = mydict[age][condCat]
        return res_dict

    def make_dict3(self, mydict):
        """ for rr diarrhoea """
        res_dict = sc.odict()
        for age in mydict.iterkeys():
            res_dict[age] = sc.odict()
            for condCat in mydict[age].iterkeys():
                cat = condCat[1]
                if res_dict[age].get(cat) is None:
                    res_dict[age][cat] = mydict[age][condCat]
        return res_dict

class InputData(object):
    """ Container for all the region-specific data (prevalences, mortality rates etc) read in from spreadsheet"""
    def __init__(self, filepath):
        self.spreadsheet = pandas.ExcelFile(filepath)
        self.settings = settings.Settings()
        self.demo = None
        self.proj = sc.odict()
        self.death_dist = sc.odict()
        self.risk_dist = sc.odict()
        self.causes_death = None
        self.time_trends = sc.odict()
        self.birth_age = None
        self.birth_int = None
        self.prog_target = None
        self.famplan_methods = None
        self.incidences = sc.odict()
        self.pw_agedist = []
        self.wra_proj = []
        self.samtomam = None
        self.mamtosam = None

        self.get_demo()
        self.get_proj()
        self.get_risk_dist()
        self.get_death_dist()
        self.get_time_trends()
        self.get_fertility_risks()
        self.get_incidences()
        self.get_famplan_methods()
        self.rem_spreadsheet()
    
    def __repr__(self):
        output  = sc.desc(self)
        return output

    def rem_spreadsheet(self):
        self.spreadsheet.close()
        self.spreadsheet = None

    ## DEMOGRAPHICS ##

    def get_demo(self):
        baseline = self.read_sheet('Baseline year population inputs', [0,1])
        demo = sc.odict()
        # the fields that group the data in spreadsheet
        fields = ['Population data', 'Food', 'Age distribution of pregnant women', 'Mortality', 'Other risks']
        for field in fields:
            demo.update(baseline.loc[field].to_dict('index'))
        self.demo = {key: item['Data'] for key, item in demo.iteritems()}
        self.demo['Birth dist'] = baseline.loc['Birth outcome distribution'].to_dict()['Data']
        # wasting
        self.mamtosam = self.demo.pop('Percentage of SAM cases that develop from MAM')
        self.samtomam = self.demo.pop('Percentage of SAM cases that only recover to MAM')
        # fix ages for PW
        baseline = self.read_sheet('Baseline year population inputs', [0])
        for row in baseline.loc['Age distribution of pregnant women'].iterrows():
            self.pw_agedist.append(row[1]['Data'])

    def get_proj(self):
        proj = self.read_sheet('Demographic projections', [0])
        # dict of lists to support indexing
        for column in proj:
            self.proj[column] = proj[column].tolist()
        # wra pop projections list in increasing age order
        for age in self.settings.wra_ages:
            self.wra_proj.append(proj[age].tolist())

    def get_risk_dist(self):
        dist = self.read_sheet('Nutritional status distribution', [0,1])
        # dist = dist.drop(dist.index[[1]])
        riskDist = sc.odict()
        for field in ['Stunting (height-for-age)', 'Wasting (weight-for-height)']:
            riskDist[field.split(' ',1)[0]] = dist.loc[field].dropna(axis=1, how='all').to_dict('dict')
        # fix key refs (surprisingly hard to do in Pandas)
        for outer, ageCat in riskDist.iteritems():
            self.risk_dist[outer] = sc.odict()
            for age, catValue in ageCat.iteritems():
                self.risk_dist[outer][age] = sc.odict()
                for cat, value in catValue.iteritems():
                    newCat = cat.split(' ',1)[0]
                    self.risk_dist[outer][age][newCat] = value
        # get anaemia
        dist = self.read_sheet('Nutritional status distribution', [0,1], skiprows=12)
        self.risk_dist['Anaemia'] = sc.odict()
        anaem = dist.loc['Anaemia', 'Prevalence of iron deficiency anaemia'].to_dict()
        for age, prev in anaem.iteritems():
            self.risk_dist['Anaemia'][age] = sc.odict()
            self.risk_dist['Anaemia'][age]['Anaemic'] = prev
            self.risk_dist['Anaemia'][age]['Not anaemic'] = 1.-prev
        # get breastfeeding dist
        dist = self.read_sheet('Breastfeeding distribution', [0,1])
        self.risk_dist['Breastfeeding'] = dist.loc['Breastfeeding'].to_dict()

    def get_time_trends(self):
        trends = self.spreadsheet.parse('Time trends', index_col=[0,1])
        self.time_trends['Stunting'] = trends.loc['Stunting prevalence (%)'].loc['Children 0-59 months'].values.tolist()[:1]
        self.time_trends['Wasting'] = trends.loc['Wasting prevalence (%)'].loc['Children 0-59 months'].values.tolist()[:1]
        self.time_trends['Anaemia'] = trends.loc['Anaemia prevalence (%)'].values.tolist()[:3] # order is (children, PW, WRA)
        self.time_trends['Breastfeeding'] = trends.loc['Prevalence of age-appropriate breastfeeding'].values.tolist()[:2] # 0-5 months, 6-23 months
        self.time_trends['Mortality'] = trends.loc['Mortality'].values.tolist() # under 5, maternal

    def get_fertility_risks(self):
        fert = self.read_sheet('Fertility risks', [0,1])
        self.birth_age = fert.loc['Birth age and order'].to_dict()['Percentage of births in category']
        self.birth_int = fert.loc['Birth intervals'].to_dict()['Percentage of births in category']

    def get_incidences(self):
        self.incidences = self.read_sheet('Incidence of conditions', [0], to_odict=True)

    def get_famplan_methods(self):
        self.famplan_methods = self.read_sheet('Programs family planning', [0], 'index')

    ### MORTALITY ###

    def get_death_dist(self):
        death_dist = self.read_sheet('Causes of death', [0], 'index')
        # convert 'Pregnant women' to age bands
        for key, value in death_dist.iteritems():
            self.death_dist[key] = sc.odict()
            pw_val = value['Pregnant women']
            for age in self.settings.pw_ages+self.settings.child_ages:
                if "PW" in age:
                    self.death_dist[key][age] = pw_val
                else:
                    self.death_dist[key][age] = value[age]
        # list causes of death
        self.causes_death = self.death_dist.keys()

    def read_sheet(self, name, cols, dict_orient=None, skiprows=None, to_odict=False):
        df = self.spreadsheet.parse(name, index_col=cols, skiprows=skiprows).dropna(how='all')
        if dict_orient:
            df = df.to_dict(dict_orient)
        return df

class ProgData(object):
    """Stores all the settings for each project, defined by the user"""
    def __init__(self, input_path):
        self.settings = settings.Settings()
        self.spreadsheet = pandas.ExcelFile(input_path)
        self.prog_set = []
        self.ref_progs = []
        self.prog_deps = None
        self.prog_info = None
        self.prog_target = None
        self.famplan_methods = None

        # load data
        self.get_prog_target()
        self.get_prog_deps()
        self.get_ref_progs()
        self.get_prog_info()
        self.create_iycf()
        self.rem_spreadsheet()
    
    def __repr__(self):
        output  = sc.desc(self)
        return output

    def rem_spreadsheet(self):
        self.spreadsheet.close()
        self.spreadsheet = None

    def get_prog_target(self):
        targetPopSheet = self.read_sheet('Programs target population', [0,1])
        targetPop = sc.odict()
        for pop in ['Children', 'Pregnant women', 'Non-pregnant WRA', 'General population']:
            targetPop.update(targetPopSheet.loc[pop].to_dict(orient='index'))
        self.prog_target = targetPop

    def get_ref_progs(self):
        reference = self.spreadsheet.parse('Reference programs', index_col=[0])
        self.ref_progs = list(reference.index)

    def get_prog_deps(self):
        deps = self.read_sheet('Program dependencies', [0])
        programDep = sc.odict()
        for program, dependency in deps.iterrows():
            programDep[program] = sc.odict()
            for dependType, value in dependency.iteritems():
                if isinstance(value, unicode): # cell not empty
                    programDep[program][dependType] = value.replace(", ", ",").split(',') # assumes programs separated by ", "
                else:
                    programDep[program][dependType] = []
        # pad the remaining programs
        missingProgs = list(set(self.prog_set) - set(programDep.keys()))
        for program in missingProgs:
            programDep[program] = sc.odict()
            for field in deps.columns:
                programDep[program][field] = []
        self.prog_deps = programDep

    def get_prog_info(self):
        self.prog_info = self.read_sheet('Programs cost and coverage', [0], to_odict=True)

    def create_iycf(self):
        packages = self.define_iycf()
        target = self.get_iycf_target(packages)
        self.prog_target.update(target)

    def define_iycf(self):
        """ Returns a dict with values as a list of two tuples (age, modality)."""
        IYCFpackages = self.read_sheet('IYCF packages', [0,1])
        packagesDict = sc.odict()
        for packageName, package in IYCFpackages.groupby(level=[0, 1]):
            if packageName[0] not in packagesDict:
                packagesDict[packageName[0]] = []
            for mode in package:
                col = package[mode]
                if col.notnull()[0]:
                    if mode == 'Mass media':
                        ageModeTuple = [(pop, mode) for pop in self.settings.child_ages[:-1]] # exclude 24-59 months
                    else:
                        ageModeTuple = [(packageName[1], mode)]
                    packagesDict[packageName[0]] += ageModeTuple
        return packagesDict

    def get_iycf_target(self, package_modes):
        """ Creates the frac of pop targeted by each IYCF package.
        Note that frac in community and mass media assumed to be 1.
        Note also this fraction can exceed 1, and is adjusted for the target pop calculations of the Programs class """
        pop_data = self.spreadsheet.parse('Baseline year population inputs', index_col=[0,1]).loc['Population data']
        frac_pw = float(pop_data.loc['Percentage of pregnant women attending health facility'])
        frac_child = float(pop_data.loc['Percentage of children attending health facility'])
        # target pop is the sum of fractions exposed to modality in each age band
        target = sc.odict()
        for name, package in package_modes.iteritems():
            target[name] = sc.odict()
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
        # convert pw to age bands and set missing children + wra to 0
        new_target = copy.deepcopy(target)
        for name in target.iterkeys():
            if 'Pregnant women' in target[name]:
                new_target[name].update({age:target[name]['Pregnant women'] for age in self.settings.pw_ages})
                new_target[name].pop('Pregnant women')
            for age in self.settings.all_ages:
                if age not in new_target[name]:
                    new_target[name].update({age:0})
        return new_target

    def create_age_bands(self, my_dict, keys, ages, pop):
        for key in keys:  # could be program, ages
            subDict = my_dict[key].pop(pop, None)
            newAgeGroups = {age:subDict for age in ages if subDict is not None}
            my_dict[key].update(newAgeGroups)
        return my_dict

    def read_sheet(self, name, cols, dict_orient=None, skiprows=None, to_odict=False):
        df = self.spreadsheet.parse(name, index_col=cols, skiprows=skiprows).dropna(how='all')
        if dict_orient:
            df = df.to_dict(dict_orient)
        elif to_odict:
            df = df.to_dict(into=sc.odict)
        return df

class UserOpts(object):
    """ Container for information provided by the front end, which are the user-defined settings for each scenario """
    def __init__(self, name, scen_type, t, prog_set, scen):
        self.name = name
        self.scen_type = scen_type
        self.t = t
        self.prog_set = prog_set
        self.scen = scen
    
    def __repr__(self):
        output  = sc.desc(self)
        return output

    def get_attr(self):
        return self.__dict__


class OptimOptsTest(object):
    """ Only for testing purposes. """
    def __init__(self, name, filepath=settings.default_opts_path()):
        self.spreadsheet = pandas.ExcelFile(filepath)

        self.name = name
        self.prog_set = []
        self.t = None
        self.mults = None
        self.fix_curr = None
        self.add_funds = None
        self.objs = None
        self.filter_progs = None
        self.get_prog_set()
        self.get_opts()

        delattr(self, 'spreadsheet')
    
    def __repr__(self):
        output  = sc.desc(self)
        return output

    def get_attr(self):
        return self.__dict__

    def get_prog_set(self):
        prog_sheet = self.read_sheet('Programs to include', [0])
        prog_sheet = prog_sheet[pandas.notnull(prog_sheet)]
        for program, value in prog_sheet.iterrows():
            self.prog_set.append(program)

    def get_opts(self):
        opts = self.spreadsheet.parse('Optimization options')
        self.t = [opts['start year'][0], opts['end year'][0]]
        self.objs = opts['objectives'][0].replace(' ','').split(',')
        mults = str(opts['multiples of flexible funding'][0]).replace(' ', '').split(',')
        self.mults = [int(x) for x in mults]
        fix_curr = opts['fix current funds'][0]
        self.fix_curr = True if fix_curr else False
        self.add_funds = opts['additional funds'][0]
        filter = opts['filter programs'][0]
        self.filter_progs = True if filter else False

    def read_sheet(self, name, cols, dict_orient=None, skiprows=None, to_odict=False):
        df = self.spreadsheet.parse(name, index_col=cols, skiprows=skiprows).dropna(how='all')
        if dict_orient:
            df = df.to_dict(dict_orient)
        elif to_odict:
            df = df.to_dict(into=sc.odict)
        return df

class ScenOptsTest(object):
    """ Only used for testing purposes. This information should be supplied by the frontend. """

    def __init__(self, name, scen_type, filepath=settings.default_opts_path()):
        self.spreadsheet = pandas.ExcelFile(filepath)

        self.name = name
        self.prog_set = []
        self.scen_type = scen_type
        self.scen = sc.odict()
        self.t = [2017, 2025]

        self.get_prog_set()
        if 'ov' in scen_type: # coverage scenario
            self.get_cov_scen()
        else:
            self.get_budget_scen()

        delattr(self, 'spreadsheet')
    
    def __repr__(self):
        output  = sc.desc(self)
        return output

    def get_attr(self):
        return self.__dict__

    def get_prog_set(self):
        prog_sheet = self.read_sheet('Programs to include', [0])
        prog_sheet = prog_sheet[pandas.notnull(prog_sheet)]
        for program, value in prog_sheet.iterrows():
            self.prog_set.append(program)

    def get_cov_scen(self):
        cov = self.spreadsheet.parse('Coverage scenario', index_col=[0,1])
        for prog in self.prog_set: # only programs included
            self.scen[prog] = cov.loc[prog,'Coverage'].tolist()

    def get_budget_scen(self):
        budget = self.spreadsheet.parse('Budget scenario', index_col=[0,1])
        for prog in self.prog_set: # only programs included
            self.scen[prog] = budget.loc[prog,'Spending'].tolist()

    def read_sheet(self, name, cols, dict_orient=None, skiprows=None, to_odict=False):
        df = self.spreadsheet.parse(name, index_col=cols, skiprows=skiprows).dropna(how='all')
        if dict_orient:
            df = df.to_dict(dict_orient)
        elif to_odict:
            df = df.to_dict(into=sc.odict)
        return df

class Dataset(object):
    ''' Store all the data for a project '''
    
    def __init__(self, country='default', region='default', demo_data=None, prog_data=None, default_params=None, pops=None, name=None, doload=False):
        self.country = country
        self.region = region
        self.demo_data = demo_data
        self.prog_data = prog_data
        self.default_params = default_params
        self.pops = pops
        if name is None: name = country+'_'+region
        self.name = name
        self.modified = sc.today()
        if doload:
            self.load()
        return None
    
    def __repr__(self):
        output  = sc.desc(self)
        return output
    
    def load(self):
        demo_data, prog_data, default_params, pops = get_data(self.country, self.region, withpops=True)
        self.demo_data = demo_data
        self.prog_data = prog_data
        self.default_params = default_params
        self.pops = pops
        self.modified = sc.today()
        return None
    
    def spit(self, withpops=False):
        ''' Hopefully temporary method to spit out a tuple, to match get_data '''
        if withpops:
            output = (self.demo_data, self.prog_data, self.default_params)
        else:
            output = (self.demo_data, self.prog_data, self.default_params, self.pops)
        return output
    
    def prog_names(self):
        names = self.prog_data.prog_info['baseline coverage'].keys()
        return names


def get_data(country=None, region=None, project=None, dataset=None, filepath=None, asobj=False, withpops=False):
    if project is not None:
        demo_data, prog_data, default_params, pops = project.dataset(dataset).spit()
    else:
        sim_type = 'national' if country == region else 'regional'
        if filepath is None:
            input_path = settings.data_path(country, region, sim_type)
        else:
            input_path = filepath
        # get data
        demo_data = InputData(input_path)
        prog_data = ProgData(input_path)
        default_params = DefaultParams(settings.default_params_path(), input_path)
        pops = populations.set_pops(demo_data, default_params)
    if asobj:
        output = Dataset(country, region, demo_data, prog_data, default_params, pops)
        return output
    else:
        if withpops:
            return demo_data, prog_data, default_params, pops
        else:
            return demo_data, prog_data, default_params