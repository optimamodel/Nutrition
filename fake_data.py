# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 15:57:07 2016

@author: ruth
"""


mortalityRateByAgeGroup = [22, 35, 35, 35, 49]



causes = ["diarrhea", "malaria"]
ages = ["0-1 month", "1-6 months", "6-12 months", "12-24 months", "24-59 months"]

#causes of death are percent
causeOfDeathbyAge = {"diarrhea":{"0-1 month":0.4, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1}, "malaria":{"0-1 month":0.2, "1-6 months":0.2, "6-12 months":0.2, "12-24 months":0.2, "24-59 months":0.2}}

RRStuntingDiarrhea = {"normal":{"0-1 month":0.1, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1},
                      "mild":{"0-1 month":0.1, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1},
                      "moderate":{"0-1 month":0.1, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1},
                      "high":{"0-1 month":0.1, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1} }

RRStuntingMalaria = {"normal":{"0-1 month":0.1, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1},
                      "mild":{"0-1 month":0.1, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1},
                      "moderate":{"0-1 month":0.1, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1},
                      "high":{"0-1 month":0.1, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1} }

RRStunting = {"diarrhea":RRStuntingDiarrhea, "malaria":RRStuntingMalaria}
RRWasting = {"diarrhea":RRStuntingDiarrhea, "malaria":RRStuntingMalaria} #this is just the same as stunting for now