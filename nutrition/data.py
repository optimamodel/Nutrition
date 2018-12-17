import numpy as np
import pandas
import sciris as sc
from . import settings, populations, utils, programs

# TODO (possible): we may want to merge this class with InputData to make another class (DatabookData).
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
        self.rr_space_bo = None
        self.or_space_prog = None
        self.or_bf_prog = None
        self.man_mam = False
        self.arr_rr_death = sc.odict()
        # read data
        self.spreadsheet = default_data
        self.input_data = input_data
        self.read_spreadsheet()
        self.spreadsheet = None
        self.input_data = None
        return None
    
    def __repr__(self):
        output  = sc.prepr(self)
        return output

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
            for risk, value in areas.items():
                if self.prog_areas.get(risk) is None:
                    self.prog_areas[risk] = []
                if not value:
                    self.prog_areas[risk].append(program)

    def pop_risks(self):
        areas = utils.read_sheet(self.spreadsheet, 'Population risk areas', [0])
        booleanFrame = areas.isnull()
        for program, areas in booleanFrame.iterrows():
            for risk, value in areas.items():
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
        or_sheet = utils.read_sheet(self.spreadsheet, 'Odds ratios', [0,1], skiprows=18).dropna(axis=1, how='all')
        self.or_space_prog = or_sheet.loc['Odds ratios for optimal birth spacing by program'].to_dict('index')

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
        self.rr_space_bo = bo_sheet.loc['Relative risk by birth spacing'].to_dict('index')
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
        for age, progCatTypeDict in mydict.items():
            result[age] = sc.odict()
            for progCatType in progCatTypeDict.items():
                keys = progCatType[0]
                val = progCatType[1]
                result[age].update({keys[0]:{keys[1]:{keys[2]:val}}})
        return result

    def make_dict2(self, mydict):
        """ creating relative risk dict """
        res_dict = sc.odict()
        for age in mydict.keys():
            res_dict[age] = sc.odict()
            for condCat in mydict[age].keys():
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
        for age in mydict.keys():
            res_dict[age] = sc.odict()
            for condCat in mydict[age].keys():
                cat = condCat[1]
                if res_dict[age].get(cat) is None:
                    res_dict[age][cat] = mydict[age][condCat]
        return res_dict

# TODO (possible): we may want to merge this class with InputData to make another class (DatabookData).
class InputData(object):
    """ Container for all the region-specific data (prevalences, mortality rates etc) read in from spreadsheet"""
    def __init__(self, data, recalc=False):
        self.spreadsheet = data
        self.settings = settings.Settings()
        self.demo = None
        self.proj = sc.odict()
        self.death_dist = sc.odict()
        self.risk_dist = sc.odict()
        self.causes_death = None
        self.time_trends = sc.odict()
        self.birth_space = None
        self.incidences = sc.odict()
        self.pw_agedist = []
        self.wra_proj = []
        self.t = None
        self.recalc = recalc # Whether or not to recalculate formulas

        self.get_demo()
        self.get_proj()
        self.get_risk_dist()
        self.get_death_dist()
        self.get_time_trends()
        self.get_incidences()

    def __repr__(self):
        output  = sc.prepr(self)
        return output


    ## DEMOGRAPHICS ##

    def get_demo(self):
        baseline = utils.read_sheet(self.spreadsheet, 'Baseline year population inputs', [0,1])
        demo = sc.odict()
        # the fields that group the data in spreadsheet
        fields = ['Population data', 'Food', 'Age distribution of pregnant women', 'Mortality', 'Other risks']
        for field in fields:
            demo.update(baseline.loc[field].to_dict('index'))
        self.demo = {key: item['Data'] for key, item in demo.items()}
        self.demo['Birth dist'] = baseline.loc['Birth outcome distribution'].to_dict()['Data']
        t = baseline.loc['Projection years']
        self.t = [int(t.loc['Baseline year (projection start year)']['Data']), int(t.loc['End year']['Data'])]
        # birth spacing
        self.birth_space = baseline.loc['Birth spacing'].to_dict()['Data']
        self.birth_space.pop('Total (must be 100%)', None)
        # fix ages for PW
        baseline = utils.read_sheet(self.spreadsheet, 'Baseline year population inputs', [0])
        for row in baseline.loc['Age distribution of pregnant women'].iterrows():
            self.pw_agedist.append(row[1]['Data'])
        return None

    def get_proj(self):
        # drops rows with any na
        proj = utils.read_sheet(self.spreadsheet, 'Demographic projections', cols=[0], dropna='any')
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
        for outer, ageCat in riskDist.items():
            self.risk_dist[outer] = sc.odict()
            for age, catValue in ageCat.items():
                self.risk_dist[outer][age] = dict()
                for cat, value in catValue.items():
                    newCat = cat.split(' ',1)[0]
                    self.risk_dist[outer][age][newCat] = value
        # get anaemia
        dist = utils.read_sheet(self.spreadsheet, 'Nutritional status distribution', [0,1], skiprows=12)
        self.risk_dist['Anaemia'] = sc.odict()
        if 1: # not self.recalc: # CK: for future when we implement reload
            anaem = dist.loc['Anaemia', 'Prevalence of iron deficiency anaemia'].to_dict()
#        else:
#            # CK: Spreadsheet recalculation #1
#            all_anaem = dist.loc['Anaemia', 'Prevalence of anaemia'].to_dict()
#            baseline = utils.read_sheet(self.spreadsheet, 'Baseline year population inputs')
#            index = np.array(baseline['Field']).tolist().index('Percentage of anaemia that is iron deficient')
#            iron_pct = np.array(baseline['Data'])[index]
#            anaem = {key:val*iron_pct for key,val in all_anaem.items()}
        for age, prev in anaem.items():
            self.risk_dist['Anaemia'][age] = dict()
            self.risk_dist['Anaemia'][age]['Anaemic'] = prev
            self.risk_dist['Anaemia'][age]['Not anaemic'] = 1.-prev
        # get breastfeeding dist
        dist = utils.read_sheet(self.spreadsheet, 'Breastfeeding distribution', [0,1])
        self.risk_dist['Breastfeeding'] = dist.loc['Breastfeeding'].to_dict()

    def get_time_trends(self):
        trends = utils.read_sheet(self.spreadsheet, 'Time trends', cols=[0,1], dropna=False)
        self.time_trends['Stunting'] = trends.loc['Stunting prevalence (%)'].loc['Children 0-59 months'].values.tolist()[:1]
        self.time_trends['Wasting'] = trends.loc['Wasting prevalence (%)'].loc['Children 0-59 months'].values.tolist()[:1]
        self.time_trends['Anaemia'] = trends.loc['Anaemia prevalence (%)'].values.tolist()[:3] # order is (children, PW, WRA)
        self.time_trends['Breastfeeding'] = trends.loc['Prevalence of age-appropriate breastfeeding'].values.tolist()[:2] # 0-5 months, 6-23 months
        self.time_trends['Mortality'] = trends.loc['Mortality'].values.tolist() # under 5, maternal

    def get_incidences(self):
        self.incidences = utils.read_sheet(self.spreadsheet, 'Incidence of conditions', [0], to_odict=True)

    ### MORTALITY ###

    def get_death_dist(self):
        # read in with helpful column names, ignore the final row of each sub-table
        deathdist = utils.read_sheet(self.spreadsheet, 'Causes of death', [0, 1], skiprows=1)
        neonates = deathdist.loc['Neonatal'].ix[:-1]
        deathdist = utils.read_sheet(self.spreadsheet, 'Causes of death', [0, 1], skiprows=12)
        children = deathdist.loc['Children'].ix[:-1]
        deathdist = utils.read_sheet(self.spreadsheet, 'Causes of death', [0, 1], skiprows=24)
        pw = deathdist.loc['Pregnant women'].ix[:-1]
        dist = pandas.concat([neonates['<1 month'], children, pw['Pregnant women.1']], axis=1, sort=False).fillna(0)
        for cause in dist.index:
            self.death_dist[cause] = sc.odict()
            for age in self.settings.child_ages + self.settings.pw_ages:
                if 'PW' in age:
                    # stratify the pregnant women
                    self.death_dist[cause][age] = dist['Pregnant women.1'][cause]
                else:
                    self.death_dist[cause][age] = dist[age][cause]
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
        self.costtype = None
        self.prog_deps = None
        self.prog_target = None
        self.famplan_methods = None
        self.impacted_pop = default_data.impacted_pop
        self.prog_areas = default_data.prog_areas

        # load data
        self.get_prog_info()
        self.get_prog_target()
        self.get_prog_deps()
        self.get_ref_progs()
        self.get_famplan_methods()
        self.create_iycf()
        self.spreadsheet = None # Reset to save memory
        self.validate()

    def __repr__(self):
        output  = sc.prepr(self)
        return output

    def validate(self):
        """ Validate program data """
        invalid = []
        for progname in self.base_prog_set:
            cov = self.base_cov[progname]
            if cov < 0 or cov > 1:
                errormsg = 'Baseline coverage is outside the interval (0, 100) for %s' %progname
                invalid.append(errormsg)
            sat = self.sat[progname]
            if sat < 0 or sat > 1:
                errormsg = 'Saturation is outside the interval (0, 100) for %s' %progname
                invalid.append(errormsg)
            cost = self.costs[progname]
            if cost <= 0:
                errormsg = 'Cost is 0 or negative for %s' %progname
                invalid.append(errormsg)
            if progname not in self.prog_target.keys():
                errormsg = 'Target population not defined for %s' % progname
                invalid.append(errormsg)
            elif sum(self.prog_target[progname].values()) == 0:
                errormsg = 'Target population is 0 for %s' %progname
                invalid.append(errormsg)
        if invalid:
            errors = '\n\n'.join(invalid)
            raise Exception(errors)

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
            for dependType, value in dependency.items():
                if sc.isstring(value): # cell not empty
                    programDep[program][dependType] = value.replace(", ", ",").split(',') # assumes programs separated by ", "
                else:
                    programDep[program][dependType] = []
        # pad the remaining programs
        missingProgs = list(set(self.base_prog_set) - set(programDep.keys()))
        for program in missingProgs:
            programDep[program] = sc.odict()
            for field in deps.columns:
                programDep[program][field] = []
        self.prog_deps = programDep

    def get_famplan_methods(self):
        self.famplan_methods = utils.read_sheet(self.spreadsheet, 'Programs family planning', [0], 'index')

    def get_prog_info(self):
        sheet = utils.read_sheet(self.spreadsheet, 'Programs cost and coverage')
        self.base_prog_set = sheet.iloc[:,0].tolist()
        self.base_cov = sc.odict(zip(self.base_prog_set, sheet.iloc[:,1].tolist()))
        self.sat = sc.odict(zip(self.base_prog_set, sheet.iloc[:,2].tolist()))
        self.costs = sc.odict(zip(self.base_prog_set, sheet.iloc[:,3].tolist()))
        costtypes = utils.format_costtypes(sheet.iloc[:,4].tolist())
        self.costtype = sc.odict(zip(self.base_prog_set, costtypes))

    def create_iycf(self):
        packages = self.define_iycf()
        # remove IYCF from base progs if it isn't appropriately defined (avoid error in baseline)
        remprog = [key for key,val in packages.iteritems() if not val]
        self.base_prog_set = [prog for prog in self.base_prog_set if prog not in remprog]
        packages = sc.odict({key: val for key,val in packages.iteritems() if val})
        target = self.get_iycf_target(packages)
        self.prog_target.update(target)

    def define_iycf(self):
        """ Returns a dict with values as a list of two tuples (age, modality)."""
        IYCFpackages = self.spreadsheet.parse(sheet_name='IYCF packages', index_col=[0,1])
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
        for name, package in package_modes.items():
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
        for name in target.keys():
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
    
    def __init__(self, country=None, region=None, name=None, demo_data=None, prog_data=None, default_params=None,
                 pops=None, prog_info=None, doload=False, inputspath=None, defaultspath=None, fromfile=None, project=None):
        
        self.country = country
        self.region = region
        
        self.demo_data = demo_data  # demo = demographic
        self.prog_data = prog_data
        self.default_params = default_params  # TODO: this should probably be phased out once the InputData and DefaultParams classes get merged
        # The next three attributes are used to initialize a Model object.
        self.pops = pops  # populations
        self.prog_info = prog_info  # program info
        self.t = None  # start and end years for the simulation
        self.name = name
        self.modified = sc.now()
        if doload:
            self.load(project=project)
        return None
    
    def __repr__(self):
        output  = sc.prepr(self)
        return output
    
    def load(self, project=None):
        # Handle inputs
        if project is None:
            raise Exception('Sorry, but you must supply a project for load().')
        
        # Pull the sheets from the project
        if self.name in project.spreadsheets.keys():
            spreadsheetkey = self.name
        else:
            spreadsheetkey = -1
        inputsheet    = project.inputsheet(spreadsheetkey)
        legacydefaultssheet = project.legacydefaultssheet  # TODO: this should be ultimately phased out.
        
        # Convert them to Pandas
        input_data     = inputsheet.pandas() 
        legacy_default_data   = legacydefaultssheet.pandas() # TODO: this should be ultimately phased out.  For now, we'll pull from this if the worksheets are missing in input_data

        # If the 'Programs impacted population' worksheet is in input_data, then we are working with one of the newer
        # databooks, so pull the default data from input_data.
        if 'Programs impacted population' in input_data.sheet_names:
            default_data = input_data

        # Otherwise, pull the default data from the legacy spreadsheet.
        else:
            default_data = legacy_default_data
        
        # Read them into actual data
        try:
            self.demo_data = InputData(input_data)  # demo_ here is demographic_
        except Exception as E:
            raise Exception('Error in databook: %s'%str(E))
        try:
            self.default_params = DefaultParams(default_data, input_data)
            self.default_params.compute_risks(self.demo_data)
            self.prog_data = ProgData(input_data, self.default_params)
        except Exception as E:
            raise Exception('Error in program data: %s'%str(E))
        try:
            self.pops = populations.set_pops(self.demo_data, self.default_params)
        except Exception as E:
            raise Exception('Error in creating populations, check data and defaults books: %s'%str(E))
        self.prog_info = programs.ProgramInfo(self.prog_data)
        self.t = self.demo_data.t
        self.modified = sc.now()
        return None
    
    def prog_names(self):
        ''' WARNING, hacky function to get program names '''
        names = self.prog_data.base_prog_set
        return names