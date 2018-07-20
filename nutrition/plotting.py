import pylab as pl
import numpy as np
import matplotlib.ticker as tk
import sciris.core as sc
import utils
import scipy.interpolate

def make_plots(all_res=None, toplot=None, optim=False):
    """ res is a ScenResult or Result object (could be a list of these objects) from which all information can be extracted """
    ## Initialize
    allplots = sc.odict()
    if toplot is None:
        toplot = ['prevs', 'ann', 'agg']
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
    if 'ann' in toplot:
        outfigs = plot_outputs(all_res, True, 'ann')
        allplots.update(outfigs)
    if 'agg' in toplot:
        outfigs = plot_outputs(all_res, False, 'agg')
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
    for i, prev in enumerate(prevs):
        fig = pl.figure()
        ax = fig.add_subplot(111)
        ymax = 0
        leglabels = []
        # plot results
        for res in all_res:
            years = res.years
            out = res.get_outputs([prev], seq=True)[0]
            # out = round_elements(output, dec=1)
            f = scipy.interpolate.PchipInterpolator(years, out, extrapolate=False)
            newx = np.linspace(years[0], years[-1], len(years)*10)
            out = f(newx) * 100
            thismax = max(out)
            if thismax > ymax: ymax = thismax
            line, = ax.plot(newx, out)
            lines.append(line)
            leglabels.append(res.name)
        # formatting
        ax.yaxis.set_major_formatter(tk.FormatStrFormatter('%.1f'))
        ax.set_ylabel('{} (%)'.format(prev))
        ax.set_ylim([0, ymax + ymax*0.1])
        ax.set_xlabel('Years')
        ax.set_title('Risk prevalences')
        ax.legend(lines, [res.name for res in all_res], loc='right', ncol=1)
        figs['prevs_%0i'%i] = fig
    return figs

def plot_outputs(all_res, seq, name):
    outcomes = ['thrive', 'child_deaths']
    width = 0.15 if seq else 0.35
    figs = sc.odict()
    baseres = all_res[0]
    years = np.array(baseres.years) # assume these scenarios over same time horizon
    for i, outcome in enumerate(outcomes):
        fig = pl.figure()
        ax = fig.add_subplot(111)
        ymax = 0
        perchange = []
        bars = []
        offset = -width
        baseout = baseres.get_outputs(outcome, seq=seq)[0]
        for res in all_res:
            offset += width
            xpos = np.array(res.years) + offset if seq else offset
            output = res.get_outputs(outcome, seq=seq)[0]
            thimax = max(output)
            if thimax > ymax: ymax = thimax
            change = round_elements([utils.get_change(base, out) for out,base in zip(output, baseout)], dec=1)
            perchange.append(change)
            bar = ax.bar(xpos, output, width=width)
            bars.append(bar)
        if seq:
            ax.set_xticks(years+offset/2.)
            ax.set_xticklabels(years)
        else:
            ax.set_xticks([])
            # display percentage change
            for j, bar in enumerate(bars[1:],1):
                for k, rect in enumerate(bar):
                    change = perchange[j][k]
                    height = rect.get_height()
                    ax.text(rect.get_x() + rect.get_width() / 2., height,'{}%'.format(change), ha='center',
                                va='bottom')
        # formatting
        ax.set_ylim([0, ymax + ymax * .1])
        ax.set_ylabel(outcome)
        ax.legend(bars, [res.name for res in all_res], loc='right', ncol=1)
        ax.set_title(outcome)
        figs['%s_out_%0i'%(name, i)] = fig
    return figs

def plot_alloc(all_res):
    """ Plot the program allocations from an optimization, alongside baseline allocation.
     Note that scenarios not generated from optimization cannot be plotted using this function,
     as assumed structure for spending is different """
    #initialize
    width = 0.35
    fig = pl.figure()
    ax = fig.add_subplot(111)
    figs = sc.odict()
    try:
        ref = all_res[1]
        ref_spend = ref.prog_info.refs # adjust for reference spending
    except IndexError:
        ref = all_res[0] # baseline
        ref_spend = [0 for i in ref.programs] # don't adjust if only baseline
    x = np.arange(len(all_res))
    xlabs = []
    bars = []
    bottom = np.zeros(len(all_res))
    for i, prog in enumerate(ref.programs):
        y = []
        # get allocation for each multiple
        for j, res in enumerate(all_res):
            pos = res.mult if res.mult else res.name
            xlabs.append(pos)
            # adjust spending so does not display reference spending
            alloc = res.programs[i].annual_spend[1] - ref_spend[i] # spending is same after first year in optimization
            y = np.append(y, alloc)
        bar = ax.bar(x, y, width=width, bottom=bottom)
        bars.append(bar)
        bottom += y
    ymax = max(bottom)
    # formatting
    ax.set_title(ref.obj)
    ax.set_xticks(x)
    ax.set_xticklabels(xlabs)
    ax.set_ylim((0, ymax+ymax*.1))
    ax.set_ylabel('Funding')
    ax.set_xlabel('Multiple of flexible funding')
    ax.legend(bars, [prog.name for prog in ref.programs])
    figs['alloc'] = fig
    return figs

def round_elements(mylist, dec=1):
    return [round(np.float64(x) * 100, dec) for x in mylist] # Type conversion to handle None













