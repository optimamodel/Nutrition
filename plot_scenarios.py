
import output as output
import pickle as pickle
import data as dataCode

ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages, birthOutcomes, wastingList, stuntingList, breastfeedingList]
spreadsheetData = dataCode.getDataFromSpreadsheet('InputForCode.xlsx', keyList)

plotData = []
run=0

pickleFilename = 'testDefault.pkl'
nametag = "Baseline"
plotcolor = 'grey'
file3 = open(pickleFilename, 'rb')
test_p30 = []
while 1:
    try:
        test_p30.append(pickle.load(file3))
    except (EOFError):
        break
file3.close()
plotData.append({})
plotData[run]["modelList"] = test_p30
plotData[run]["tag"] = nametag
plotData[run]["color"] = plotcolor
run += 1

percentageIncrease = 90
for ichoose in range(len(spreadsheetData.interventionList)):
    chosenIntervention = spreadsheetData.interventionList[ichoose]
    pickleFilename = 'test_Intervention%i_P%i.pkl'%(ichoose,percentageIncrease)
    #nametag = chosenIntervention+": increase coverage by %g%% points"%(percentageIncrease)
    nametag = chosenIntervention
    print "\n"+nametag

    file3 = open(pickleFilename, 'rb')
    # read the model output with simple intervention
    test_p30 = []
    while 1:
        try:
            test_p30.append(pickle.load(file3))
        except (EOFError):
            break
    file3.close()
    plotData.append({})
    plotData[run]["modelList"] = test_p30
    plotData[run]["tag"] = nametag
    plotData[run]["color"] = (1.0-0.13*run, 1.0-0.3*abs(run-4), 0.0+0.13*run)
    run += 1

output.getCombinedPlots(run, plotData, save=True)
