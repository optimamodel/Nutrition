import pylab as pl
import numpy as np
import matplotlib.ticker as tk
import sciris.core as sc

def make_plots(all_res=None, toplot=None):
    """ res is a ScenResult or Result object (could be a list of these objects) from which all information can be extracted """
    ## Initialize
    allplots = sc.odict()
    if toplot is None: toplot = ['prevs', 'outputs', 'alloc']
    if all_res is None or all_res == []:
        print('WARNING, no results selected to plot')
        return allplots
    
    toplot = sc.promotetolist(toplot)
    all_res = sc.promotetolist(all_res)
    if 'prevs' in toplot:
        prevfigs = plot_prevs(all_res)
        allplots.update(prevfigs)
    if 'outputs' in toplot:
        outfigs = plot_outputs(all_res)
        allplots.update(outfigs)
    if 'alloc' in toplot: # optimized allocations
        outfigs = plot_alloc(all_res)
        allplots.update(outfigs)
#        try:
#            
#        except Exception as E:
#            print('WARNING, could not plot allocation: %s' % repr(E))
    return allplots


def plot_prevs(all_res):
    """ Plot prevs for each scenario"""
    allattr = all_res[0].model_attr()
    prevs = [attr for attr in allattr if 'prev' in attr]
    
    lines = []
    figs = sc.odict()
    for i in range(len(prevs)):
        fig = pl.figure()
        row = fig.add_subplot(111)
        #settings
        row.yaxis.set_major_formatter(tk.FormatStrFormatter('%.1f'))
        label = prevs[i]
        row.set_ylabel('{} (%)'.format(label))
        ymax = 0
        leglabels = []
        # plot results
        for res in all_res:
            years = res.year_names
            output = res.get_outputs([label], seq=True)[0]
            out = round_elements(output, dec=1)
            thismax = max(out)
            if thismax > ymax:
                ymax = thismax
            line, = row.plot(years, out)
            lines.append(line)
            leglabels.append(res.name)
        row.set_ylim([0, ymax + ymax*0.1])
        pl.xlabel('Years')
        pl.title('Risk prevalences')
        pl.legend(lines, [res.name for res in all_res], loc='right', ncol=1)
        figs['prevs_%0i'%i] = fig
    
    return figs

def plot_outputs(all_res):
    outcomes = ['thrive', 'child_deaths']
    width = 0.15
    bars = []
    figs = sc.odict()
    for i in range(len(outcomes)):
        fig = pl.figure()
        row = fig.add_subplot(111)
        ymax = 0
        offset = 0
        outcome = outcomes[i]
        row.set_ylabel(outcome)
        for res in all_res:
            years = np.array(res.year_names)
            output = res.get_outputs([outcome], seq=True)[0]
            thismax = max(output)
            if thismax > ymax:
                ymax = thismax
            bar = row.bar(years+offset, output, width=width)
            offset += width
            bars.append(bar)
        offset -= width
        row.set_ylim([0, ymax + ymax*.1])
        pl.xticks(years+offset/2, years)
        pl.legend(bars, [res.name for res in all_res], loc='right', ncol=1)
        pl.xlabel('Years')
        pl.title('Annual outcomes')
        figs['outputs_%0i'%i] = fig
    return figs

# TODO: want to compare the total outcomes across scenarios

def plot_alloc(all_res):
    """ Plot the program allocations from an optimization, alongside current allocation """
    #initialize
    width = 0.35
    fig = pl.figure()
    figs = sc.odict()
    try: ref=all_res[1]
    except IndexError: ref = all_res[0] # baseline
    x = np.arange(len(all_res))
    xlabs = []
    bottom = np.zeros(len(all_res))
    for i, prog in enumerate(ref.programs):
        y = []
        # get allocation for each multiple
        for j, res in enumerate(all_res):
            xlabs.append(res.mult)
            alloc = res.programs[i].annual_spend[1] # spending is same after first year in optimization
            y = np.append(y, alloc)
        pl.bar(x, y, width=width, bottom=bottom)
        bottom += y
    pl.title(ref.obj)
    pl.xticks(x, xlabs)
    pl.ylabel('Funding')
    pl.xlabel('Multiples of flexible funding')
    leglab = [prog.name for prog in res.programs]
    pl.legend(leglab)
    figs['alloc_%0i'%i] = fig
    return figs

def round_elements(mylist, dec=1):
    return [round(np.float64(x) * 100, dec) for x in mylist] # Type conversion to handle None

















