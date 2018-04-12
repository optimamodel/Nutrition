# -*- coding: utf-8 -*-
"""
Created on Thu Nov 17 15:11:55 2016

@author: ruth
"""

from old_files import project

projectSpreadsheet = 'project_spreadsheets/test_national_project.xlsx'
thisProject = project.Project(projectSpreadsheet)
thisProject.runCascade()
thisProject.runSingleOptimisation()
thisProject.runSingleOptimisationCustomBudget(10000000)