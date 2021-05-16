import os
import itertools
import sciris as sc
from .version import version
from .utils import get_translator
import pathlib



class Settings(object):
    """Store all the static data for a project that won't change except between Optima versions
    WARNING: Do not change the order of these lists without checking the potential consequences within the code"""

    def __init__(self, locale):

        _ = get_translator(locale)

        self.t = [2017, 2030]
        self.years = sc.inclusiverange(self.t[0], self.t[1])
        self.n_years = len(self.years)
        self.timestep = 1.0 / 12.0  # in months
        self.stunting_list = ["High", "Moderate", "Mild", "Normal"]
        self.stunted_list = self.stunting_list[:2]
        self.non_stunted_list = self.stunting_list[2:]
        self.anaemia_list = ["Anaemic", "Not anaemic"]
        self.anaemic_list = self.anaemia_list[:1]
        self.non_anaemic_list = self.anaemia_list[1:]
        self.wasting_list = ["SAM", "MAM", "Mild", "Normal"]
        self.wasted_list = self.wasting_list[:2]
        self.non_wasted_list = self.wasting_list[2:]
        self.bf_list = ["Exclusive", "Predominant", "Partial", "None"]
        list_cats = [self.stunting_list, self.wasting_list, self.anaemia_list, self.bf_list]
        self.all_cats = list(itertools.product(*list_cats))
        self.n_cats = len(self.all_cats)
        self.correct_bf = {"<1 month": "Exclusive", "1-5 months": "Exclusive", "6-11 months": "Partial", _("12-23 months"): "Partial", "24-59 months": "None"}
        self.optimal_space = "24 months or greater"
        self.birth_outcomes = ["Term AGA", "Term SGA", "Pre-term AGA", "Pre-term SGA"]
        self.global_eclampsia_prevalence = {"Pre-eclampsia": 0.046, "Eclampsia": 0.014}  # Need data/source, using https://www.ejog.org/article/S0301-2115(13)00196-6/fulltext
        self.all_risks = [self.stunting_list, self.wasting_list, self.bf_list, self.anaemia_list]
        self.child_ages = ["<1 month", "1-5 months", "6-11 months", _("12-23 months"), "24-59 months"]
        self.pw_ages = ["PW: 15-19 years", "PW: 20-29 years", "PW: 30-39 years", "PW: 40-49 years"]
        self.wra_ages = ["WRA: 15-19 years", "WRA: 20-29 years", "WRA: 30-39 years", "WRA: 40-49 years"]
        self.all_ages = self.child_ages + self.pw_ages + self.wra_ages
        self.risks = ["Stunting", "Wasting", "Breastfeeding", "Anaemia"]  # todo: even use this?
        self.child_age_spans = [1.0, 5.0, 6.0, 12.0, 36.0]  # in months
        self.women_age_rates = [1.0 / 5.0, 1.0 / 10.0, 1.0 / 10.0, 1.0 / 10.0]  # in years

    def __repr__(self):
        output = sc.prepr(self)
        return output


ONpath = pathlib.Path(__file__).parent.parent


def data_path(locale, country, region=None):
    region = region or "national"
    return ONpath / "inputs" / locale / f"{country}_{region}_input.xlsx"

#####################################################################################################################
### Define debugging and exception functions/classes
#####################################################################################################################

# Debugging information
def debuginfo(output=False):
    outstr = "\nOptima Nutrition debugging info:\n"
    outstr += "   Version: %s\n" % version
    outstr += "   Branch:  %s\n" % sc.gitinfo()["branch"]
    outstr += "   SHA:     %s\n" % sc.gitinfo()["hash"]
    outstr += "   Date:    %s\n" % sc.gitinfo()["date"]
    outstr += "   Path:    %s\n" % ONpath
    if output:
        return outstr
    else:
        print(outstr)
        return None
