import pylab as pl
import numpy as np
import matplotlib.ticker as tk
import sciris.core as sc

def make_plots(all_res=None, toplot=None, optim=False):
    """ res is a ScenResult or Result object (could be a list of these objects) from which all information can be extracted """
    ## Initialize
    allplots = sc.odict()
    if toplot is None:
        toplot = ['prevs', 'outputs', 'comp']
        if optim:
            toplot.append('alloc')
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
    if 'comp' in toplot:
        compfigs = compare_outputs(all_res)
        allplots.update(compfigs)
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
            if thismax > ymax: ymax = thismax
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
            if thismax > ymax: ymax = thismax
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

def compare_outputs(all_res):
    """ Compare the results of multiple scenarios. These are aggregate values """
    figs = sc.odict()
    outcomes = ['thrive', 'child_deaths']
    ind = np.arange(len(outcomes))
    fig = pl.figure()
    row = fig.add_subplot(111)
    ymax = 0
    ymin = 0
    width = 0.35
    offset = -width
    base_res = all_res[0] # assumes baseline included
    baseline = base_res.get_outputs(outcomes, seq=False)
    bars = []
    for res in all_res[1:]:
        offset += width
        output = res.get_outputs(outcomes, seq=False)
        perc_change = [(out - base)/base for out,base in zip(output, baseline)]
        perc_change = round_elements(perc_change, dec=2)
        bar = row.bar(ind+offset, perc_change, width=width)
        thismax = max(perc_change)
        thismin = min(perc_change)
        if thismax>ymax:ymax = thismax
        if thismin<ymin:ymin = thismin
        bars.append(bar)
    row.set_ylim([min(ymin+ymin*.1,0), ymax+ymax*.1])
    pl.xticks(ind+offset/2, outcomes)
    pl.legend(bars, [res.name for res in all_res[1:]], loc='right', ncol=1)
    pl.xlabel('Outcomes')
    pl.ylabel('Change (%)')
    pl.title('Percentage change from baseline')
    figs['comp'] = fig
    return figs

def plot_alloc(all_res):
    """ Plot the program allocations from an optimization, alongside baseline allocation.
     Note that scenarios not generated from optimization cannot be plotted using this function,
     as assumed structure for spending is different """
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
            pos = res.mult if res.mult else res.name
            xlabs.append(pos)
            alloc = res.programs[i].annual_spend[1] # spending is same after first year in optimization
            y = np.append(y, alloc)
        pl.bar(x, y, width=width, bottom=bottom)
        bottom += y
    ymax = max(bottom)
    pl.title(ref.obj)
    pl.xticks(x, xlabs)
    pl.ylim((0, ymax+ymax*.1))
    pl.ylabel('Funding')
    pl.xlabel('Multiples of flexible funding')
    leglab = [prog.name for prog in res.programs]
    pl.legend(leglab)
    figs['alloc'] = fig
    return figs

def round_elements(mylist, dec=1):
    return [round(np.float64(x) * 100, dec) for x in mylist] # Type conversion to handle None

















