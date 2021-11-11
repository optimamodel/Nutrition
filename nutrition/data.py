import numpy as np
from scipy.stats import norm
import pandas
import sciris as sc
import re
from . import settings, populations, utils, programs
from .migration import migrate
from .utils import translate

def get_databook_locale(workbook):
    locale = "en"  # Default language
    if workbook.properties.keywords:
        for item in workbook.properties.keywords.split(","):
            item = item.strip().split("=")
            if item[0] == "lang":
                locale = item[1]
                break
    return locale

# This class is used to define an object which keeps a cache of all cells from the Excel databook/s that need to be
# calculated.  This cache used by RPC code that figures out what calculation values to send to the FE to be displayed
# in the grey non-editable cells in the GUI.
class CalcCellCache(object):
    def __init__(self):
        self.cachedict = sc.odict()

    # From the key string value, pull out the spreadsheet name, and row and col numbers (0-indexed).
    def _key_to_indices(self, keyval):
        sheetname = re.sub(":.*$", "", keyval)
        droptocolon = re.sub(".*:\[", "", keyval)
        dropcommatoend = re.sub(",.*$", "", droptocolon)
        rownum = int(dropcommatoend)
        droptocomma = re.sub(".*,", "", keyval)
        dropendbracket = re.sub("\]", "", droptocomma)
        colnum = int(dropendbracket)
        return (sheetname, rownum, colnum)

    # Write a single value to the cache.
    def write_cell(self, worksheet_name, row, col, val):
        cell_key = "%s:[%d,%d]" % (worksheet_name, row, col)
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
        cell_key = "%s:[%d,%d]" % (worksheet_name, row, col)
        if cell_key in self.cachedict:
            return self.cachedict[cell_key]
        else:
            print("ERROR: Sheet: %s, Row: %d, Col: %d is not in cache!" % (worksheet_name, row, col))
            return 0.0

    # Do a dump of the whole cache.
    def show(self):
        print(self.cachedict)

    # Check a value in the calculations cache against the cached value actually in the spreadsheet.
    def check_cell_against_worksheet_value(self, wb, worksheet_name, row, col):
        calc_val = self.read_cell(worksheet_name, row, col)
        wsheet_val = wb.readcells(method="openpyexcel", wbargs={"data_only": True}, sheetname=worksheet_name, cells=[[row, col]])[0]
        if sc.approx(calc_val, wsheet_val):
            print("Sheet: %s, Row: %d, Col: %d -- match" % (worksheet_name, row, col))
        else:
            print("Sheet: %s, Row: %d, Col: %d -- MISMATCH" % (worksheet_name, row, col))
            print("-- calc cache value")
            print(calc_val)
            print("-- spreadsheet cached value")
            print(wsheet_val)

    # For all items in the calculations cache, check whether they match with what's in the spreadsheet.
    def check_all_cells_against_worksheet_values(self, wb):
        print("Calculations cache check against spreadsheet:")
        for key in self.cachedict.keys():  # TODO -- move worksheet load outside loop so don't have to reload for every cell
            (sheetname, rownum, colnum) = self._key_to_indices(key)
            self.check_cell_against_worksheet_value(wb, sheetname, rownum, colnum)


# TODO (possible): we may want to merge this class with InputData to make another class (DatabookData).
class DefaultParams(object):
    def __init__(self, default_data, input_data):
        self.locale = get_databook_locale(default_data.book)
        assert get_databook_locale(default_data.book) == self.locale, 'Default data and input data locales do not match'

        self.settings = settings.Settings(self.locale)
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
        output = sc.prepr(self)
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

    @translate
    def extend_treatsam(self):
        treatsam = self.input_data.parse(sheet_name=_("Treatment of SAM"))
        add_man = treatsam.iloc[0][_("Add extension")]
        if pandas.notnull(add_man):
            self.man_mam = True

    @translate
    def impact_pop(self):
        sheet = utils.read_sheet(self.spreadsheet, _("Programs impacted population"), [0, 1])
        impacted = sc.odict()
        for pop in [_("Children"), _("Pregnant women"), _("Non-pregnant WRA"), _("General population")]:
            impacted.update(sheet.loc[pop].to_dict(orient="index"))
        self.impacted_pop = impacted

    @translate
    def prog_risks(self):
        areas = utils.read_sheet(self.spreadsheet, _("Program risk areas"), [0])
        booleanFrame = areas.isnull()
        for program, areas in booleanFrame.iterrows():
            for risk, value in areas.items():
                if self.prog_areas.get(risk) is None:
                    self.prog_areas[risk] = []
                if not value:
                    self.prog_areas[risk].append(program)

    @translate
    def pop_risks(self):
        areas = utils.read_sheet(self.spreadsheet, _("Population risk areas"), [0])
        booleanFrame = areas.isnull()
        for program, areas in booleanFrame.iterrows():
            for risk, value in areas.items():
                if self.pop_areas.get(risk) is None:
                    self.pop_areas[risk] = []
                if not value:
                    self.pop_areas[risk].append(program)

    @translate
    def relative_risks(self):
        # risk areas hidden in spreadsheet (white text)
        # stunting
        rr_sheet = utils.read_sheet(self.spreadsheet, _("Relative risks"), [0, 1, 2], skiprows=1)
        rr = rr_sheet.loc[_("Stunting")].to_dict()
        self.rr_death[_("Stunting")] = self.make_dict2(rr)
        # wasting
        rr_sheet = utils.read_sheet(self.spreadsheet, _("Relative risks"), [0, 1, 2], skiprows=28)
        rr = rr_sheet.loc[_("Wasting")].to_dict()
        self.rr_death[_("Wasting")] = self.make_dict2(rr)
        # anaemia
        rr_sheet = utils.read_sheet(self.spreadsheet, _("Relative risks"), [0, 1, 2], skiprows=55).dropna(axis=1, how="all")
        rr = rr_sheet.loc[_("Anaemia")].to_dict()
        self.rr_death[_("Anaemia")] = self.make_dict2(rr)
        # currently no impact on mortality for anaemia
        self.rr_death[_("Anaemia")].update({age: {cat: {_("Diarrhoea"): 1} for cat in self.settings.anaemia_list} for age in self.settings.child_ages})
        # breastfeeding
        rr_sheet = utils.read_sheet(self.spreadsheet, _("Relative risks"), [0, 1, 2], skiprows=64)
        rr = rr_sheet.loc[_("Breastfeeding")].to_dict()
        self.rr_death[_("Breastfeeding")] = self.make_dict2(rr)
        # diarrhoea
        rr_sheet = utils.read_sheet(self.spreadsheet, _("Relative risks"), [0, 1, 2], skiprows=103).dropna(axis=1, how="all")
        rr = rr_sheet.loc[_("Diarrhoea")].to_dict()
        self.rr_dia = self.make_dict3(rr)

    @translate
    def compute_risks(self, input_data=None):
        """ Turn rr_death into an array"""
        for age in self.settings.child_ages:
            self.arr_rr_death[age] = np.zeros((self.settings.n_cats, len(input_data.causes_death)))
            stunting = self.rr_death[_("Stunting")][age]
            wasting = self.rr_death[_("Wasting")][age]
            bf = self.rr_death[_("Breastfeeding")][age]
            anaemia = self.rr_death[_("Anaemia")][age]
            for i, cats in enumerate(self.settings.all_cats):
                stuntcat = cats[0]
                wastcat = cats[1]
                anaemcat = cats[2]
                bfcat = cats[3]
                for j, cause in enumerate(input_data.causes_death):
                    stunt = stunting[stuntcat].get(cause, 1)
                    wast = wasting[wastcat].get(cause, 1)
                    anaem = anaemia[anaemcat].get(cause, 1)
                    breast = bf[bfcat].get(cause, 1)
                    self.arr_rr_death[age][i, j] = stunt * wast * anaem * breast

    @translate
    def odds_ratios(self):
        or_sheet = utils.read_sheet(self.spreadsheet, _("Odds ratios"), [0, 1], skiprows=1)
        this_or = or_sheet.loc[_("Condition")].to_dict("index")
        self.or_cond[_("Stunting")] = sc.odict()
        self.or_cond[_("Stunting")][_("Prev stunting")] = this_or[_("Given previous stunting (HAZ < -2 in previous age band)")]
        self.or_cond[_("Stunting")][_("Diarrhoea")] = this_or[_("Diarrhoea (per additional episode)")]
        self.or_cond[_("SAM")] = sc.odict()
        self.or_cond[_("SAM")][_("Diarrhoea")] = or_sheet.loc[_("Wasting")].to_dict("index")[_("For SAM per additional episode of diarrhoea")]
        self.or_cond[_("MAM")] = sc.odict()
        self.or_cond[_("MAM")][_("Diarrhoea")] = or_sheet.loc[_("Wasting")].to_dict("index")[_("For MAM per additional episode of diarrhoea")]
        self.or_cond[_("Anaemia")] = sc.odict()
        self.or_cond[_("Anaemia")][_("Severe diarrhoea")] = sc.odict()
        self.or_cond[_("Anaemia")][_("Severe diarrhoea")] = or_sheet.loc[_("Anaemia")].to_dict("index")[_("For anaemia per additional episode of severe diarrhoea")]
        self.or_stunting_prog = or_sheet.loc[_("By program")].to_dict("index")
        self.or_bf_prog = or_sheet.loc[_("Odds ratios for correct breastfeeding by program")].to_dict("index")
        or_sheet = utils.read_sheet(self.spreadsheet, _("Odds ratios"), [0, 1], skiprows=18).dropna(axis=1, how="all")
        self.or_space_prog = or_sheet.loc[_("Odds ratios for optimal birth spacing by program")].to_dict("index")

    @translate
    def get_bo_progs(self):
        progs = utils.read_sheet(self.spreadsheet, _("Programs birth outcomes"), [0, 1], "index")
        newprogs = sc.odict()
        for program in progs.keys():
            if not newprogs.get(program[0]):
                newprogs[program[0]] = sc.odict()
            newprogs[program[0]][program[1]] = progs[program]
        self.bo_progs = newprogs

    @translate
    def anaemia_progs(self):
        anaem_sheet = utils.read_sheet(self.spreadsheet, _("Programs anaemia"), [0, 1])
        self.rr_anaem_prog = anaem_sheet.loc[_("Relative risks of anaemia when receiving intervention")].to_dict(orient="index")
        self.or_anaem_prog = anaem_sheet.loc[_("Odds ratios of being anaemic when covered by intervention")].to_dict(orient="index")

    @translate
    def wasting_progs(self):
        wastingSheet = utils.read_sheet(self.spreadsheet, _("Programs wasting"), [0, 1])
        treatsam = wastingSheet.loc[_("Odds ratio of SAM when covered by program")].to_dict(orient="index")
        manman = wastingSheet.loc[_("Odds ratio of MAM when covered by program")].to_dict(orient="index")
        self.or_wasting_prog[_("SAM")] = treatsam
        if self.man_mam:
            self.or_wasting_prog[_("MAM")] = {_("Treatment of SAM"): manman["Management of MAM"]}

    @translate
    def get_child_progs(self):
        self.child_progs = utils.read_sheet(self.spreadsheet, _("Programs for children"), [0, 1, 2], to_odict=True)

    @translate
    def get_pw_progs(self):
        self.pw_progs = utils.read_sheet(self.spreadsheet, _("Programs for PW"), [0, 1, 2], to_odict=True)

    @translate
    def get_bo_risks(self):
        bo_sheet = utils.read_sheet(self.spreadsheet, _("Birth outcome risks"), [0, 1], skiprows=[0])
        ors = bo_sheet.loc[_("Odds ratios for conditions")].to_dict("index")
        self.or_cond_bo[_("Stunting")] = ors[_("Stunting (HAZ-score < -2)")]
        self.or_cond_bo[_("MAM")] = ors[_("MAM (WHZ-score between -3 and -2)")]
        self.or_cond_bo[_("SAM")] = ors[_("SAM (WHZ-score < -3)")]
        self.rr_space_bo = bo_sheet.loc[_("Relative risk by birth spacing")].to_dict("index")
        self.rr_death[_("Birth outcomes")] = bo_sheet.loc[_("Relative risks of neonatal causes of death")].to_dict()

    @translate
    def get_iycf_effects(self, iycf_packs):
        # TODO: need something that catches if iycf packages not included at all.
        effects = utils.read_sheet(self.spreadsheet, _("IYCF odds ratios"), [0, 1, 2])
        bf_effects = effects.loc[_("Odds ratio for correct breastfeeding")]
        stunt_effects = effects.loc[_("Odds ratio for stunting")]
        self.or_bf_prog.update(self.create_iycf(bf_effects, iycf_packs))
        self.or_stunting_prog.update(self.create_iycf(stunt_effects, iycf_packs))

    @translate
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
                ORs[age] = 1.0
                for pop, mode in item:
                    row = effects.loc[pop, mode]
                    thisOR = row[age]
                    ORs[age] *= thisOR
            newPrograms[key].update(ORs)
        return newPrograms

    @translate
    def define_iycf(self):
        """ Returns a dict with values as a list of two tuples (age, modality)."""
        IYCFpackages = self.input_data.parse(sheet_name=_("IYCF packages"), index_col=[0, 1])
        packagesDict = sc.odict()
        for packageName, package in IYCFpackages.groupby(level=[0, 1]):
            if packageName[0] not in packagesDict:
                packagesDict[packageName[0]] = []
            for mode in package:
                col = package[mode]
                if col.notnull()[0]:
                    if mode == _("Mass media"):
                        ageModeTuple = [(pop, mode) for pop in self.settings.child_ages[:-1]]  # exclude 24-59 months
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
                result[age].update({keys[0]: {keys[1]: {keys[2]: val}}})
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
                    res_dict[age][cat] = dict()  # CK TEST
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

        self.locale = get_databook_locale(data.book)

        self.spreadsheet = data
        self.settings = settings.Settings(self.locale)
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
        self.calcscache = calcscache

        self.get_demo()
        self.get_proj()
        self.get_risk_dist()
        self.get_death_dist()
        self.get_time_trends()
        self.get_incidences()

    def __repr__(self):
        output = sc.prepr(self)
        return output

    def __setstate__(self, d):
        self.__dict__ = d
        d = migrate(self)
        self.__dict__ = d.__dict__

    ## DEMOGRAPHICS ##

    @translate
    def get_demo(self):
        # Load the main spreadsheet into a DataFrame.

        baseline = utils.read_sheet(self.spreadsheet, _("Baseline year population inputs"), [0, 1])

        # Recalculate cells that need it, and remember in the calculations cache.
        frac_rice = baseline.loc[(_("Food"), _("Fraction eating rice as main staple food")), _("Data")]
        frac_wheat = baseline.loc[(_("Food"), _("Fraction eating wheat as main staple food")), _("Data")]
        frac_maize = baseline.loc[(_("Food"), _("Fraction eating maize as main staple food")), _("Data")]
        frac_other_staples = 1.0 - frac_rice - frac_wheat - frac_maize
        baseline.loc[(_("Food"), _("Fraction on other staples as main staple food")), _("Data")] = frac_other_staples
        self.calcscache.write_cell(_("Baseline year population inputs"), 19, 2, frac_other_staples)
        birth_spacing_sum = baseline.loc[_("Birth spacing"), _("Data")][0:4].sum()
        baseline.loc[_("Birth spacing"), _("Total (must be 100%)")] = birth_spacing_sum
        self.calcscache.write_cell(_("Baseline year population inputs"), 32, 2, birth_spacing_sum)
        outcome_sum = baseline.loc[_("Birth outcome distribution"), _("Data")][0:3].sum()
        baseline.loc[(_("Birth outcome distribution"), _("Term AGA")), _("Data")] = 1.0 - outcome_sum
        self.calcscache.write_cell(_("Baseline year population inputs"), 47, 2, 1.0 - outcome_sum)

        demo = sc.odict()
        # the fields that group the data in spreadsheet
        fields = [_("Population data"), _("Food"), _("Age distribution of pregnant women"), _("Mortality"), _("Other risks")]
        for field in fields:
            demo.update(baseline.loc[field].to_dict("index"))
        self.demo = {key: item[_("Data")] for key, item in demo.items()}
        self.demo["Birth dist"] = baseline.loc[_("Birth outcome distribution")].to_dict()[_("Data")]
        t = baseline.loc[_("Projection years")]
        self.t = [int(t.loc[_("Baseline year (projection start year)")][_("Data")]), int(t.loc[_("End year")][_("Data")])]
        # birth spacing
        self.birth_space = baseline.loc[_("Birth spacing")].to_dict()[_("Data")]
        self.birth_space.pop(_("Total (must be 100%)"), None)

        # Load the main spreadsheet into a DataFrame (slightly different format).
        # fix ages for PW
        baseline = utils.read_sheet(self.spreadsheet, _("Baseline year population inputs"), [0])

        for row in baseline.loc[_(("Age distribution of pregnant women"))].iterrows():
            self.pw_agedist.append(row[1][_("Data")])
        return None

    @translate
    def get_proj(self):
        # Load the main spreadsheet into a DataFrame.
        # drops rows with any na

        proj = utils.read_sheet(self.spreadsheet, _("Demographic projections"), cols=[0], dropna="any")

        # Read in the Baseline spreadsheet information we'll need.
        baseline = utils.read_sheet(self.spreadsheet, _("Baseline year population inputs"), [0, 1])
        stillbirth = baseline.loc[_("Mortality")].loc[_("Stillbirths (per 1,000 total births)")].values[0]
        abortion = baseline.loc[_("Mortality")].loc[_("Fraction of pregnancies ending in spontaneous abortion")].values[0]

        # Recalculate cells that need it, and remember in the calculations cache.
        total_wra = proj.loc[:, [_("WRA: 15-19 years"), _("WRA: 20-29 years"), _("WRA: 30-39 years"), _("WRA: 40-49 years")]].sum(axis=1).values
        proj.loc[:, _("Total WRA")] = total_wra
        self.calcscache.write_col(_("Demographic projections"), 1, 6, total_wra)
        numbirths = proj.loc[:, _("Number of births")].values
        estpregwomen = (numbirths + numbirths * stillbirth / (1000.0 - stillbirth)) / (1.0 - abortion)
        proj.loc[:, _("Estimated pregnant women")] = estpregwomen
        self.calcscache.write_col(_("Demographic projections"), 1, 7, estpregwomen)
        nonpregwra = total_wra - estpregwomen
        proj.loc[:, _("non-pregnant WRA")] = nonpregwra
        self.calcscache.write_col(_("Demographic projections"), 1, 8, nonpregwra)

        # dict of lists to support indexing
        for column in proj:
            self.proj[column] = proj[column].tolist()
        # wra pop projections list in increasing age order
        for age in self.settings.wra_ages:
            self.wra_proj.append(proj[age].tolist())

    @translate
    def get_risk_dist(self):
        # Load the main spreadsheet into a DataFrame.

        dist = utils.read_sheet(self.spreadsheet, _(_("Nutritional status distribution")), [0, 1])

        # Recalculate cells that need it, and remember in the calculations cache.
        stunting_mod_hi_sums = dist.loc[_("Stunting (height-for-age)")].iloc[2:4, 0:5].astype(np.float).sum().values
        stunting_invs = norm.ppf(stunting_mod_hi_sums, 0.0, 1.0)
        stunting_norm_pcts = np.ones(5) - norm.cdf(stunting_invs + np.ones(5), 0.0, 1.0)
        cols = dist.columns[0:5]
        dist.loc[(_("Stunting (height-for-age)"), _("Normal (HAZ-score > -1)")), cols] = stunting_norm_pcts
        self.calcscache.write_row(_("Nutritional status distribution"), 1, 2, stunting_norm_pcts)
        stunting_mild_pcts = norm.cdf(stunting_invs + np.ones(5), 0.0, 1.0) - stunting_mod_hi_sums
        dist.loc[(_("Stunting (height-for-age)"), _("Mild (HAZ-score between -2 and -1)")), cols] = stunting_mild_pcts
        self.calcscache.write_row(_("Nutritional status distribution"), 2, 2, stunting_mild_pcts)
        wasting_mod_hi_sums = dist.loc[_("Wasting (weight-for-height)")].iloc[2:4, 0:5].astype(np.float).sum().values
        wasting_invs = norm.ppf(wasting_mod_hi_sums, 0.0, 1.0)
        wasting_norm_pcts = np.ones(5) - norm.cdf(wasting_invs + np.ones(5), 0.0, 1.0)
        dist.loc[(_("Wasting (weight-for-height)"), _("Normal  (WHZ-score > -1)")), cols] = wasting_norm_pcts
        self.calcscache.write_row(_("Nutritional status distribution"), 7, 2, wasting_norm_pcts)
        wasting_mild_pcts = norm.cdf(wasting_invs + np.ones(5), 0.0, 1.0) - wasting_mod_hi_sums
        dist.loc[(_("Wasting (weight-for-height)"), _("Mild  (WHZ-score between -2 and -1)")), cols] = wasting_mild_pcts
        self.calcscache.write_row(_("Nutritional status distribution"), 8, 2, wasting_mild_pcts)

        # dist = dist.drop(dist.index[[1]])
        riskDist = sc.odict()
        for key, field in zip([_('Stunting'),_('Wasting')], [_("Stunting (height-for-age)"), _("Wasting (weight-for-height)")]):
            riskDist[key] = dist.loc[field].dropna(axis=1, how="all").to_dict("dict")
        # fix key refs (surprisingly hard to do in Pandas)
        for outer, ageCat in riskDist.items():
            self.risk_dist[outer] = sc.odict()
            for age, catValue in ageCat.items():
                self.risk_dist[outer][age] = dict()
                for cat, value in catValue.items():
                    newCat = cat.split(" ", 1)[0]
                    self.risk_dist[outer][age][newCat] = value

        # Load the main spreadsheet into a DataFrame, but skipping 12 rows.
        # get anaemia
        dist = utils.read_sheet(self.spreadsheet, _("Nutritional status distribution"), [0, 1], skiprows=12)

        self.risk_dist[_("Anaemia")] = sc.odict()

        # Recalculate cells that need it, and remember in the calculations cache.
        all_anaem = dist.loc[_("Anaemia"), _("Prevalence of anaemia")].to_dict()
        baseline = utils.read_sheet(self.spreadsheet, _("Baseline year population inputs"))
        index = np.array(baseline["Field"]).tolist().index(_("Percentage of anaemia that is iron deficient"))
        iron_pct = np.array(baseline[_("Data")])[index]
        anaem = dist.loc[_("Anaemia"), _("Prevalence of anaemia")] * iron_pct
        self.calcscache.write_row(_("Nutritional status distribution"), 14, 2, anaem.values)

        # These should work, but don't in Google Cloud.
        # anaem = sc.odict({key: val * iron_pct for key, val in all_anaem.items()})
        # self.calcscache.write_row('Nutritional status distribution', 14, 2, anaem[:])

        # for age, prev in anaem.items():  # Should work with commented out code above
        for age, prev in anaem.iteritems():
            self.risk_dist[_("Anaemia")][age] = dict()
            self.risk_dist[_("Anaemia")][age][_("Anaemic")] = prev
            self.risk_dist[_("Anaemia")][age][_("Not anaemic")] = 1.0 - prev

        # Load the main spreadsheet into a DataFrame.
        # get breastfeeding dist
        dist = utils.read_sheet(self.spreadsheet, _("Breastfeeding distribution"), [0, 1])

        # Recalculate cells that need it, and remember in the calculations cache.
        calc_cells = 1.0 - dist.loc[_("Breastfeeding")].iloc[0:3].sum().values
        self.calcscache.write_row(_("Breastfeeding distribution"), 4, 2, calc_cells)
        dist.loc[(_("Breastfeeding"), "None"), :] = calc_cells

        self.risk_dist[_("Breastfeeding")] = dist.loc[_("Breastfeeding")].to_dict()

    @translate
    def get_time_trends(self):

        trends = utils.read_sheet(self.spreadsheet, _("Time trends"), cols=[0, 1], dropna=False)

        self.time_trends[_("Stunting")] = trends.loc[_("Stunting prevalence (%)")].loc[_("Children 0-59 months")].values.tolist()[:1]
        self.time_trends[_("Wasting")] = trends.loc[_("Wasting prevalence (%)")].loc[_("Children 0-59 months")].values.tolist()[:1]
        self.time_trends[_("Anaemia")] = trends.loc[_("Anaemia prevalence (%)")].values.tolist()[:3]  # order is (children, PW, WRA)
        self.time_trends[_("Breastfeeding")] = trends.loc[_("Prevalence of age-appropriate breastfeeding")].values.tolist()[:2]  # 0-5 months, 6-23 months
        self.time_trends[_("Mortality")] = trends.loc[_("Mortality")].values.tolist()  # under 5, maternal

    @translate
    def get_incidences(self):

        incidences = utils.read_sheet(self.spreadsheet, _("Incidence of conditions"), [0])

        # Recalculate cells that need it, and remember in the calculations cache.
        baseline = utils.read_sheet(self.spreadsheet, _("Baseline year population inputs"), [0, 1])
        diarr_incid = baseline.loc[_("Diarrhoea incidence")][_("Data")].values
        incidences.loc[_("Diarrhoea"), :] = diarr_incid
        self.calcscache.write_row(_("Incidence of conditions"), 1, 1, diarr_incid)
        dist = utils.read_sheet(self.spreadsheet, _("Nutritional status distribution"), [0, 1])
        mam_incid = dist.loc[_("Wasting (weight-for-height)")].loc[_("MAM   (WHZ-score between -3 and -2)")][0:5].values.astype(np.float) * 2.6
        sam_incid = dist.loc[_("Wasting (weight-for-height)")].loc[_("SAM   (WHZ-score < -3)")][0:5].values.astype(np.float) * 2.6
        incidences.loc[_("MAM"), :] = mam_incid
        self.calcscache.write_row(_("Incidence of conditions"), 2, 1, mam_incid)
        incidences.loc[_("SAM"), :] = sam_incid
        self.calcscache.write_row(_("Incidence of conditions"), 3, 1, sam_incid)

        self.incidences = incidences.to_dict()

    ### MORTALITY ###

    @translate
    def get_death_dist(self):

        # Load the main spreadsheet into a DataFrame.
        deathdist = utils.read_sheet(self.spreadsheet, _("Causes of death"), [0, 1], skiprows=1)

        # Recalculate cells that need it, and remember in the calculations cache.
        neonatal_death_pct_sum = deathdist.loc[_("Neonatal")][_("<1 month")].values[:-1].astype(np.float).sum()
        self.calcscache.write_cell(_("Causes of death"), 10, 2, neonatal_death_pct_sum)
        children_death_pct_sums = deathdist.loc[_("Children")].iloc[1:-1, 0:4].astype(np.float).sum().values
        self.calcscache.write_row(_("Causes of death"), 22, 2, children_death_pct_sums)
        pregwomen_death_pct_sum = deathdist.loc[_("Pregnant women")].iloc[1:-1, 0].values.astype(np.float).sum()
        self.calcscache.write_cell(_("Causes of death"), 34, 2, pregwomen_death_pct_sum)

        neonates = deathdist.loc[_("Neonatal")].iloc[:-1].dropna(axis=1)

        children = utils.read_sheet(self.spreadsheet, _("Causes of death"), [0, 1])
        children = deathdist.loc[_("Children")]
        children.columns = children.iloc[0]
        children = children.iloc[1:-1].dropna(axis=1)

        pw = utils.read_sheet(self.spreadsheet, _("Causes of death"), [0, 1])
        pw = deathdist.loc[_("Pregnant women")]
        pw.columns = pw.iloc[0]
        pw = pw.iloc[1:-1].dropna(axis=1)
        for grp in self.settings.pw_ages:
            pw[grp] = pw.iloc[:,0]
        pw = pw.iloc[:,1:]

        death_dist = pandas.concat([neonates, children, pw])
        death_dist.fillna(0, inplace=True)
        death_dist = death_dist.T.to_dict()
        death_dist = sc.odict({k:sc.odict(v) for k,v in death_dist.items()})

        self.death_dist = death_dist
        self.causes_death = self.death_dist.keys()


class ProgData(object):
    """Stores all the settings for each project, defined by the user"""

    def __init__(self, data, default_data, calcscache):

        self.locale = get_databook_locale(data.book)

        self.settings = settings.Settings(self.locale)
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
        self.calcscache = calcscache

        # load data
        self.get_prog_info()
        self.get_prog_target()
        self.get_prog_deps()
        self.get_ref_progs()
        self.get_famplan_methods()
        self.create_iycf()
        self.recalc_treatsam_prog_costs()
        self.spreadsheet = None  # Reset to save memory
        self.validate()

    def __repr__(self):
        output = sc.prepr(self)
        return output

    def __setstate__(self, d):
        self.__dict__ = d
        d = migrate(self)
        self.__dict__ = d.__dict__

    def validate(self):
        """ Validate program data """
        invalid = []
        for progname in self.base_prog_set:
            cov = self.base_cov[progname]
            if cov < 0 or cov > 1:
                errormsg = _("Baseline coverage is outside the interval (0, 100) for %s") % progname
                invalid.append(errormsg)
            sat = self.sat[progname]
            if sat < 0 or sat > 1:
                errormsg = _("Saturation is outside the interval (0, 100) for %s") % progname
                invalid.append(errormsg)
            cost = self.costs[progname]
            if cost <= 0:
                errormsg = _("Cost is 0 or negative for %s") % progname
                invalid.append(errormsg)
            if progname not in self.prog_target.keys():
                errormsg = _("Target population not defined for %s") % progname
                invalid.append(errormsg)
            elif sum(self.prog_target[progname].values()) == 0:
                errormsg = _("Target population is 0 for %s") % progname
                invalid.append(errormsg)
        if invalid:
            errors = "\n\n".join(invalid)
            raise Exception(errors)

    @translate
    def get_prog_target(self):
        # Load the main spreadsheet into a DataFrame.

        targetPopSheet = utils.read_sheet(self.spreadsheet, _("Programs target population"), [0, 1])

        # Recalculate cells that need it, and remember in the calculations cache.
        baseline = utils.read_sheet(self.spreadsheet, _("Baseline year population inputs"), [0, 1])
        food_insecure = baseline.loc[_("Population data")].loc[_("Percentage of population food insecure (default poor)")].values[0]
        frac_malaria_risk = baseline.loc[_("Population data")].loc[_("Percentage of population at risk of malaria")].values[0]
        school_attendance = baseline.loc[_("Population data")].loc[_("School attendance (percentage of 15-19 year women)")].values[0]
        frac_PW_health_facility = baseline.loc[_("Population data")].loc[_("Percentage of pregnant women attending health facility")].values[0]
        frac_children_health_facility = baseline.loc[_("Population data")].loc[_("Percentage of children attending health facility")].values[0]
        famplan_unmet_need = baseline.loc[_("Population data")].loc[_("Unmet need for family planning")].values[0]
        frac_rice = baseline.loc[_("Food")].loc[_("Fraction eating rice as main staple food")].values[0]
        frac_wheat = baseline.loc[_("Food")].loc[_("Fraction eating wheat as main staple food")].values[0]
        frac_maize = baseline.loc[_("Food")].loc[_("Fraction eating maize as main staple food")].values[0]
        diarr_incid = baseline.loc[_("Diarrhoea incidence")][_("Data")].values
        if len(baseline.loc[_("Other risks")].values) < 4:
            print(_("Warning, the databook being read is out of date and does not include baseline prevalences of eclampsia and pre-eclampsia so global averages will be used."))
            preeclampsia_prev = self.settings.global_eclampsia_prevalence["Pre-eclampsia"]
            eclampsia_prev = self.settings.global_eclampsia_prevalence["Eclampsia"]
        else:
            preeclampsia_prev = baseline.loc[_("Other risks")].loc[_("Prevalence of pre-eclampsia")].values[0]
            eclampsia_prev = baseline.loc[_("Other risks")].loc[_("Prevalence of eclampsia")].values[0]
        treatsam = self.spreadsheet.parse(sheet_name=_("Treatment of SAM"))
        comm_deliv_raw = treatsam.iloc[1][_("Add extension")]
        comm_deliv = pandas.notnull(comm_deliv_raw)
        cash_transfers_row = food_insecure * np.ones(4)
        targetPopSheet.loc[_("Children"), _("Cash transfers")].iloc[1:5] = cash_transfers_row
        self.calcscache.write_row(_("Programs target population"), 1, 3, cash_transfers_row)
        lipid_row = food_insecure * np.ones(2)
        targetPopSheet.loc[_("Children"), _("Lipid-based nutrition supplements")].iloc[2:4] = lipid_row
        self.calcscache.write_row(_("Programs target population"), 4, 4, lipid_row)
        oral_rehyd_row = diarr_incid
        targetPopSheet.loc[_("Children"), _("Oral rehydration salts")].iloc[0:5] = oral_rehyd_row
        self.calcscache.write_row(_("Programs target population"), 6, 2, oral_rehyd_row)
        pub_prov_row = food_insecure * np.ones(2)
        targetPopSheet.loc[_("Children"), _("Public provision of complementary foods")].iloc[2:4] = pub_prov_row
        self.calcscache.write_row(_("Programs target population"), 7, 4, pub_prov_row)
        if comm_deliv:
            treat_SAM_val = 1.0
        else:
            treat_SAM_val = frac_children_health_facility
        treat_SAM_row = treat_SAM_val * np.ones(4)
        targetPopSheet.loc[_("Children"), _("Treatment of SAM")].iloc[1:5] = treat_SAM_row
        self.calcscache.write_row(_("Programs target population"), 8, 3, treat_SAM_row)
        zinc_treatment_row = diarr_incid
        targetPopSheet.loc[_("Children"), _("Zinc for treatment + ORS")].iloc[0:5] = zinc_treatment_row
        self.calcscache.write_row(_("Programs target population"), 10, 2, zinc_treatment_row)
        balanced_energy_row = food_insecure * np.ones(4)
        targetPopSheet.loc[_("Pregnant women"), _("Balanced energy-protein supplementation")].iloc[5:9] = balanced_energy_row
        self.calcscache.write_row(_("Programs target population"), 13, 7, balanced_energy_row)
        IFAS_preg_health_row = frac_PW_health_facility * np.ones(4)
        targetPopSheet.loc[_("Pregnant women"), _("IFAS for pregnant women (health facility)")].iloc[5:9] = IFAS_preg_health_row
        self.calcscache.write_row(_("Programs target population"), 16, 7, IFAS_preg_health_row)
        IPTp_row = frac_malaria_risk * np.ones(4)
        targetPopSheet.loc[_("Pregnant women"), _("IPTp")].iloc[5:9] = IPTp_row
        self.calcscache.write_row(_("Programs target population"), 17, 7, IPTp_row)
        mg_eclampsia_row = eclampsia_prev * np.ones(4)
        targetPopSheet.loc[_("Pregnant women"), _("Mg for eclampsia")].iloc[5:9] = mg_eclampsia_row
        self.calcscache.write_row(_("Programs target population"), 18, 7, mg_eclampsia_row)
        mg_preeclampsia_row = preeclampsia_prev * np.ones(4)
        targetPopSheet.loc[_("Pregnant women"), _("Mg for pre-eclampsia")].iloc[5:9] = mg_preeclampsia_row
        self.calcscache.write_row(_("Programs target population"), 19, 7, mg_preeclampsia_row)
        fam_planning_row = famplan_unmet_need * np.ones(4)
        targetPopSheet.loc[_("Non-pregnant WRA"), _("Family planning")].iloc[9:13] = fam_planning_row
        self.calcscache.write_row(_("Programs target population"), 22, 11, fam_planning_row)
        IFAS_comm_row = np.ones(4)
        IFAS_comm_row[0] = (1.0 - food_insecure) * 0.49 * (1.0 - school_attendance) + food_insecure * 0.7 * (1.0 - school_attendance)
        IFAS_comm_row[1:] = (1.0 - food_insecure) * 0.49 + food_insecure * 0.7
        targetPopSheet.loc[_("Non-pregnant WRA"), _("IFAS (community)")].iloc[9:13] = IFAS_comm_row
        self.calcscache.write_row(_("Programs target population"), 23, 11, IFAS_comm_row)
        IFAS_health_fac_row = np.ones(4)
        IFAS_health_fac_row[0] = (1.0 - food_insecure) * 0.21 * (1.0 - school_attendance) + food_insecure * 0.3 * (1.0 - school_attendance)
        IFAS_health_fac_row[1:] = (1.0 - food_insecure) * 0.21 + food_insecure * 0.3
        targetPopSheet.loc[_("Non-pregnant WRA"), _("IFAS (health facility)")].iloc[9:13] = IFAS_health_fac_row
        self.calcscache.write_row(_("Programs target population"), 24, 11, IFAS_health_fac_row)
        IFAS_retailer_row = np.ones(4)
        IFAS_retailer_row[0] = (1.0 - food_insecure) * 0.3 * (1.0 - school_attendance)
        IFAS_retailer_row[1:] = (1.0 - food_insecure) * 0.3
        targetPopSheet.loc[_("Non-pregnant WRA"), _("IFAS (retailer)")].iloc[9:13] = IFAS_retailer_row
        self.calcscache.write_row(_("Programs target population"), 25, 11, IFAS_retailer_row)
        IFAS_school_row = (1.0 - food_insecure) * school_attendance + food_insecure * school_attendance
        targetPopSheet.loc[_("Non-pregnant WRA"), _("IFAS (school)")].iloc[9] = IFAS_school_row
        self.calcscache.write_cell(_("Programs target population"), 26, 11, IFAS_school_row)
        IFA_maize_row = frac_maize * np.ones(11)
        targetPopSheet.loc[_("General population"), _("IFA fortification of maize")].iloc[2:13] = IFA_maize_row
        self.calcscache.write_row(_("Programs target population"), 28, 4, IFA_maize_row)
        IFA_rice_row = frac_rice * np.ones(11)
        targetPopSheet.loc[_("General population"), _("IFA fortification of rice")].iloc[2:13] = IFA_rice_row
        self.calcscache.write_row(_("Programs target population"), 29, 4, IFA_rice_row)
        IFA_wheat_row = frac_wheat * np.ones(11)
        targetPopSheet.loc[_("General population"), _("IFA fortification of wheat flour")].iloc[2:13] = IFA_wheat_row
        self.calcscache.write_row(_("Programs target population"), 30, 4, IFA_wheat_row)
        bednet_row = frac_malaria_risk * np.ones(13)
        targetPopSheet.loc[(_("General population"), _("Long-lasting insecticide-treated bednets")), :] = bednet_row
        self.calcscache.write_row(_("Programs target population"), 32, 2, bednet_row)

        targetPop = sc.odict()
        for pop in [_("Children"), _("Pregnant women"), _("Non-pregnant WRA"), _("General population")]:
            targetPop.update(targetPopSheet.loc[pop].to_dict(orient="index"))
        self.prog_target = targetPop

    @translate
    def get_ref_progs(self):
        reference = self.spreadsheet.parse(sheet_name=_("Reference programs"), index_col=[0])
        self.ref_progs = list(reference.index)

    @translate
    def get_prog_deps(self):
        deps = utils.read_sheet(self.spreadsheet, _("Program dependencies"), [0])
        programDep = sc.odict()
        for program, dependency in deps.iterrows():
            programDep[program] = sc.odict()
            for dependType, value in dependency.items():
                if sc.isstring(value):  # cell not empty
                    programDep[program][dependType] = value.replace(", ", ",").split(",")  # assumes programs separated by ", "
                else:
                    programDep[program][dependType] = []
        # pad the remaining programs
        missingProgs = list(set(self.base_prog_set) - set(programDep.keys()))
        for program in missingProgs:
            programDep[program] = sc.odict()
            for field in deps.columns:
                programDep[program][field] = []
        self.prog_deps = programDep

    @translate
    def get_famplan_methods(self):
        # Load the main spreadsheet into a DataFrame.
        famplan_methods = utils.read_sheet(self.spreadsheet, _("Programs family planning"), [0])

        # Recalculate cells that need it, and remember in the calculations cache.
        dist = famplan_methods.loc[:, _("Distribution")].values
        costs = famplan_methods.loc[:, _("Cost")].values
        prop_costs = dist * costs
        famplan_methods.loc[:, _("Proportional Cost")] = prop_costs
        self.calcscache.write_col("Programs family planning", 1, 4, prop_costs)

        self.famplan_methods = famplan_methods.to_dict("index")

    @translate
    def get_prog_info(self):
        # Load the main spreadsheet into a DataFrame.
        sheet = utils.read_sheet(self.spreadsheet, _("Programs cost and coverage"))

        self.base_prog_set = sheet.iloc[:, 0].tolist()  # This grabs _all_ programs even those with zero unit cost.
        self.base_cov = sc.odict(zip(self.base_prog_set, sheet.iloc[:, 1].tolist()))
        self.sat = sc.odict(zip(self.base_prog_set, sheet.iloc[:, 2].tolist()))
        self.costs = sc.odict(zip(self.base_prog_set, sheet.iloc[:, 3].tolist()))
        costtypes = self._format_costtypes(sheet.iloc[:, 4].tolist())
        self.costtype = sc.odict(zip(self.base_prog_set, costtypes))

    @translate
    def _format_costtypes(self, oldlabs):
        maps = {_("Linear (constant marginal cost) [default]"): "linear",
                _("Curved with increasing marginal cost"): "increasing",
                _("Curved with decreasing marginal cost"): "decreasing",
                _("S-shaped (decreasing then increasing marginal cost)"): "s-shaped",
                }
        newlabs = []
        for lab in oldlabs:
            newlabs.append(maps[lab])
        return newlabs

    def create_iycf(self):
        packages = self.define_iycf()
        # remove IYCF from base progs if it isn't appropriately defined (avoid error in baseline)
        remprog = [key for key, val in packages.iteritems() if not val]
        self.base_prog_set = [prog for prog in self.base_prog_set if prog not in remprog]
        packages = sc.odict({key: val for key, val in packages.iteritems() if val})
        target = self.get_iycf_target(packages)
        self.prog_target.update(target)

    @translate
    def define_iycf(self):
        """ Returns a dict with values as a list of two tuples (age, modality)."""
        IYCFpackages = self.spreadsheet.parse(sheet_name=_("IYCF packages"), index_col=[0, 1])
        packagesDict = sc.odict()
        for packageName, package in IYCFpackages.groupby(level=[0, 1]):
            if packageName[0] not in packagesDict:
                packagesDict[packageName[0]] = []
            for mode in package:
                col = package[mode]
                if col.notnull()[0]:
                    if mode == _("Mass media"):
                        ageModeTuple = [(pop, mode) for pop in self.settings.child_ages[:-1]]  # exclude 24-59 months
                    else:
                        ageModeTuple = [(packageName[1], mode)]
                    packagesDict[packageName[0]] += ageModeTuple
        return packagesDict

    @translate
    def recalc_treatsam_prog_costs(self):
        nutrition_status = utils.read_sheet(self.spreadsheet, _("Nutritional status distribution"), [0, 1])
        sam_prev = []
        for s, span in enumerate(self.settings.child_age_spans):  # weight age group incidence/prevalence by size of group
            sam_prev.append(nutrition_status.values[7][s] * span)
        av_sam_prev = sum(sam_prev) / (sum(self.settings.child_age_spans))  # weighted average under 5 SAM prevalence
        self.costs[_("Treatment of SAM")] *= av_sam_prev * 2.6  # estimated ratio of incidence/prevalence
        return

    @translate
    def get_iycf_target(self, package_modes):
        """Creates the frac of pop targeted by each IYCF package.
        Note that frac in community and mass media assumed to be 1.
        Note also this fraction can exceed 1, and is adjusted for the target pop calculations of the Programs class"""

        pop_data = self.spreadsheet.parse(_("Baseline year population inputs"), index_col=[0, 1]).loc[_("Population data")][_("Data")]
        frac_pw = float(pop_data.loc[_("Percentage of pregnant women attending health facility")])
        frac_child = float(pop_data.loc[_("Percentage of children attending health facility")])
        # target pop is the sum of fractions exposed to modality in each age band
        target = sc.odict()
        for name, package in package_modes.items():
            target[name] = sc.odict()
            for pop, mode in package:
                if target[name].get(pop) is None:
                    target[name][pop] = 0.0
                if mode == _("Health facility"):
                    if pop in self.settings.child_ages:  # children
                        target[name][pop] += frac_child
                    else:  # pregnant women
                        target[name][pop] += frac_pw
                else:  # community or mass media
                    target[name][pop] += 1
        # convert pw to age bands and set missing children + wra to 0
        new_target = sc.dcp(target)
        for name in target.keys():
            if _("Pregnant women") in target[name]:
                new_target[name].update({age: target[name][_("Pregnant women")] for age in self.settings.pw_ages})
                new_target[name].pop(_("Pregnant women"))
            for age in self.settings.all_ages:
                if age not in new_target[name]:
                    new_target[name].update({age: 0})
        return new_target

    def create_age_bands(self, my_dict, keys, ages, pop):
        for key in keys:  # could be program, ages
            subDict = my_dict[key].pop(pop, None)
            newAgeGroups = {age: subDict for age in ages if subDict is not None}
            my_dict[key].update(newAgeGroups)
        return my_dict


class Dataset(object):
    """ Store all the data for a project """

    def __init__(self, country=None, region=None, name=None, demo_data=None, prog_data=None, default_params=None, pops=None, prog_info=None, doload=False, inputspath=None, defaultspath=None, fromfile=None, project=None):

        self.locale = None  # Store the databook locale (set during `Dataset.load`)

        self.country = country
        self.region = region

        self.calcscache = CalcCellCache()

        self.demo_data = demo_data  # demo = demographic
        self.prog_data = prog_data
        self.default_params = default_params  # TODO: this should probably be phased out once the InputData and DefaultParams classes get merged
        # The next three attributes are used to initialize a Model object.
        self.pops = pops  # populations
        self.prog_info = prog_info  # program info
        self.t = None  # start and end years for the simulation
        self.name = name
        self.modified = sc.now(utc=True)
        if doload:
            self.load(project=project)
        return None

    def __repr__(self):
        output = sc.prepr(self)
        return output

    @translate
    def load(self, project=None):

        # Handle inputs
        if project is None:
            raise Exception(_("Sorry, but you must supply a project for load()."))

        # Pull the sheets from the project
        if self.name in project.spreadsheets.keys():
            spreadsheetkey = self.name
        else:
            spreadsheetkey = -1
        inputsheet = project.inputsheet(spreadsheetkey)

        # Convert them to Pandas
        input_data = inputsheet.pandas()

        self.locale = get_databook_locale(input_data.book)

        # If the 'Programs impacted population' worksheet is in input_data, then we are working with one of the newer
        # databooks, so pull the default data from input_data.
        if _("Programs impacted population") in input_data.sheet_names:
            default_data = input_data

        # Otherwise, pull the default data from the legacy spreadsheet.
        else:
            filename = settings.ONpath / "inputs" / self.locale / "legacy_default_params.xlsx"
            default_data = sc.Spreadsheet(filename=filename).pandas()

        # Read them into actual data
        self.demo_data = InputData(input_data, self.calcscache)  # demo_ here is demographic_


        self.default_params = DefaultParams(default_data, input_data)
        self.default_params.compute_risks(self.demo_data)
        self.prog_data = ProgData(input_data, self.default_params, self.calcscache)

        try:
            self.pops = populations.set_pops(self.demo_data, self.default_params)
        except Exception as E:
            raise Exception(_("Error in creating populations, check data and defaults books")+": %s" % str(E))
        self.prog_info = programs.ProgramInfo(self.prog_data)
        self.t = self.demo_data.t
        self.modified = sc.now(utc=True)
        return None

    def prog_names(self):
        """ WARNING, hacky function to get program names """
        names = self.prog_data.base_prog_set
        return names
