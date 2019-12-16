import xlsxwriter as xw
from nutrition.results import run_analysis
import sciris as sc


time_trends = False
type = 'scaled up'
# initialise project

countries = ['China', 'North Korea', 'Cambodia', 'Indonesia', 'Laos', 'Malaysia', 'Maldives', 'Myanmar',
             'Philippines', 'Sri Lanka', 'Thailand', 'Timor-Leste', 'Vietnam', 'Fiji', 'Kiribati',
             'Federated States of Micronesia', 'Papua New Guinea', 'Samoa', 'Solomon Islands', 'Tonga', 'Vanuatu',
             'Armenia', 'Azerbaijan', 'Kazakhstan', 'Kyrgyzstan', 'Mongolia', 'Tajikistan', 'Turkmenistan',
             'Uzbekistan', 'Albania', 'Bosnia and Herzegovina', 'Bulgaria', 'Macedonia', 'Montenegro', 'Romania',
             'Serbia', 'Belarus', 'Moldova', 'Russian Federation', 'Ukraine', 'Belize', 'Cuba', 'Dominican Republic',
             'Grenada', 'Guyana', 'Haiti', 'Jamaica', 'Saint Lucia', 'Saint Vincent and the Grenadines', 'Suriname',
             'Bolivia', 'Ecuador', 'Peru', 'Colombia', 'Costa Rica', 'El Salvador', 'Guatemala', 'Honduras',
             'Nicaragua', 'Venezuela', 'Brazil', 'Paraguay', 'Algeria', 'Egypt', 'Iran', 'Iraq', 'Jordan', 'Lebanon',
             'Libya', 'Morocco', 'Palestine', 'Syria', 'Tunisia', 'Turkey', 'Yemen', 'Afghanistan', 'Bangladesh',
             'Bhutan', 'India', 'Nepal', 'Pakistan', 'Angola', 'Central African Republic', 'Congo',
             'Democratic Republic of the Congo', 'Equatorial Guinea', 'Gabon', 'Burundi', 'Comoros', 'Djibouti',
             'Ethiopia', 'Kenya', 'Madagascar', 'Malawi', 'Mauritius', 'Mozambique', 'Rwanda', 'Somalia', 'Tanzania',
             'Uganda', 'Zambia', 'Botswana', 'Lesotho', 'Namibia', 'South Africa', 'Eswatini', 'Zimbabwe', 'Benin',
             'Burkina Faso', 'Cameroon', 'Cape Verde', 'Chad', 'Cote dIvoire', 'The Gambia', 'Ghana', 'Guinea',
             'Guinea-Bissau', 'Liberia', 'Mali', 'Mauritania', 'Niger', 'Nigeria', 'Sao Tome and Principe', 'Senegal',
             'Sierra Leone', 'Togo', 'Georgia', 'South Sudan', 'Sudan']

CE_data = sc.odict()
# run simulation for each country
for country in countries[:5]:
    CE_data.append(country, run_analysis(country))
print(CE_data)

CE_book = xw.Workbook('Country_CE_serial15082019.xlsx')
CE_sheet = CE_book.add_worksheet()
row = 0
column = 0

for country in CE_data.keys():
    CE_sheet.write(row, column, country)
    row += 1
    column += 1
    for o, objective in enumerate(['stunting', 'wasting', 'anaemia', 'mortality']):
        CE_sheet.write(row, column, objective)
        row += 1
        column += 1
        for m, measure in enumerate(['Cost effectiveness', 'Cost', 'Impact', 'Program']):
            CE_sheet.write(row, column, measure)
            column += 1
            if CE_data[country][o][m]:
                if measure == 'Cost':
                    CE_sheet.write(row, column, 0)
                    column += 1
                    for e, element in enumerate(CE_data[country][o][m]):
                        if e == 0:
                            CE_sheet.write(row, column, CE_data[country][o][m][e])
                            column += 1
                        else:
                            CE_sheet.write(row, column, sum(CE_data[country][o][m][:e+1]))
                            column += 1
                    row += 1
                    column -= e + 3
                elif measure == 'Impact':
                    CE_sheet.write(row, column, 0)
                    column += 1
                    CE_sheet.write_row(row, column, CE_data[country][o][m])
                    row += 1
                    column -= 2
                else:
                    CE_sheet.write(row, column, "")
                    column += 1
                    CE_sheet.write_row(row, column, CE_data[country][o][m])
                    row += 1
                    column -= 2
            else:
                CE_sheet.write(row, column, "")
                row += 1
                column -= 1
        column -= 1
    column -= 1
CE_book.close()
print('Finished!')







