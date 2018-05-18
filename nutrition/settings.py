"""
SETTINGS

Store all the statis data for a project that won't change except between Optima versions

"""

class Settings(object):
    def __init__(self):
        self.timestep = 1./12. # in months
        self.stunting_list = ['High', 'Moderate', 'Mild', 'Normal']
        self.stunted_list = self.stunting_list[:2]
        self.non_stunted_list = self.stunting_list[:2]
        self.anaemia_list = ['Anaemic', 'Not anaemic']
        self.anaemic_list = self.anaemia_list[:1]
        self.non_anaemic_list = self.anaemia_list[:1]
        self.wasting_list = ['SAM', 'MAM', 'Mild', 'Normal']
        self.wasted_list = self.wasting_list[:2]
        self.non_wasted_list = self.wasting_list[2:]
        self.bf_list = ['exclusive', 'predominant', 'partial', 'none']
        self.correct_bf = {'<1 month': 'exclusive', '1-5 months': 'exclusive', '6-11 months':'partial',
                           '12-23 months': 'partial', '24-59 months': 'none'}
        self.birth_outcomes = ['Term AGA', 'Term SGA', 'Pre-term AGA','Pre-term SGA']
        self.all_risks = [self.stunting_list, self.wasting_list, self.bf_list, self.anaemia_list]
        self.child_ages = ['<1 month', '1-5 months', '6-11 months', '12-23 months', '24-59 months']
        self.pw_ages = ['PW: 15-19 years', 'PW: 20-29 years', 'PW: 30-39 years', 'PW: 40-49 years']
        self.wra_ages = ['WRA: 15-19 years', 'WRA: 20-29 years', 'WRA: 30-39 years', 'WRA: 40-49 years']
        self.all_ages = self.child_ages + self.pw_ages + self.wra_ages
        self.risks = ['Stunting', 'Wasting', 'Breastfeeding', 'Anaemia']
        self.child_age_spans = [1., 5., 6., 12., 36.] # in months
        self.women_age_rates = [1./5., 1./10., 1./10., 1./10.] # in years
