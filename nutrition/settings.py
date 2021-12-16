import os
import itertools
import sciris as sc
from .version import version
from .utils import get_translator
import pathlib
from .migration import migrate

class Settings(object):
    """Store all the static data for a project that won't change except between Optima versions
    WARNING: Do not change the order of these lists without checking the potential consequences within the code"""

    def __init__(self, locale):
        self.locale = locale  # Store the locale for this settings instance

        _ = get_translator(locale)

        self.t = [2017, 2030]
        self.years = sc.inclusiverange(self.t[0], self.t[1])
        self.n_years = len(self.years)
        self.timestep = 1.0 / 12.0  # in months. WARNING do not change this, montly timestep is hardcoded as e.g. for month in range(12) elsewhere.
        self.stunting_list = [_("High"), _("Moderate"), _("Mild"), _("Normal")]
        self.stunted_list = self.stunting_list[:2]
        self.non_stunted_list = self.stunting_list[2:]
        self.anaemia_list = [_("Anaemic"), _("Not anaemic")]
        self.anaemic_list = self.anaemia_list[:1]
        self.non_anaemic_list = self.anaemia_list[1:]
        self.wasting_list = [_("SAM"), _("MAM"), _("Mild"), _("Normal")]
        self.wasted_list = self.wasting_list[:2]
        self.non_wasted_list = self.wasting_list[2:]
        self.bf_list = [_("Exclusive"), _("Predominant"), _("Partial"), _("None")]
        list_cats = [self.stunting_list, self.wasting_list, self.anaemia_list, self.bf_list]
        self.all_cats = list(itertools.product(*list_cats))
        self.n_cats = len(self.all_cats)
        self.correct_bf = {_("<1 month"): _("Exclusive"), _("1-5 months"): _("Exclusive"), _("6-11 months"): _("Partial"), _("12-23 months"): _("Partial"), _("24-59 months"): _("None")}
        self.optimal_space = _("24 months or greater")
        self.birth_outcomes = [_("Term AGA"), _("Term SGA"), _("Pre-term AGA"), _("Pre-term SGA")]
        self.global_eclampsia_prevalence = {"Pre-eclampsia": 0.046, "Eclampsia": 0.014}  # Need data/source, using https://www.ejog.org/article/S0301-2115(13)00196-6/fulltext
        self.all_risks = [self.stunting_list, self.wasting_list, self.bf_list, self.anaemia_list]
        self.child_ages = [_("<1 month"), _("1-5 months"), _("6-11 months"), _("12-23 months"), _("24-59 months")]
        self.pw_ages = [_("PW: 15-19 years"), _("PW: 20-29 years"), _("PW: 30-39 years"), _("PW: 40-49 years")]
        self.wra_ages = [_("WRA: 15-19 years"), _("WRA: 20-29 years"), _("WRA: 30-39 years"), _("WRA: 40-49 years")]
        self.all_ages = self.child_ages + self.pw_ages + self.wra_ages
        self.risks = [_("Stunting"), _("Wasting"), _("Breastfeeding"), _("Anaemia")]  # todo: even use this?
        self.child_age_spans = [1.0, 5.0, 6.0, 12.0, 36.0]  # in months
        self.women_age_rates = [1.0 / 5.0, 1.0 / 10.0, 1.0 / 10.0, 1.0 / 10.0]  # in years

        self.cost_types = {
            _("Linear (constant marginal cost) [default]"): "linear",
            _("Curved with increasing marginal cost"): "increasing",
            _("Curved with decreasing marginal cost"): "decreasing",
            _("S-shaped (decreasing then increasing marginal cost)"): "s-shaped",
        }

    def __repr__(self):
        output = sc.prepr(self)
        return output

    def __setstate__(self, d):
        self.__dict__ = d
        d = migrate(self)
        self.__dict__ = d.__dict__

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
