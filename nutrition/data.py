import numpy as np
import pandas
import sciris.core as sc
from . import settings, populations, utils, programs
import numpy as np

class Spreadsheet(object):
    ''' A class for reading and writing spreadsheet data in binary format, so a project contains the spreadsheet loaded '''
    
    def __init__(self, filename=None):
        self.data = None
        self.filename = None
        if filename is not None: self.load(filename)
        return None
    
    def __repr__(self):
        output  = sc.desc(self)
        return output
    
    def load(self, filename=None):
        if filename is not None:
            filepath = sc.makefilepath(filename=filename)
            self.filename = filepath
            with open(filepath, mode='rb') as f: 
                self.data = f.read()
        else:
            print('No filename specified; aborting.')
        return None
    
    def save(self, filename=None):
        if filename is None:
            if self.filename is not None: filename = self.filename
        if filename is not None:
            filepath = sc.makefilepath(filename=filename)
            with open(filepath, mode='wb') as f:
                f.write(self.data)
            print('Spreadsheet saved to %s.' % filepath)
        return filepath
            

class DefaultParams(object):
    def __init__(self, default_data, input_data):
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
        self.arr_rr_death = sc.odict()
        # read data
        self.spreadsheet = default_data
        self.input_data = input_data
        self.read_spreadsheet()
        self.rem_spreadsheet(default_data.io)
        return None
    
    def __repr__(self):
        output  = sc.desc(self)
        return output

    def rem_spreadsheet(self, default_path):
        self.spreadsheet.close()
        self.spreadsheet = Spreadsheet(default_path) # Load spreadsheet binary file into project -- WARNING, only partly implemented since not sure how to read from

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
        treatsam = self.input_data.parse(sheet_name='Treatment of SAM')
        add_man = treatsam.iloc[0]['Add extension']
        if pandas.notnull(add_man):
            self.man_mam = True

    def impact_pop(self):
        sheet = utils.read_sheet(self.spreadsheet, 'Programs impacted population', [0,1])
        impacted = sc.odict()
        for pop in ['Children', 'Pregnant women', 'Non-pregnant WRA', 'General population']:
            impacted.update(sheet.loc[pop].to_dict(orient='index'))
        self.impacted_pop = impacted

    def prog_risks(self):
        areas = utils.read_sheet(self.spreadsheet, 'Program risk areas', [0])
        booleanFrame = areas.isnull()
        for program, areas in booleanFrame.iterrows():
            for risk, value in areas.iteritems():
                if self.prog_areas.get(risk) is None:
                    self.prog_areas[risk] = []
                if not value:
                    self.prog_areas[risk].append(program)

    def pop_risks(self):
        areas = utils.read_sheet(self.spreadsheet, 'Population risk areas', [0])
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
        rr_sheet = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=1)
        rr = rr_sheet.loc['Stunting'].to_dict()
        self.rr_death['Stunting'] = self.make_dict2(rr)
        # wasting
        rr_sheet = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=28)
        rr = rr_sheet.loc['Wasting'].to_dict()
        self.rr_death['Wasting'] = self.make_dict2(rr)
        # anaemia
        rr_sheet = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=55).dropna(axis=1, how='all')
        rr = rr_sheet.loc['Anaemia'].to_dict()
        self.rr_death['Anaemia'] = self.make_dict2(rr)
        # currently no impact on mortality for anaemia
        self.rr_death['Anaemia'].update({age:{cat:{'Diarrhoea':1} for cat in self.settings.anaemia_list} for age in self.settings.child_ages})
        # breastfeeding
        rr_sheet = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=64)
        rr = rr_sheet.loc['Breastfeeding'].to_dict()
        self.rr_death['Breastfeeding'] = self.make_dict2(rr)
        # diarrhoea
        rr_sheet = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=103).dropna(axis=1, how='all')
        rr = rr_sheet.loc['Diarrhoea'].to_dict()
        self.rr_dia = self.make_dict3(rr)

    def compute_risks(self, input_data=None):
        """ Turn rr_death into an array"""
        for age in self.settings.child_ages:
            self.arr_rr_death[age] = np.zeros((self.settings.n_cats, len(input_data.causes_death)))
            stunting = self.rr_death['Stunting'][age]
            wasting = self.rr_death['Wasting'][age]
            bf = self.rr_death['Breastfeeding'][age]
            anaemia = self.rr_death['Anaemia'][age]
            for i, cats in enumerate(self.settings.all_cats):
                stuntcat = cats[0]
                wastcat = cats[1]
                anaemcat = cats[2]
                bfcat = cats[3]
                for j, cause in enumerate(input_data.causes_death):
                    stunt = stunting[stuntcat].get(cause,1)
                    wast = wasting[wastcat].get(cause,1)
                    anaem = anaemia[anaemcat].get(cause,1)
                    breast = bf[bfcat].get(cause,1)
                    self.arr_rr_death[age][i,j] = stunt*wast*anaem*breast

    def odds_ratios(self):
        or_sheet = utils.read_sheet(self.spreadsheet, 'Odds ratios', [0,1], skiprows=1)
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
        self.or_bf_prog = or_sheet.loc['Odds ratios for correct breastfeeding by program'].to_dict('index')

    def get_bo_progs(self):
        progs = utils.read_sheet(self.spreadsheet, 'Programs birth outcomes', [0,1], 'index')
        newprogs = sc.odict()
        for program in progs.keys():
            if not newprogs.get(program[0]):
                newprogs[program[0]] = sc.odict()
            newprogs[program[0]][program[1]] = progs[program]
        self.bo_progs = newprogs

    def anaemia_progs(self):
        anaem_sheet = utils.read_sheet(self.spreadsheet, 'Programs anemia', [0,1])
        self.rr_anaem_prog = anaem_sheet.loc['Relative risks of anaemia when receiving intervention'].to_dict(orient='index')
        self.or_anaem_prog = anaem_sheet.loc['Odds ratios of being anaemic when covered by intervention'].to_dict(orient='index')

    def wasting_progs(self):
        wastingSheet = utils.read_sheet(self.spreadsheet, 'Programs wasting', [0,1])
        treatsam = wastingSheet.loc['Odds ratio of SAM when covered by program'].to_dict(orient='index')
        manman = wastingSheet.loc['Odds ratio of MAM when covered by program'].to_dict(orient='index')
        self.or_wasting_prog['SAM'] = treatsam
        if self.man_mam:
            self.or_wasting_prog['MAM'] = {'Treatment of SAM': manman['Management of MAM'] }

    def get_child_progs(self):
        self.child_progs = utils.read_sheet(self.spreadsheet, 'Programs for children', [0,1,2], to_odict=True)

    def get_pw_progs(self):
        self.pw_progs = utils.read_sheet(self.spreadsheet, 'Programs for PW', [0,1,2], to_odict=True)

    def get_bo_risks(self):
        bo_sheet = utils.read_sheet(self.spreadsheet, 'Birth outcome risks', [0,1], skiprows=[0])
        ors = bo_sheet.loc['Odds ratios for conditions'].to_dict('index')
        self.or_cond_bo['Stunting'] = ors['Stunting (HAZ-score < -2)']
        self.or_cond_bo['MAM'] = ors['MAM (WHZ-score between -3 and -2)']
        self.or_cond_bo['SAM'] = ors['SAM (WHZ-score < -3)']
        self.rr_age_order = bo_sheet.loc['Relative risk by birth age and order'].to_dict('index')
        self.rr_interval = bo_sheet.loc['Relative risk by birth interval'].to_dict('index')
        self.rr_death['Birth outcomes'] = bo_sheet.loc['Relative risks of neonatal causes of death'].to_dict()

    def get_iycf_effects(self, iycf_packs):
        # TODO: need something that catches if iycf packages not included at all.
        effects = utils.read_sheet(self.spreadsheet, 'IYCF odds ratios', [0,1,2])
        bf_effects = effects.loc['Odds ratio for correct breastfeeding']
        stunt_effects = effects.loc['Odds ratio for stunting']
        self.or_bf_prog.update(self.create_iycf(bf_effects, iycf_packs))
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
        IYCFpackages = self.input_data.parse(sheet_name='IYCF packages', index_col=[0,1])
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
                    res_dict[age][cat] = dict() # CK TEST
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
    def __init__(self, data):
        self.spreadsheet = data
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
        self.t = None

        self.get_demo()
        self.get_proj()
        self.get_risk_dist()
        self.get_death_dist()
        self.get_time_trends()
        self.get_fertility_risks()
        self.get_incidences()
        self.get_famplan_methods()
        self.rem_spreadsheet(data.io)

    def __repr__(self):
        output  = sc.desc(self)
        return output

    def rem_spreadsheet(self, filepath):
        self.spreadsheet.close()
        self.spreadsheet = Spreadsheet(filepath)

    ## DEMOGRAPHICS ##

    def get_demo(self):
        baseline = utils.read_sheet(self.spreadsheet, 'Baseline year population inputs', [0,1])
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
        t = baseline.loc['Projection years']
        self.t = [int(t.loc['Baseline year (projection start year)']['Data']), int(t.loc['End year']['Data'])]
        # fix ages for PW
        baseline = utils.read_sheet(self.spreadsheet, 'Baseline year population inputs', [0])
        for row in baseline.loc['Age distribution of pregnant women'].iterrows():
            self.pw_agedist.append(row[1]['Data'])

    def get_proj(self):
        # drops rows with any na
        proj = self.spreadsheet.parse(sheet_name='Demographic projections', index_col=[0]).dropna(how='any')
        # dict of lists to support indexing
        for column in proj:
            self.proj[column] = proj[column].tolist()
        # wra pop projections list in increasing age order
        for age in self.settings.wra_ages:
            self.wra_proj.append(proj[age].tolist())

    def get_risk_dist(self):
        dist = utils.read_sheet(self.spreadsheet, 'Nutritional status distribution', [0,1])
        # dist = dist.drop(dist.index[[1]])
        riskDist = sc.odict()
        for field in ['Stunting (height-for-age)', 'Wasting (weight-for-height)']:
            riskDist[field.split(' ',1)[0]] = dist.loc[field].dropna(axis=1, how='all').to_dict('dict')
        # fix key refs (surprisingly hard to do in Pandas)
        for outer, ageCat in riskDist.iteritems():
            self.risk_dist[outer] = sc.odict()
            for age, catValue in ageCat.iteritems():
                self.risk_dist[outer][age] = dict()
                for cat, value in catValue.iteritems():
                    newCat = cat.split(' ',1)[0]
                    self.risk_dist[outer][age][newCat] = value
        # get anaemia
        dist = utils.read_sheet(self.spreadsheet, 'Nutritional status distribution', [0,1], skiprows=12)
        self.risk_dist['Anaemia'] = sc.odict()
        anaem = dist.loc['Anaemia', 'Prevalence of iron deficiency anaemia'].to_dict()
        for age, prev in anaem.iteritems():
            self.risk_dist['Anaemia'][age] = dict()
            self.risk_dist['Anaemia'][age]['Anaemic'] = prev
            self.risk_dist['Anaemia'][age]['Not anaemic'] = 1.-prev
        # get breastfeeding dist
        dist = utils.read_sheet(self.spreadsheet, 'Breastfeeding distribution', [0,1])
        self.risk_dist['Breastfeeding'] = dist.loc['Breastfeeding'].to_dict()

    def get_time_trends(self):
        trends = self.spreadsheet.parse(sheet_name='Time trends', index_col=[0,1])
        self.time_trends['Stunting'] = trends.loc['Stunting prevalence (%)'].loc['Children 0-59 months'].values.tolist()[:1]
        self.time_trends['Wasting'] = trends.loc['Wasting prevalence (%)'].loc['Children 0-59 months'].values.tolist()[:1]
        self.time_trends['Anaemia'] = trends.loc['Anaemia prevalence (%)'].values.tolist()[:3] # order is (children, PW, WRA)
        self.time_trends['Breastfeeding'] = trends.loc['Prevalence of age-appropriate breastfeeding'].values.tolist()[:2] # 0-5 months, 6-23 months
        self.time_trends['Mortality'] = trends.loc['Mortality'].values.tolist() # under 5, maternal

    def get_fertility_risks(self):
        fert = utils.read_sheet(self.spreadsheet, 'Fertility risks', [0,1])
        self.birth_age = fert.loc['Birth age and order'].iloc[:,0].to_dict()
        self.birth_int = fert.loc['Birth intervals'].iloc[:,0].to_dict()

    def get_incidences(self):
        self.incidences = utils.read_sheet(self.spreadsheet, 'Incidence of conditions', [0], to_odict=True)

    def get_famplan_methods(self):
        self.famplan_methods = utils.read_sheet(self.spreadsheet, 'Programs family planning', [0], 'index')

    ### MORTALITY ###

    def get_death_dist(self):
        death_dist = utils.read_sheet(self.spreadsheet, 'Causes of death', [0], 'index')
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

class ProgData(object):
    """Stores all the settings for each project, defined by the user"""
    def __init__(self, data, default_data):
        self.settings = settings.Settings()
        self.spreadsheet = data
        self.prog_set = []
        self.base_prog_set = []
        self.base_cov = []
        self.ref_progs = []
        self.sat = None
        self.costs = None
        self.prog_deps = None
        self.prog_target = None
        self.famplan_methods = None
        self.impacted_pop = default_data.impacted_pop
        self.prog_areas = default_data.prog_areas

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
        targetPopSheet = utils.read_sheet(self.spreadsheet, 'Programs target population', [0,1])
        targetPop = sc.odict()
        for pop in ['Children', 'Pregnant women', 'Non-pregnant WRA', 'General population']:
            targetPop.update(targetPopSheet.loc[pop].to_dict(orient='index'))
        self.prog_target = targetPop

    def get_ref_progs(self):
        reference = self.spreadsheet.parse(sheet_name='Reference programs', index_col=[0])
        self.ref_progs = list(reference.index)

    def get_prog_deps(self):
        deps = utils.read_sheet(self.spreadsheet, 'Program dependencies', [0])
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
        sheet = utils.read_sheet(self.spreadsheet, 'Programs cost and coverage')
        self.base_prog_set = sheet.iloc[:,0].tolist()
        self.base_cov = sc.odict(zip(self.base_prog_set, sheet.iloc[:,1].tolist()))
        self.sat = sc.odict(zip(self.base_prog_set, sheet.iloc[:,2].tolist()))
        self.costs = sc.odict(zip(self.base_prog_set, sheet.iloc[:,3].tolist()))

    def create_iycf(self):
        packages = self.define_iycf()
        target = self.get_iycf_target(packages)
        self.prog_target.update(target)

    def define_iycf(self):
        """ Returns a dict with values as a list of two tuples (age, modality)."""
        IYCFpackages = utils.read_sheet(self.spreadsheet, 'IYCF packages', [0,1])
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
        new_target = sc.dcp(target)
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

class Dataset(object):
    ''' Store all the data for a project '''
    
    def __init__(self, country='demo', region='demo', name=None, demo_data=None, prog_data=None, default_params=None,
                 pops=None, prog_info=None, doload=False, filepath=None):
        self.country = country
        self.region = region
        self.demo_data = demo_data
        self.prog_data = prog_data
        self.default_params = default_params
        self.pops = pops
        self.prog_info = prog_info
        self.t = None
        if name is None:
            try:    name = country+'_'+region
            except: name = 'default'
        self.name = name
        self.modified = sc.today()
        if doload:
            self.load(filepath=filepath)
        return None
    
    def __repr__(self):
        output  = sc.desc(self)
        return output
    
    def load(self, filepath=None):
        demo_data, prog_data, default_params, pops, prog_info = get_data(country=self.country, region=self.region, filepath=filepath, withpops=True)
        self.demo_data = demo_data
        self.prog_data = prog_data
        self.default_params = default_params
        self.pops = pops
        self.prog_info = prog_info
        self.t = demo_data.t
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
        input_data = pandas.ExcelFile(input_path)
        demo_data = InputData(input_data)
        default_data = pandas.ExcelFile(settings.default_params_path())
        default_params = DefaultParams(default_data, input_data)
        default_params.compute_risks(demo_data)
        prog_data = ProgData(input_data, default_params)
        pops = populations.set_pops(demo_data, default_params)
        prog_info = programs.ProgramInfo(prog_data)
    if asobj:
        output = Dataset(country, region, demo_data, prog_data, default_params, pops)
        return output
    else:
        if withpops:
            return demo_data, prog_data, default_params, pops, prog_info
        else:
            return demo_data, prog_data, default_params