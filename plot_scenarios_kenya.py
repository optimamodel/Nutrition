
import output as output
import pickle as pickle
import data as dataCode

ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages, birthOutcomes, wastingList, stuntingList, breastfeedingList]
spreadsheetData = dataCode.getDataFromSpreadsheet('InputForCode_Kenya.xlsx', keyList)

plotData = []
run=0

pickleFilename = 'testDefault.pkl'
nametag = "Baseline"
plotcolor = 'grey'
file = open(pickleFilename, 'rb')
modelList = []
while 1:
    try:
        modelList.append(pickle.load(file))
    except (EOFError):
        break
file.close()
plotData.append({})
plotData[run]["modelList"] = modelList
plotData[run]["tag"] = nametag
plotData[run]["color"] = plotcolor
run += 1

percentageIncrease = 50
for ichoose in range(len(spreadsheetData.interventionList)):
    chosenIntervention = spreadsheetData.interventionList[ichoose]
    pickleFilename = 'test_Intervention%i_P%i.pkl'%(ichoose,percentageIncrease)
    nametag = chosenIntervention
    print "\n"+nametag

    fileX = open(pickleFilename, 'rb')
    # read the model output with simple intervention
    modelXList = []
    while 1:
        try:
            modelXList.append(pickle.load(fileX))
        except (EOFError):
            break
    fileX.close()
    plotData.append({})
    plotData[run]["modelList"] = modelXList
    plotData[run]["tag"] = nametag
    plotData[run]["color"] = (1.0-0.13*run, 1.0-0.3*abs(run-4), 0.0+0.13*run)
    run += 1

output.getCombinedPlots(run, plotData, save=True)
