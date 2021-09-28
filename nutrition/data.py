import numpy as np
from scipy.stats import norm
import pandas
import sciris as sc
import re
from itertools import chain
from . import settings, populations, utils, programs

# This class is used to define an object which keeps a cache of all cells from the Excel databook/s that need to be
# calculated.  This cache used by RPC code that figures out what calculation values to send to the FE to be displayed
# in the grey non-editable cells in the GUI.
class CalcCellCache(object):
    def __init__(self):
        self.cachedict = sc.odict()

    # From the key string value, pull out the spreadsheet name, and row and col numbers (0-indexed).
    def _key_to_indices(self, keyval):
        sheetname = re.sub(':.*$', '', keyval)
        droptocolon = re.sub('.*:\[', '', keyval)
        dropcommatoend = re.sub(',.*$', '', droptocolon)
        rownum = int(dropcommatoend)
        droptocomma = re.sub('.*,', '', keyval)
        dropendbracket = re.sub('\]', '', droptocomma)
        colnum = int(dropendbracket)
        return (sheetname, rownum, colnum)

    # Write a single value to the cache.
    def write_cell(self, worksheet_name, row, col, val):
        cell_key = '%s:[%d,%d]' % (worksheet_name, row, col)
        self.cachedict[cell_key] = val

    # Write a row of values to the cache.
    def write_row(self, worksheet_name, row, col, vals):
        for ind in range(len(vals)):
            self.write_cell(worksheet_name, row, col + ind, vals[ind])

    # Write a column of values to the cache.
    def write_col(self, worksheet_name, row, col, vals):
        for ind in range(len(vals)):
            self.write_cell(worksheet_name, row + ind, col, vals[ind])

    # Read a value out of the cache, returning 0.0 if no entry is found.
    def read_cell(self, worksheet_name, row, col):
        cell_key = '%s:[%d,%d]' % (worksheet_name, row, col)
        if cell_key in self.cachedict:
            return self.cachedict[cell_key]
        else:
            print('ERROR: Sheet: %s, Row: %d, Col: %d is not in cache!' % (worksheet_name, row, col))
            return 0.0

    # Do a dump of the whole cache.
    def show(self):
        print(self.cachedict)

    # Check a value in the calculations cache against the cached value actually in the spreadsheet.
    def check_cell_against_worksheet_value(self, wb, worksheet_name, row, col):
        calc_val = self.read_cell(worksheet_name, row, col)
        wsheet_val = wb.readcells(method='openpyexcel', wbargs={'data_only': True},
                                  sheetname=worksheet_name, cells=[[row, col]])[0]
        if sc.approx(calc_val, wsheet_val):
            print('Sheet: %s, Row: %d, Col: %d -- match' % (worksheet_name, row, col))
        else:
            print('Sheet: %s, Row: %d, Col: %d -- MISMATCH' % (worksheet_name, row, col))
            print('-- calc cache value')
            print(calc_val)
            print('-- spreadsheet cached value')
            print(wsheet_val)

    # For all items in the calculations cache, check whether they match with what's in the spreadsheet.
    def check_all_cells_against_worksheet_values(self, wb):
        print('Calculations cache check against spreadsheet:')
        for key in self.cachedict.keys(): # TODO -- move worksheet load outside loop so don't have to reload for every cell
            (sheetname, rownum, colnum) = self._key_to_indices(key)
            self.check_cell_against_worksheet_value(wb, sheetname, rownum, colnum)


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
    
# TODO (possible): we may want to merge this class with DefaultParams to make another class (DatabookData).
class InputData(object):
    """ Container for all the region-specific data (prevalences, mortality rates etc) read in from spreadsheet"""
    def __init__(self, data, calcscache):
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
        self.cost_wasting = None
        self.cost_stunting = None
        self.cost_child_death = None
        self.cost_pw_death = None
        self.cost_child_anaemic = None
        self.cost_pw_anaemic = None
        self.calcscache = calcscache

        self.get_demo()
        self.get_proj()
        self.get_risk_dist()
        self.get_death_dist()
        self.get_time_trends()
        self.get_incidences()
        self.get_economic_cost()

    def __repr__(self):
        output  = sc.prepr(self)
        return output


    ## DEMOGRAPHICS ##

    def get_demo(self):
        # Load the main spreadsheet into a DataFrame.
        baseline = utils.read_sheet(self.spreadsheet, 'Baseline year population inputs', [0, 1])

        # Recalculate cells that need it, and remember in the calculations cache.
        frac_rice = baseline.loc['Food'].loc['Fraction eating rice as main staple food'].values[0]
        frac_wheat = baseline.loc['Food'].loc['Fraction eating wheat as main staple food'].values[0]
        frac_maize = baseline.loc['Food'].loc['Fraction eating maize as main staple food'].values[0]
        frac_other_staples = 1.0 - frac_rice - frac_wheat - frac_maize
        baseline.loc['Food'].loc['Fraction on other staples as main staple food'] = frac_other_staples
        self.calcscache.write_cell('Baseline year population inputs', 19, 2, frac_other_staples)
        birth_spacing_sum = baseline.loc['Birth spacing'][0:4].sum().values[0]
        baseline.loc['Birth spacing'].loc['Total (must be 100%)'] = birth_spacing_sum
        self.calcscache.write_cell('Baseline year population inputs', 32, 2, birth_spacing_sum)
        outcome_sum = baseline.loc['Birth outcome distribution'][0:3].sum().values[0]
        baseline.loc['Birth outcome distribution'].loc['Term AGA'] = 1.0 - outcome_sum
        self.calcscache.write_cell('Baseline year population inputs', 47, 2, 1.0 - outcome_sum)

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

        # Load the main spreadsheet into a DataFrame (slightly different format).
        # fix ages for PW
        baseline = utils.read_sheet(self.spreadsheet, 'Baseline year population inputs', [0])

        for row in baseline.loc['Age distribution of pregnant women'].iterrows():
            self.pw_agedist.append(row[1]['Data'])
        return None

    def get_proj(self):
        # Load the main spreadsheet into a DataFrame.
        # drops rows with any na
        proj = utils.read_sheet(self.spreadsheet, 'Demographic projections', cols=[0], dropna='any')

        # Read in the Baseline spreadsheet information we'll need.
        baseline = utils.read_sheet(self.spreadsheet, 'Baseline year population inputs', [0, 1])
        stillbirth = baseline.loc['Mortality'].loc['Stillbirths (per 1,000 total births)'].values[0]
        abortion = baseline.loc['Mortality'].loc['Fraction of pregnancies ending in spontaneous abortion'].values[0]

        # Recalculate cells that need it, and remember in the calculations cache.
        total_wra = proj.loc[:, ['WRA: 15-19 years', 'WRA: 20-29 years', 'WRA: 30-39 years',
            'WRA: 40-49 years']].sum(axis=1).values
        proj.loc[:, 'Total WRA'] = total_wra
        self.calcscache.write_col('Demographic projections', 1, 6, total_wra)
        numbirths = proj.loc[:, 'Number of births'].values
        estpregwomen = (numbirths + numbirths * stillbirth / (1000.0 - stillbirth)) / (1.0 - abortion)
        proj.loc[:, 'Estimated pregnant women'] = estpregwomen
        self.calcscache.write_col('Demographic projections', 1, 7, estpregwomen)
        nonpregwra = total_wra - estpregwomen
        proj.loc[:, 'non-pregnant WRA'] = nonpregwra
        self.calcscache.write_col('Demographic projections', 1, 8, nonpregwra)

        # dict of lists to support indexing
        for column in proj:
            self.proj[column] = proj[column].tolist()
        # wra pop projections list in increasing age order
        for age in self.settings.wra_ages:
            self.wra_proj.append(proj[age].tolist())

    def get_risk_dist(self):
        # Load the main spreadsheet into a DataFrame.
        dist = utils.read_sheet(self.spreadsheet, 'Nutritional status distribution', [0, 1])

        # Recalculate cells that need it, and remember in the calculations cache.
        stunting_mod_hi_sums = dist.loc['Stunting (height-for-age)'].iloc[2:4, 0:5].astype(np.float).sum().values
        stunting_invs = norm.ppf(stunting_mod_hi_sums, 0.0, 1.0)
        stunting_norm_pcts = np.ones(5) - norm.cdf(stunting_invs + np.ones(5), 0.0, 1.0)
        cols = dist.columns[0:5]
        dist.loc[('Stunting (height-for-age)', 'Normal (HAZ-score > -1)'), cols] = stunting_norm_pcts
        self.calcscache.write_row('Nutritional status distribution', 1, 2, stunting_norm_pcts)
        stunting_mild_pcts = norm.cdf(stunting_invs + np.ones(5), 0.0, 1.0) - stunting_mod_hi_sums
        dist.loc[('Stunting (height-for-age)', 'Mild (HAZ-score between -2 and -1)'), cols] = stunting_mild_pcts
        self.calcscache.write_row('Nutritional status distribution', 2, 2, stunting_mild_pcts)
        wasting_mod_hi_sums = dist.loc['Wasting (weight-for-height)'].iloc[2:4, 0:5].astype(np.float).sum().values
        wasting_invs = norm.ppf(wasting_mod_hi_sums, 0.0, 1.0)
        wasting_norm_pcts = np.ones(5) - norm.cdf(wasting_invs + np.ones(5), 0.0, 1.0)
        dist.loc[('Wasting (weight-for-height)', 'Normal  (WHZ-score > -1)'), cols] = wasting_norm_pcts
        self.calcscache.write_row('Nutritional status distribution', 7, 2, wasting_norm_pcts)
        wasting_mild_pcts = norm.cdf(wasting_invs + np.ones(5), 0.0, 1.0) - wasting_mod_hi_sums
        dist.loc[('Wasting (weight-for-height)', 'Mild  (WHZ-score between -2 and -1)'), cols] = wasting_mild_pcts
        self.calcscache.write_row('Nutritional status distribution', 8, 2, wasting_mild_pcts)

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

        # Load the main spreadsheet into a DataFrame, but skipping 12 rows.
        # get anaemia
        dist = utils.read_sheet(self.spreadsheet, 'Nutritional status distribution', [0, 1], skiprows=12)

        self.risk_dist['Anaemia'] = sc.odict()

        # Recalculate cells that need it, and remember in the calculations cache.
        all_anaem = dist.loc['Anaemia', 'Prevalence of anaemia'].to_dict()
        baseline = utils.read_sheet(self.spreadsheet, 'Baseline year population inputs')
        index = np.array(baseline['Field']).tolist().index('Percentage of anaemia that is iron deficient')
        iron_pct = np.array(baseline['Data'])[index]
        anaem = dist.loc['Anaemia', 'Prevalence of anaemia'] * iron_pct
        self.calcscache.write_row('Nutritional status distribution', 14, 2, anaem.values)

        # These should work, but don't in Google Cloud.
        # anaem = sc.odict({key: val * iron_pct for key, val in all_anaem.items()})
        # self.calcscache.write_row('Nutritional status distribution', 14, 2, anaem[:])

        # for age, prev in anaem.items():  # Should work with commented out code above
        for age, prev in anaem.iteritems():
            self.risk_dist['Anaemia'][age] = dict()
            self.risk_dist['Anaemia'][age]['Anaemic'] = prev
            self.risk_dist['Anaemia'][age]['Not anaemic'] = 1.-prev

        # Load the main spreadsheet into a DataFrame.
        # get breastfeeding dist
        dist = utils.read_sheet(self.spreadsheet, 'Breastfeeding distribution', [0, 1])

        # Recalculate cells that need it, and remember in the calculations cache.
        calc_cells = 1.0 - dist.loc['Breastfeeding'].iloc[0:3].sum().values
        self.calcscache.write_row('Breastfeeding distribution', 4, 2, calc_cells)
        dist.loc[('Breastfeeding', 'None'), :] = calc_cells

        self.risk_dist['Breastfeeding'] = dist.loc['Breastfeeding'].to_dict()

    def get_time_trends(self):
        # Load the main spreadsheet into a DataFrame.
        trends = utils.read_sheet(self.spreadsheet, 'Time trends', cols=[0,1], dropna=False)

        self.time_trends['Stunting'] = trends.loc['Stunting prevalence (%)'].loc['Children 0-59 months'].values.tolist()[:1]
        self.time_trends['Wasting'] = trends.loc['Wasting prevalence (%)'].loc['Children 0-59 months'].values.tolist()[:1]
        self.time_trends['Anaemia'] = trends.loc['Anaemia prevalence (%)'].values.tolist()[:3] # order is (children, PW, WRA)
        self.time_trends['Breastfeeding'] = trends.loc['Prevalence of age-appropriate breastfeeding'].values.tolist()[:2] # 0-5 months, 6-23 months
        self.time_trends['Mortality'] = trends.loc['Mortality'].values.tolist() # under 5, maternal
    
    def get_economic_cost(self):
        econo_cost = utils.read_sheet(self.spreadsheet, 'Economic loss', cols=[0], dropna=False)
        self.cost_wasting = econo_cost.loc['Wasting'].values[0]
        self.cost_stunting = econo_cost.loc['Stunting'].values[0]
        self.cost_child_death = econo_cost.loc['Child death'].values[0]
        self.cost_pw_death = econo_cost.loc['PW death'].values[0]
        self.cost_child_anaemic = econo_cost.loc['Child anaemic'].values[0]
        self.cost_pw_anaemic = econo_cost.loc['PW anaemic'].values[0]
        
    def get_incidences(self):
        # Load the main spreadsheet into a DataFrame.
        incidences = utils.read_sheet(self.spreadsheet, 'Incidence of conditions', [0])

        # Recalculate cells that need it, and remember in the calculations cache.
        baseline = utils.read_sheet(self.spreadsheet, 'Baseline year population inputs', [0, 1])
        diarr_incid = baseline.loc['Diarrhoea incidence']['Data'].values
        incidences.loc['Diarrhoea', :] = diarr_incid
        self.calcscache.write_row('Incidence of conditions', 1, 1, diarr_incid)
        dist = utils.read_sheet(self.spreadsheet, 'Nutritional status distribution', [0, 1])
        mam_incid = dist.loc['Wasting (weight-for-height)'].loc['MAM   (WHZ-score between -3 and -2)'][0:5].values.astype(np.float) * 2.6
        sam_incid = dist.loc['Wasting (weight-for-height)'].loc['SAM   (WHZ-score < -3)'][0:5].values.astype(np.float) * 2.6
        incidences.loc['MAM', :] = mam_incid
        self.calcscache.write_row('Incidence of conditions', 2, 1, mam_incid)
        incidences.loc['SAM', :] = sam_incid
        self.calcscache.write_row('Incidence of conditions', 3, 1, sam_incid)

        self.incidences = incidences.to_dict()

    ### MORTALITY ###

    def get_death_dist(self):
        # Load the main spreadsheet into a DataFrame.
        deathdist = utils.read_sheet(self.spreadsheet, 'Causes of death', [0, 1], skiprows=1)

        # Recalculate cells that need it, and remember in the calculations cache.
        neonatal_death_pct_sum = deathdist.loc['Neonatal']['<1 month'].values[:-1].astype(np.float).sum()
        self.calcscache.write_cell('Causes of death', 10, 2, neonatal_death_pct_sum)
        children_death_pct_sums = deathdist.loc['Children'].iloc[1:-1, 0:4].astype(np.float).sum().values
        self.calcscache.write_row('Causes of death', 22, 2, children_death_pct_sums)
        pregwomen_death_pct_sum = deathdist.loc['Pregnant women'].iloc[1:-1, 0].values.astype(np.float).sum()
        self.calcscache.write_cell('Causes of death', 34, 2, pregwomen_death_pct_sum)

        neonates = deathdist.loc['Neonatal'].iloc[:-1]

        # Load the main spreadsheet into a DataFrame, but skip 12 rows.
        deathdist = utils.read_sheet(self.spreadsheet, 'Causes of death', [0, 1], skiprows=12)

        children = deathdist.loc['Children'].iloc[:-1]

        # Load the main spreadsheet into a DataFrame, but skip 24 rows.
        deathdist = utils.read_sheet(self.spreadsheet, 'Causes of death', [0, 1], skiprows=24)

        pw = deathdist.loc['Pregnant women'].iloc[:-1]
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
    def __init__(self, data, default_data, calcscache):
        self.settings = settings.Settings()
        self.spreadsheet = data
        self.prog_set = []
        self.base_prog_set = []
        self.base_cov = []
        self.ref_progs = []
        self.sat = None
        self.max_inc = None
        self.max_dec = None
        self.costs = None
        self.costtype = None
        self.prog_deps = None
        self.prog_target = None
        self.famplan_methods = None
        self.impacted_pop = default_data.impacted_pop
        self.prog_areas = default_data.prog_areas
        self.calcscache = calcscache

        # load data
        self.get_prog_info()
        self.get_prog_target()
        self.get_prog_deps()
        self.get_ref_progs()
        self.get_famplan_methods()
        self.create_iycf()
        self.recalc_treatsam_prog_costs()
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
            max_inc = self.max_inc[progname]
            if max_inc < 0 or max_inc > 1:
                errormsg = 'Maximum increase is outside the interval (0, 100) for %s' %progname
                invalid.append(errormsg)
            max_dec = self.max_dec[progname]
            if max_dec < 0 or max_dec > 1:
                errormsg = 'Maximum decrease is outside the interval (0, 100) for %s' %progname
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
        # Load the main spreadsheet into a DataFrame.
        targetPopSheet = utils.read_sheet(self.spreadsheet, 'Programs target population', [0, 1])

        # Recalculate cells that need it, and remember in the calculations cache.
        baseline = utils.read_sheet(self.spreadsheet, 'Baseline year population inputs', [0, 1])
        food_insecure = baseline.loc['Population data'].loc['Percentage of population food insecure (default poor)'].values[0]
        frac_malaria_risk = baseline.loc['Population data'].loc['Percentage of population at risk of malaria'].values[0]
        school_attendance = baseline.loc['Population data'].loc['School attendance (percentage of 15-19 year women)'].values[0]
        frac_PW_health_facility = baseline.loc['Population data'].loc['Percentage of pregnant women attending health facility'].values[0]
        frac_children_health_facility = baseline.loc['Population data'].loc['Percentage of children attending health facility'].values[0]
        famplan_unmet_need = baseline.loc['Population data'].loc['Unmet need for family planning'].values[0]
        frac_rice = baseline.loc['Food'].loc['Fraction eating rice as main staple food'].values[0]
        frac_wheat = baseline.loc['Food'].loc['Fraction eating wheat as main staple food'].values[0]
        frac_maize = baseline.loc['Food'].loc['Fraction eating maize as main staple food'].values[0]
        diarr_incid = baseline.loc['Diarrhoea incidence']['Data'].values
        if len(baseline.loc['Other risks'].values) < 4:
            print('Warning, the databook being read is out of date and does not include baseline prevalences of '
                  'eclampsia and pre-eclampsia so global averages will be used.')
            preeclampsia_prev = self.settings.global_eclampsia_prevalence['Pre-eclampsia']
            eclampsia_prev = self.settings.global_eclampsia_prevalence['Eclampsia']
        else:
            preeclampsia_prev = baseline.loc['Other risks'].loc['Prevalence of pre-eclampsia'].values[0]
            eclampsia_prev = baseline.loc['Other risks'].loc['Prevalence of eclampsia'].values[0]
        treatsam = self.spreadsheet.parse(sheet_name='Treatment of SAM')
        comm_deliv_raw = treatsam.iloc[1]['Add extension']
        comm_deliv = pandas.notnull(comm_deliv_raw)
        cash_transfers_row = food_insecure * np.ones(4)
        targetPopSheet.loc['Children', 'Cash transfers'].iloc[1:5] = cash_transfers_row
        self.calcscache.write_row('Programs target population', 1, 3, cash_transfers_row)
        lipid_row = food_insecure * np.ones(2)
        targetPopSheet.loc['Children', 'Lipid-based nutrition supplements'].iloc[2:4] = lipid_row
        self.calcscache.write_row('Programs target population', 4, 4, lipid_row)
        oral_rehyd_row = diarr_incid
        targetPopSheet.loc['Children', 'Oral rehydration salts'].iloc[0:5] = oral_rehyd_row
        self.calcscache.write_row('Programs target population', 6, 2, oral_rehyd_row)
        pub_prov_row = food_insecure * np.ones(2)
        targetPopSheet.loc['Children', 'Public provision of complementary foods'].iloc[2:4] = pub_prov_row
        self.calcscache.write_row('Programs target population', 7, 4, pub_prov_row)
        if comm_deliv:
            treat_SAM_val = 1.0
        else:
            treat_SAM_val = frac_children_health_facility
        treat_SAM_row = treat_SAM_val * np.ones(4)
        targetPopSheet.loc['Children', 'Treatment of SAM'].iloc[1:5] = treat_SAM_row
        self.calcscache.write_row('Programs target population', 8, 3, treat_SAM_row)
        zinc_treatment_row = diarr_incid
        targetPopSheet.loc['Children', 'Zinc for treatment + ORS'].iloc[0:5] = zinc_treatment_row
        self.calcscache.write_row('Programs target population', 10, 2, zinc_treatment_row)
        balanced_energy_row = food_insecure * np.ones(4)
        targetPopSheet.loc['Pregnant women', 'Balanced energy-protein supplementation'].iloc[5:9] = balanced_energy_row
        self.calcscache.write_row('Programs target population', 13, 7, balanced_energy_row)
        IFAS_preg_health_row = frac_PW_health_facility * np.ones(4)
        targetPopSheet.loc['Pregnant women', 'IFAS for pregnant women (health facility)'].iloc[5:9] = IFAS_preg_health_row
        self.calcscache.write_row('Programs target population', 16, 7, IFAS_preg_health_row)
        IPTp_row = frac_malaria_risk * np.ones(4)
        targetPopSheet.loc['Pregnant women', 'IPTp'].iloc[5:9] = IPTp_row
        self.calcscache.write_row('Programs target population', 17, 7, IPTp_row)
        mg_eclampsia_row = eclampsia_prev * np.ones(4)
        targetPopSheet.loc['Pregnant women', 'Mg for eclampsia'].iloc[5:9] = mg_eclampsia_row
        self.calcscache.write_row('Programs target population', 18, 7, mg_eclampsia_row)
        mg_preeclampsia_row = preeclampsia_prev * np.ones(4)
        targetPopSheet.loc['Pregnant women', 'Mg for pre-eclampsia'].iloc[5:9] = mg_preeclampsia_row
        self.calcscache.write_row('Programs target population', 19, 7, mg_preeclampsia_row)
        fam_planning_row = famplan_unmet_need * np.ones(4)
        targetPopSheet.loc['Non-pregnant WRA', 'Family planning'].iloc[9:13] = fam_planning_row
        self.calcscache.write_row('Programs target population', 22, 11, fam_planning_row)
        IFAS_comm_row = np.ones(4)
        IFAS_comm_row[0] = (1.0 - food_insecure) * 0.49 * (1.0 - school_attendance) + food_insecure * 0.7 * (1.0 - school_attendance)
        IFAS_comm_row[1:] = (1.0 - food_insecure) * 0.49 + food_insecure * 0.7
        targetPopSheet.loc['Non-pregnant WRA', 'IFAS (community)'].iloc[9:13] = IFAS_comm_row
        self.calcscache.write_row('Programs target population', 23, 11, IFAS_comm_row)
        IFAS_health_fac_row = np.ones(4)
        IFAS_health_fac_row[0] = (1.0 - food_insecure) * 0.21 * (1.0 - school_attendance) + food_insecure * 0.3 * (1.0 - school_attendance)
        IFAS_health_fac_row[1:] = (1.0 - food_insecure) * 0.21 + food_insecure * 0.3
        targetPopSheet.loc['Non-pregnant WRA', 'IFAS (health facility)'].iloc[9:13] = IFAS_health_fac_row
        self.calcscache.write_row('Programs target population', 24, 11, IFAS_health_fac_row)
        IFAS_retailer_row = np.ones(4)
        IFAS_retailer_row[0] = (1.0 - food_insecure) * 0.3 * (1.0 - school_attendance)
        IFAS_retailer_row[1:] = (1.0 - food_insecure) * 0.3
        targetPopSheet.loc['Non-pregnant WRA', 'IFAS (retailer)'].iloc[9:13] = IFAS_retailer_row
        self.calcscache.write_row('Programs target population', 25, 11, IFAS_retailer_row)
        IFAS_school_row = (1.0 - food_insecure) * school_attendance + food_insecure * school_attendance
        targetPopSheet.loc['Non-pregnant WRA', 'IFAS (school)'].iloc[9] = IFAS_school_row
        self.calcscache.write_cell('Programs target population', 26, 11, IFAS_school_row)
        IFA_maize_row = frac_maize * np.ones(11)
        targetPopSheet.loc['General population', 'IFA fortification of maize'].iloc[2:13] = IFA_maize_row
        self.calcscache.write_row('Programs target population', 28, 4, IFA_maize_row)
        IFA_rice_row = frac_rice * np.ones(11)
        targetPopSheet.loc['General population', 'IFA fortification of rice'].iloc[2:13] = IFA_rice_row
        self.calcscache.write_row('Programs target population', 29, 4, IFA_rice_row)
        IFA_wheat_row = frac_wheat * np.ones(11)
        targetPopSheet.loc['General population', 'IFA fortification of wheat flour'].iloc[2:13] = IFA_wheat_row
        self.calcscache.write_row('Programs target population', 30, 4, IFA_wheat_row)
        bednet_row = frac_malaria_risk * np.ones(13)
        # targetPopSheet.loc['General population'].loc['Long-lasting insecticide-treated bednets'] = bednet_row
        targetPopSheet.loc[('General population', 'Long-lasting insecticide-treated bednets'), :] = bednet_row
        self.calcscache.write_row('Programs target population', 32, 2, bednet_row)

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
        # Load the main spreadsheet into a DataFrame.
        famplan_methods = utils.read_sheet(self.spreadsheet, 'Programs family planning', [0])

        # Recalculate cells that need it, and remember in the calculations cache.
        dist = famplan_methods.loc[:, 'Distribution'].values
        costs = famplan_methods.loc[:, 'Cost'].values
        prop_costs = dist * costs
        famplan_methods.loc[:, 'Proportional Cost'] = prop_costs
        self.calcscache.write_col('Programs family planning', 1, 4, prop_costs)

        self.famplan_methods = famplan_methods.to_dict('index')

    def get_prog_info(self):
        # Load the main spreadsheet into a DataFrame.
        sheet = utils.read_sheet(self.spreadsheet, 'Programs cost and coverage')

        self.base_prog_set = sheet.iloc[:,0].tolist()  # This grabs _all_ programs even those with zero unit cost.
        self.base_cov = sc.odict(zip(self.base_prog_set, sheet.iloc[:,1].tolist()))
        self.sat = sc.odict(zip(self.base_prog_set, sheet.iloc[:,2].tolist()))
        self.costs = sc.odict(zip(self.base_prog_set, sheet.iloc[:,3].tolist()))
        costtypes = utils.format_costtypes(sheet.iloc[:,4].tolist())
        self.costtype = sc.odict(zip(self.base_prog_set, costtypes))
        self.max_inc = sc.odict(zip(self.base_prog_set, sheet.iloc[:,5].tolist()))
        self.max_dec = sc.odict(zip(self.base_prog_set, sheet.iloc[:,6].tolist()))

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

    def recalc_treatsam_prog_costs(self):
        nutrition_status = utils.read_sheet(self.spreadsheet, 'Nutritional status distribution', [0, 1])
        sam_prev = []
        for s, span in enumerate(
                self.settings.child_age_spans):  # weight age group incidence/prevalence by size of group
            sam_prev.append(nutrition_status.values[7][s] * span)
        av_sam_prev = sum(sam_prev) / (sum(self.settings.child_age_spans))  # weighted average under 5 SAM prevalence
        self.costs['Treatment of SAM'] *= av_sam_prev * 2.6  # estimated ratio of incidence/prevalence
        return

    def get_iycf_target(self, package_modes):
        """ Creates the frac of pop targeted by each IYCF package.
        Note that frac in community and mass media assumed to be 1.
        Note also this fraction can exceed 1, and is adjusted for the target pop calculations of the Programs class """
        pop_data = self.spreadsheet.parse('Baseline year population inputs', index_col=[0,1]).loc['Population data']
        #frac_pw = float(pop_data.loc['Percentage of pregnant women attending health facility'])
       #frac_child = float(pop_data.loc['Percentage of children attending health facility'])
        frac_pw = pop_data.loc['Percentage of pregnant women attending health facility'][0]
        frac_child = pop_data.loc['Percentage of children attending health facility'][0]
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
    
    def __init__(self, country=None, region=None, name=None, demo_data=None, prog_data=None, default_params=None, uncertain_params=None,
                 pops=None, prog_info=None, doload=False, inputspath=None, defaultspath=None, fromfile=None, project=None):
        
        self.country = country
        self.region = region

        self.calcscache = CalcCellCache()
        
        self.demo_data = demo_data  # demo = demographic
        self.prog_data = prog_data
        self.default_params = default_params  # TODO: this should probably be phased out once the InputData and DefaultParams classes get merged
        self.uncertain_params = uncertain_params
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

        # Convert them to Pandas
        input_data     = inputsheet.pandas() 

        # If the 'Programs impacted population' worksheet is in input_data, then we are working with one of the newer
        # databooks, so pull the default data from input_data.
        if 'Programs impacted population' in input_data.sheet_names:
            default_data = input_data

        # Otherwise, pull the default data from the legacy spreadsheet.
        else:
            filename = settings.ONpath('nutrition') + 'legacy_default_params.xlsx'
            default_data = sc.Spreadsheet(filename=filename).pandas()
        
        # Read them into actual data
        try:
            self.demo_data = InputData(input_data, self.calcscache)  # demo_ here is demographic_
        except Exception as E:
            raise Exception('Error in databook: %s'%str(E))
        try:
            self.default_params = DefaultParamsDummy(default_data, input_data) # just debugging with dummy class called
            #self.default_params = DefaultParams(default_data, input_data) 
            self.default_params.compute_risks(self.demo_data)
            self.prog_data = ProgData(input_data, self.default_params, self.calcscache)
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

class UncertaintyParas(object):
    def __init__(self, default_data, input_data):
        self.settings = settings.Settings()
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
        self.treatsam = None
        self.manman = None
        self.bf_effects = None
        self.stunt_effects = None
        self.ors = None
        self.rr_space_bo = None
        self.rr_death_bo = None
        self.rr_st = None
        self.rr_ws = None
        self.rr_an = None
        self.rr_bf = None
        self.rr_diar = None
        self.stun_or = None
        self.wast_or = None
        self.ane_or = None
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
        self.set_pw_progs()
        self.set_child_progs()
        self.set_anaemia_progs()
        self.set_wasting_progs()
        self.set_bo_progs()
        self.set_iycf_effects()
        self.set_bo_risks()
        self.set_relative_risks()
        self.set_odds_ratios()
             
    # function to generate data matrix using unifrom distribution with lower and upper input of the each data cell
    def make_random(self, lb, ub):
        n = len(lb[0])
        m = len(lb[:,0])
        d=np.zeros([m, n])
        for i in range(0, m):
            for j in range(0, n):
                d[i][j] = np.random.uniform(lb[i][j], ub[i][j], 1)
        return d
    
    def set_pw_progs(self):
        pw_progs_lower = utils.read_sheet(self.spreadsheet, 'Programs for PW', [0,1,2], skiprows=[i for i in chain(range(1,10), range(16, 25))], to_odict=False).dropna(axis=1, how='all')
        pw_progs_upper = utils.read_sheet(self.spreadsheet, 'Programs for PW', [0,1,2], skiprows=[i for i in range(1,19)], to_odict=False).dropna(axis=1, how='all')
        self.pw_progs = self.make_random(pw_progs_lower.to_numpy(), pw_progs_upper.to_numpy())      
    
    def set_child_progs(self):
        child_progs_lower = utils.read_sheet(self.spreadsheet, 'Programs for children', [0,1,2], skiprows=[i for i in chain(range(1,52), range(100, 152))]).dropna(axis=1, how='all')
        child_progs_upper = utils.read_sheet(self.spreadsheet, 'Programs for children', [0,1,2], skiprows=[i for i in range(1,103)]).dropna(axis=1, how='all')
        self.child_progs = self.make_random(child_progs_lower.to_numpy(), child_progs_upper.to_numpy())
    
    def set_anaemia_progs(self):
        anaem_sheet_lower = utils.read_sheet(self.spreadsheet, 'Programs anemia', [0,1], skiprows=[i for i in chain(range(1,24), range(43, 66))]).dropna(axis=1, how='all')
        rr_anaem_prog_lower = anaem_sheet_lower.loc['Relative risks of anaemia when receiving intervention - lower'].dropna(axis=0, how='all')
        or_anaem_prog_lower = anaem_sheet_lower.loc['Odds ratios of being anaemic when covered by intervention - lower'].dropna(axis=0, how='all')
        anaem_sheet_upper = utils.read_sheet(self.spreadsheet, 'Programs anemia', [0,1], skiprows=[i for i in range(1,46)]).dropna(axis=1, how='all')
        rr_anaem_prog_upper = anaem_sheet_upper.loc['Relative risks of anaemia when receiving intervention - upper'].dropna(axis=0, how='all')
        or_anaem_prog_upper = anaem_sheet_upper.loc['Odds ratios of being anaemic when covered by intervention - upper'].dropna(axis=0, how='all')
        self.rr_anaem_prog = self.make_random(rr_anaem_prog_lower.to_numpy(), rr_anaem_prog_upper.to_numpy())
        self.or_anaem_prog = self.make_random(or_anaem_prog_lower.to_numpy(), or_anaem_prog_upper.to_numpy())
        
    def set_wasting_progs(self):
        wastingSheet_lower = utils.read_sheet(self.spreadsheet, 'Programs wasting', [0,1], skiprows=[i for i in chain(range(1,8), range(12, 19))]).dropna(axis=1, how='all')
        treatsam_lower = wastingSheet_lower.loc['Odds ratio of SAM when covered by program - lower'].dropna(axis=0, how='all')
        manman_lower = wastingSheet_lower.loc['Odds ratio of MAM when covered by program - lower'].dropna(axis=0, how='all')
        wastingSheet_upper = utils.read_sheet(self.spreadsheet, 'Programs wasting', [0,1], skiprows=[i for i in range(1,16)]).dropna(axis=1, how='all')
        treatsam_upper = wastingSheet_upper.loc['Odds ratio of SAM when covered by program - upper'].dropna(axis=0, how='all')
        manman_upper = wastingSheet_upper.loc['Odds ratio of MAM when covered by program - upper'].dropna(axis=0, how='all')
        self.treatsam = self.make_random(treatsam_lower.to_numpy(), treatsam_upper.to_numpy())
        self.manman = self.make_random(manman_lower.to_numpy(), manman_upper.to_numpy())
        
    def set_bo_progs(self):
        progs_lower = utils.read_sheet(self.spreadsheet, 'Programs birth outcomes', [0,1], skiprows=[i for i in chain(range(1,16), range(28, 43))]).dropna(axis=1, how='all')
        progs_upper = utils.read_sheet(self.spreadsheet, 'Programs birth outcomes', [0,1], skiprows=[i for i in range(1,31)]).dropna(axis=1, how='all')
        self.bo_progs = self.make_random(progs_lower.to_numpy(), progs_upper.to_numpy()) # use prog[:] = UncertaintyParas.bo_progs in the DefaultParas class to replace
        
    def set_iycf_effects(self):
        effects_lower = utils.read_sheet(self.spreadsheet, 'IYCF odds ratios', [0,1,2], skiprows=[i for i in chain(range(1,54), range(104, 157))]).dropna(axis=1, how='all')
        bf_effects_lower = effects_lower.loc['Odds ratio for correct breastfeeding - lower'].dropna(axis=0, how='all')
        stunt_effects_lower = effects_lower.loc['Odds ratio for stunting - lower'].dropna(axis=0, how='all')
        effects_upper = utils.read_sheet(self.spreadsheet, 'IYCF odds ratios', [0,1,2], skiprows=[i for i in range(1,107)]).dropna(axis=1, how='all')
        bf_effects_upper = effects_upper.loc['Odds ratio for correct breastfeeding - upper'].dropna(axis=0, how='all')
        stunt_effects_upper = effects_upper.loc['Odds ratio for stunting - upper'].dropna(axis=0, how='all')
        self.bf_effects = self.make_random(bf_effects_lower.to_numpy(), bf_effects_upper.to_numpy())
        self.stunt_effects = self.make_random(stunt_effects_lower.to_numpy(), stunt_effects_upper.to_numpy())
        
    def set_bo_risks(self):
        bo_sheet_lower = utils.read_sheet(self.spreadsheet, 'Birth outcome risks', [0,1], skiprows=[i for i in chain(range(0,28), range(52, 79))]).dropna(axis=1, how='all')
        ors_lower = bo_sheet_lower.loc['Odds ratios for conditions - lower']
        bo_sheet_upper = utils.read_sheet(self.spreadsheet, 'Birth outcome risks', [0,1], skiprows=[i for i in range(0,55)]).dropna(axis=1, how='all')
        ors_upper = bo_sheet_upper.loc['Odds ratios for conditions - upper'].dropna(axis=0, how='all')
        rr_space_bo_lower = bo_sheet_lower.loc['Relative risk by birth spacing - lower'].dropna(axis=0, how='all')
        rr_death_bo_lower = bo_sheet_lower.loc['Relative risks of neonatal causes of death - lower'].dropna(axis=0, how='all')
        rr_space_bo_upper = bo_sheet_upper.loc['Relative risk by birth spacing - upper'].dropna(axis=0, how='all')
        rr_death_bo_upper = bo_sheet_upper.loc['Relative risks of neonatal causes of death - upper'].dropna(axis=0, how='all')
        self.ors = self.make_random(ors_lower.to_numpy(), ors_upper.to_numpy())
        self.rr_space_bo = self.make_random(rr_space_bo_lower.to_numpy(), rr_space_bo_upper.to_numpy())
        self.rr_death_bo = self.make_random(rr_death_bo_lower.to_numpy(), rr_death_bo_upper.to_numpy())
        
    def set_relative_risks(self):
        #lower values
        #stunting
        rr_st_sheet_lower = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=[i for i in chain(range(0,111), range(136, 328))]).dropna(axis=1, how='all')
        rr_st_lower = rr_st_sheet_lower.loc['Stunting']
        # wasting
        rr_ws_sheet_lower = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=[i for i in chain(range(0,138), range(163, 328))]).dropna(axis=1, how='all')
        rr_ws_lower = rr_ws_sheet_lower.loc['Wasting']
        # anaemia
        rr_an_sheet_lower = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2],  skiprows=[i for i in chain(range(0,165), range(172, 328))]).dropna(axis=1, how='all')
        rr_an_lower = rr_an_sheet_lower.loc['Anaemia']
        # breastfeeding
        rr_bf_sheet_lower = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=[i for i in chain(range(0,174), range(211, 328))]).dropna(axis=1, how='all')
        rr_bf_lower = rr_bf_sheet_lower.loc['Breastfeeding']
        # diarrhoea
        rr_diar_sheet_lower = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=[i for i in chain(range(0,213), range(218, 328))]).dropna(axis=1, how='all')
        rr_diar_lower = rr_diar_sheet_lower.loc['Diarrhoea']  
        # upper values
        # stunting
        rr_st_sheet_upper = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=[i for i in chain(range(0,221), range(246, 328))]).dropna(axis=1, how='all')
        rr_st_upper = rr_st_sheet_upper.loc['Stunting']
        # wasting
        rr_ws_sheet_upper = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=[i for i in chain(range(0,248), range(273, 328))]).dropna(axis=1, how='all')
        rr_ws_upper = rr_ws_sheet_upper.loc['Wasting']
        # anaemia
        rr_an_sheet_upper = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=[i for i in chain(range(0,275), range(282, 328))]).dropna(axis=1, how='all')
        rr_an_upper = rr_an_sheet_upper.loc['Anaemia']
        # breastfeeding
        rr_bf_sheet_upper = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=[i for i in chain(range(0,284), range(321, 328))]).dropna(axis=1, how='all')
        rr_bf_upper = rr_bf_sheet_upper.loc['Breastfeeding']
        # diarrhoea
        rr_diar_sheet_upper = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=[i for i in range(0,323)]).dropna(axis=1, how='all')
        rr_diar_upper = rr_diar_sheet_upper.loc['Diarrhoea']
        # converting to random values
        self.rr_st = self.make_random(rr_st_lower.to_numpy(), rr_st_upper.to_numpy()) # stunting
        self.rr_ws = self.make_random(rr_ws_lower.to_numpy(), rr_ws_upper.to_numpy()) # wasting
        self.rr_an = self.make_random(rr_an_lower.to_numpy(), rr_an_upper.to_numpy()) # anaemia
        self.rr_bf = self.make_random(rr_bf_lower.to_numpy(), rr_bf_upper.to_numpy()) # breastfeeding
        self.rr_diar = self.make_random(rr_diar_lower.to_numpy(), rr_diar_upper.to_numpy()) # diarrhoea
        
    def set_odds_ratios(self):
        or_sheet_cond_lower = utils.read_sheet(self.spreadsheet, 'Odds ratios', [0,1], skiprows=[i for i in chain(range(0,23), range(38, 64))]).dropna(axis=1, how='all')
        or_sheet_cond_upper = utils.read_sheet(self.spreadsheet, 'Odds ratios', [0,1], skiprows=[i for i in chain(range(0,45), range(60, 64))]).dropna(axis=1, how='all')
        or_sheet_space_lower = utils.read_sheet(self.spreadsheet, 'Odds ratios', [0,1], skiprows=[i for i in chain(range(0,40), range(42, 64))]).dropna(axis=1, how='all')
        or_sheet_space_upper = utils.read_sheet(self.spreadsheet, 'Odds ratios', [0,1], skiprows=[i for i in range(0,62)]).dropna(axis=1, how='all')
        stun_or_lower = or_sheet_cond_lower.loc['Condition'].fillna(0)
        stun_or_upper = or_sheet_cond_upper.loc['Condition'].fillna(0)
        self.stun_or = self.make_random(stun_or_lower.to_numpy(), stun_or_upper.to_numpy()) # for stunting
        wast_or_lower = or_sheet_cond_lower.loc['Wasting']
        wast_or_upper = or_sheet_cond_upper.loc['Wasting']
        self.wast_or = self.make_random(wast_or_lower.to_numpy(), wast_or_upper.to_numpy()) # for wasting
        ane_or_lower = or_sheet_cond_lower.loc['Anaemia']
        ane_or_upper = or_sheet_cond_upper.loc['Anaemia']
        self.ane_or = self.make_random(ane_or_lower.to_numpy(), ane_or_upper.to_numpy()) # for anaemia
        or_stunting_prog_lower = or_sheet_cond_lower.loc['By program - lower'].dropna(axis=0, how='all')
        or_bf_prog_lower = or_sheet_cond_lower.loc['Odds ratios for correct breastfeeding by program - lower'].dropna(axis=0, how='all')
        or_stunting_prog_upper = or_sheet_cond_upper.loc['By program - upper'].dropna(axis=0, how='all')
        or_bf_prog_upper = or_sheet_cond_upper.loc['Odds ratios for correct breastfeeding by program - upper'].dropna(axis=0, how='all')
        self.or_stunting_prog = self.make_random(or_stunting_prog_lower.to_numpy(), or_stunting_prog_upper.to_numpy()) # stunting programs
        self.or_bf_prog = self.make_random(or_bf_prog_lower.to_numpy(), or_bf_prog_upper.to_numpy()) # breastfeeding programs
        or_space_prog_lower = or_sheet_space_lower.loc['Odds ratios for optimal birth spacing by program - lower']
        or_space_prog_upper = or_sheet_space_upper.loc['Odds ratios for optimal birth spacing by program - upper']
        self.or_space_prog = self.make_random(or_space_prog_lower.to_numpy(), or_space_prog_upper.to_numpy()) # birth spacing programs
        
#### IMPORTANT ####
# The following is a dummy class that should be renamed to "DefaultParams" once correctly implemented.
# This reads original data from the data book (to read and establish index names in DFs) and also call random data from UncertaintyParas class, next input them to model.
    
class DefaultParamsDummy(object):
    def __init__(self, default_data, input_data):
        self.settings = settings.Settings()
        self.uncert = UncertaintyParas(default_data, input_data)
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
        rr_sheet = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=[i for i in chain(range(0,1), range(26, 328))]).dropna(axis=1, how='all')
        rr_orig = rr_sheet.loc['Stunting']
        rr = self.data_replace(rr_orig, self.uncert.rr_st).to_dict()
        self.rr_death['Stunting'] = self.make_dict2(rr)
        # wasting
        rr_sheet = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=[i for i in chain(range(0,28), range(53, 328))]).dropna(axis=1, how='all')
        rr_orig = rr_sheet.loc['Wasting']
        rr = self.data_replace(rr_orig, self.uncert.rr_ws).to_dict()
        self.rr_death['Wasting'] = self.make_dict2(rr)
        # anaemia
        rr_sheet = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=[i for i in chain(range(0,55), range(62, 328))]).dropna(axis=1, how='all')
        rr_orig = rr_sheet.loc['Anaemia']
        rr = self.data_replace(rr_orig, self.uncert.rr_an).to_dict()
        self.rr_death['Anaemia'] = self.make_dict2(rr)
        # currently no impact on mortality for anaemia
        self.rr_death['Anaemia'].update({age:{cat:{'Diarrhoea':1} for cat in self.settings.anaemia_list} for age in self.settings.child_ages})
        # breastfeeding
        rr_sheet = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=[i for i in chain(range(0,64), range(101, 328))]).dropna(axis=1, how='all')
        rr_orig = rr_sheet.loc['Breastfeeding']
        rr = self.data_replace(rr_orig, self.uncert.rr_bf).to_dict()
        self.rr_death['Breastfeeding'] = self.make_dict2(rr)
        # diarrhoea
        rr_sheet = utils.read_sheet(self.spreadsheet, 'Relative risks', [0,1,2], skiprows=[i for i in chain(range(0,103), range(108, 328))]).dropna(axis=1, how='all')
        rr_orig = rr_sheet.loc['Diarrhoea']
        rr = self.data_replace(rr_orig, self.uncert.rr_diar).to_dict()
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
        or_sheet = utils.read_sheet(self.spreadsheet, 'Odds ratios', [0,1], skiprows=[i for i in chain(range(0,1), range(16, 64))]).dropna(axis=1, how='all')
        this_or_orig = or_sheet.loc['Condition']
        this_or = self.data_replace(this_or_orig, self.uncert.stun_or).to_dict('index')
        self.or_cond['Stunting'] = sc.odict()
        self.or_cond['Stunting']['Prev stunting'] = this_or['Given previous stunting (HAZ < -2 in previous age band)']
        self.or_cond['Stunting']['Diarrhoea'] = this_or['Diarrhoea (per additional episode)']
        wasting_or_orig = or_sheet.loc['Wasting']
        wasting_or = self.data_replace(wasting_or_orig, self.uncert.wast_or)
        self.or_cond['SAM'] = sc.odict()
        self.or_cond['SAM']['Diarrhoea'] = wasting_or.to_dict('index')['For SAM per additional episode of diarrhoea']
        self.or_cond['MAM'] = sc.odict()
        self.or_cond['MAM']['Diarrhoea'] = wasting_or.to_dict('index')['For MAM per additional episode of diarrhoea']
        anem_or_orig = or_sheet.loc['Anaemia']
        anem_or = self.data_replace(anem_or_orig, self.uncert.ane_or)
        self.or_cond['Anaemia'] = sc.odict()
        self.or_cond['Anaemia']['Severe diarrhoea'] = sc.odict()
        self.or_cond['Anaemia']['Severe diarrhoea'] = anem_or.to_dict('index')['For anaemia per additional episode of severe diarrhoea']
        or_stunting_prog_orig = or_sheet.loc['By program'].dropna(axis=0, how='all')
        self.or_stunting_prog = self.data_replace(or_stunting_prog_orig, self.uncert.or_stunting_prog).to_dict('index')
        or_bf_prog_orig = or_sheet.loc['Odds ratios for correct breastfeeding by program'].dropna(axis=0, how='all')
        self.or_bf_prog = self.data_replace(or_bf_prog_orig, self.uncert.or_bf_prog).to_dict('index')
        or_sheet_space = utils.read_sheet(self.spreadsheet, 'Odds ratios', [0,1], skiprows=[i for i in chain(range(0,18), range(20, 64))]).dropna(axis=1, how='all')
        or_space_prog_orig = or_sheet_space.loc['Odds ratios for optimal birth spacing by program']
        self.or_space_prog = self.data_replace(or_space_prog_orig, self.uncert.or_space_prog).to_dict('index')

    def get_bo_progs(self):
        progs_orig = utils.read_sheet(self.spreadsheet, 'Programs birth outcomes', [0,1], skiprows=[i for i in range(13,43)]).dropna(axis=1, how='all')
        progs = self.data_replace(progs_orig, self.uncert.bo_progs).to_dict('index')
        newprogs = sc.odict()
        for program in progs.keys():
            if not newprogs.get(program[0]):
                newprogs[program[0]] = sc.odict()
            newprogs[program[0]][program[1]] = progs[program]
        self.bo_progs = newprogs

    def anaemia_progs(self):
        anaem_sheet = utils.read_sheet(self.spreadsheet, 'Programs anemia', [0,1], skiprows=[i for i in range(22,66)]).dropna(axis=1, how='all')
        rr_anaem_prog = anaem_sheet.loc['Relative risks of anaemia when receiving intervention'].dropna(axis=0, how='all')
        self.rr_anaem_prog = self.data_replace(rr_anaem_prog, self.uncert.rr_anaem_prog).to_dict(orient='index')
        or_anaem_prog = anaem_sheet.loc['Odds ratios of being anaemic when covered by intervention'].dropna(axis=0, how='all')
        self.or_anaem_prog = self.data_replace(or_anaem_prog, self.uncert.or_anaem_prog).to_dict(orient='index')

    def wasting_progs(self):
        wastingSheet = utils.read_sheet(self.spreadsheet, 'Programs wasting', [0,1], skiprows=[i for i in range(5,19)]).dropna(axis=1, how='all')
        treatsam_orig = wastingSheet.loc['Odds ratio of SAM when covered by program'].dropna(axis=0, how='all')
        manman_orig = wastingSheet.loc['Odds ratio of MAM when covered by program'].dropna(axis=0, how='all')
        treatsam = self.data_replace(treatsam_orig, self.uncert.treatsam).to_dict(orient='index')
        manman = self.data_replace(manman_orig, self.uncert.manman).to_dict(orient='index')
        self.or_wasting_prog['SAM'] = treatsam
        if self.man_mam:
            self.or_wasting_prog['MAM'] = {'Treatment of SAM': manman['Management of MAM'] }

    def get_child_progs(self):
        child_progs_orig = utils.read_sheet(self.spreadsheet, 'Programs for children', [0,1,2], skiprows=[i for i in range(49,151)]).dropna(axis=1, how='all')
        self.child_progs = self.data_replace(child_progs_orig, self.uncert.child_progs).to_dict()

    def get_pw_progs(self):
        pw_progs_orig = utils.read_sheet(self.spreadsheet, 'Programs for PW', [0,1,2], skiprows=[i for i in range(7,25)]).dropna(axis=1, how='all')
        self.pw_progs = self.data_replace(pw_progs_orig, self.uncert.pw_progs).to_dict()
        
    def get_bo_risks(self):
        bo_sheet = utils.read_sheet(self.spreadsheet, 'Birth outcome risks', [0,1], skiprows=[i for i in chain(range(25,81), range(0,1))]).dropna(axis=1, how='all')
        ors_orig = bo_sheet.loc['Odds ratios for conditions'].dropna(axis=0, how='all')
        ors = self.data_replace(ors_orig, self.uncert.ors).to_dict('index')
        self.or_cond_bo['Stunting'] = ors['Stunting (HAZ-score < -2)']
        self.or_cond_bo['MAM'] = ors['MAM (WHZ-score between -3 and -2)']
        self.or_cond_bo['SAM'] = ors['SAM (WHZ-score < -3)']
        rr_space_bo_orig = bo_sheet.loc['Relative risk by birth spacing'].dropna(axis=0, how='all')
        self.rr_space_bo = self.data_replace(rr_space_bo_orig, self.uncert.rr_space_bo).to_dict('index')
        rr_death_orig = bo_sheet.loc['Relative risks of neonatal causes of death'].dropna(axis=0, how='all')
        self.rr_death['Birth outcomes'] = self.data_replace(rr_death_orig, self.uncert.rr_death_bo).to_dict()
        
    def get_iycf_effects(self, iycf_packs):
        # TODO: need something that catches if iycf packages not included at all.
        effects = utils.read_sheet(self.spreadsheet, 'IYCF odds ratios', [0,1,2], skiprows=[i for i in range(51,157)]).dropna(axis=1, how='all')
        bf_effects_orig = effects.loc['Odds ratio for correct breastfeeding'].dropna(axis=0, how='all')
        stunt_effects_orig = effects.loc['Odds ratio for stunting'].dropna(axis=0, how='all')
        bf_effects = self.data_replace(bf_effects_orig, self.uncert.bf_effects)
        stunt_effects = self.data_replace(stunt_effects_orig, self.uncert.stunt_effects)
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
    
    """replacing original data by randomly tranformed data"""
    def data_replace(self, orig, transformed):
        outdata = sc.dcp(orig)
        outdata.loc[:,:] = transformed
        return outdata