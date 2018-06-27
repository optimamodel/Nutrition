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
    if 'prevs' in toplot: # WARNING, Does not work for OptimResult
        prevfigs = plot_prevs(all_res)
        allplots.update(prevfigs)
    if 'outputs' in toplot: # WARNING, Does not work for OptimResult
        outfigs = plot_outputs(all_res)
        allplots.update(outfigs)
    if 'alloc' in toplot: # optimized allocations
        try:
            bars = plot_alloc(all_res)
            allplots.update(bars)
        except Exception as E:
            print('WARNING, could not plot allocation: %s' % repr(E))
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
    width = 0.1
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
            years = res.year_names
            output = res.get_outputs([outcome], seq=True)[0]
            thismax = max(output)
            if thismax > ymax:
                ymax = thismax
            bar = row.bar([year + offset for year in years], output, width=width)
            offset += width
            bars.append(bar)
        row.set_ylim([0, ymax + ymax*.1])
        pl.xticks([year + width for year in years], years)
        pl.legend(bars, [res.name for res in all_res], loc='right', ncol=1)
        pl.xlabel('Years')
        pl.title('Annual outcomes')
        figs['outputs_%0i'%i] = fig
    return figs

# TODO: want to compare the total outcomes across scenarios

def plot_alloc(all_res):
    """ Plot the program allocations from an optimization, alongside current allocation """
    # TODO: WARNING: Cannot plot multiple objectives. Would like Optim to only take 1 objective each, then this will be resolved.
#    if len(all_res)>1:
#        print('WARNING, not currently enabled to plot more than one allocation, you have asked for %s' % len(all_res))
    res = all_res[0]
    xlabs = ['current'] + res.mults
    x = np.arange(len(xlabs))
    width = 0.35
    allocs = [res.curr_alloc] + res.optim_allocs
    figs = sc.odict()
    all_y = []
    bottom = np.zeros(len(xlabs))
    for i, prog in enumerate(res.programs):
        y = []
        # get allocation for each multiple
        for j, mult in enumerate(xlabs):
            alloc = allocs[j]
            y = np.append(y, alloc[i])
        all_y.append(y)
        fig = pl.bar(x, all_y[i], width=width, bottom=bottom)
        
        bottom += all_y[i]
        pl.ylabel('Funding')
        pl.xticks(x, xlabs)
        legendart = [p[0] for p in figs.values()]
        legendlab = [prog.name for prog in res.programs]
        pl.legend(legendart, legendlab)
        figs['alloc_%0i'%i] = fig
    return figs

def round_elements(mylist, dec=1):
    return [round(np.float64(x) * 100, dec) for x in mylist] # Type conversion to handle None

















