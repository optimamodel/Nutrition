# -*- coding: utf-8 -*-
"""
Created on Thu Nov 17 15:11:55 2016

@author: ruth
"""

import project
projectSpreadsheet = 'project_spreadsheets/test_national_project.xlsx'
thisProject = project.Project(projectSpreadsheet)
thisProject.runCascade()