# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 13:38:11 2016

@author: ruth
"""
from numpy import array
import pickle as pickle
filename = 'Bangladesh_full_cascade_dictionary_deaths.pkl'
infile = open(filename, 'rb')

cascade = []
while 1:
    try:
        cascade.append(pickle.load(infile))
    except (EOFError):
        break
infile.close()


cascade =  [{0.25: {u'Balanced energy supplementation': array([  4.89774724e-10]),
   u'Breastfeeding promotion (dual delivery)': array([ 6503801.51498762]),
   u'Complementary feeding (education)': array([  3.58494939e-08]),
   u'Complementary feeding (supplementation)': array([  7.25377710e-09]),
   u'Multiple micronutrient supplementation': array([  1.10647804e-08]),
   u'Vitamin A supplementation': array([  8.32540340e-11]),
   u'Zinc supplementation': array([  1.08465543e-08])},
  0.5: {u'Balanced energy supplementation': array([ 4320.8305067]),
   u'Breastfeeding promotion (dual delivery)': array([ 12737626.17914143]),
   u'Complementary feeding (education)': array([ 35.29045206]),
   u'Complementary feeding (supplementation)': array([  1.27869604e-12]),
   u'Multiple micronutrient supplementation': array([ 263950.5278935]),
   u'Vitamin A supplementation': array([ 1670.20198169]),
   u'Zinc supplementation': array([ 0.])},
  0.75: {u'Balanced energy supplementation': array([ 6342.78916847]),
   u'Breastfeeding promotion (dual delivery)': array([ 14982460.30663345]),
   u'Complementary feeding (education)': array([ 5383.18133137]),
   u'Complementary feeding (supplementation)': array([ 0.]),
   u'Multiple micronutrient supplementation': array([ 2938074.33266951]),
   u'Vitamin A supplementation': array([ 1571279.00135529]),
   u'Zinc supplementation': array([ 7864.93380497])},
  1.0: {u'Balanced energy supplementation': array([ 2466.37281952]),
   u'Breastfeeding promotion (dual delivery)': array([ 18478695.88869058]),
   u'Complementary feeding (education)': array([ 42975.10301093]),
   u'Complementary feeding (supplementation)': array([  6.64496909e-11]),
   u'Multiple micronutrient supplementation': array([ 4979939.78883011]),
   u'Vitamin A supplementation': array([ 2511128.90659961]),
   u'Zinc supplementation': array([ 0.])},
  1.5: {u'Balanced energy supplementation': array([ 3620.44746446]),
   u'Breastfeeding promotion (dual delivery)': array([ 23140550.27733861]),
   u'Complementary feeding (education)': array([ 6141098.20999375]),
   u'Complementary feeding (supplementation)': array([ 0.]),
   u'Multiple micronutrient supplementation': array([ 6217909.53706571]),
   u'Vitamin A supplementation': array([ 3519630.61806359]),
   u'Zinc supplementation': array([  5.93423583e-11])},
  2.0: {u'Balanced energy supplementation': array([ 38323.44209328]),
   u'Breastfeeding promotion (dual delivery)': array([ 27923967.52145288]),
   u'Complementary feeding (education)': array([ 11654834.85857537]),
   u'Complementary feeding (supplementation)': array([  1.68917515e-10]),
   u'Multiple micronutrient supplementation': array([ 7896385.7065184]),
   u'Vitamin A supplementation': array([ 4516900.59126158]),
   u'Zinc supplementation': array([  4.22293786e-10])},
  3.0: {u'Balanced energy supplementation': array([ 0.]),
   u'Breastfeeding promotion (dual delivery)': array([ 37218506.87544007]),
   u'Complementary feeding (education)': array([ 19679109.90559045]),
   u'Complementary feeding (supplementation)': array([  1.41623997e-10]),
   u'Multiple micronutrient supplementation': array([ 11134188.27835392]),
   u'Vitamin A supplementation': array([ 6348606.20072219]),
   u'Zinc supplementation': array([ 3665206.91974563])},
  4.0: {u'Balanced energy supplementation': array([ 0.]),
   u'Breastfeeding promotion (dual delivery)': array([ 38765817.070614]),
   u'Complementary feeding (education)': array([ 20580878.27930436]),
   u'Complementary feeding (supplementation)': array([ 0.]),
   u'Multiple micronutrient supplementation': array([ 11513992.1703326]),
   u'Vitamin A supplementation': array([ 6695613.72933129]),
   u'Zinc supplementation': array([ 26504522.99022076])}}]