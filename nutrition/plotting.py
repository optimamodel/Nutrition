import pylab as pl
import numpy as np
import scipy.interpolate
import sciris as sc
from . import utils

# Choose where the legend appears: outside right or inside right
for_frontend = True
if for_frontend:
    legend_loc =      {'bbox_to_anchor':(1.0,1.0)}
    fig_size = (8,3)
    ax_size = [0.2,0.18,0.40,0.72]
else:
    legend_loc = {'loc':'right'}
    ax_size = [0.2,0.10,0.65,0.75]


def make_plots(all_res=None, toplot=None, optim=False):
    """ res is a ScenResult or Result object (could be a list of these objects) from which all information can be extracted """
    ## Initialize
    allplots = sc.odict()
    if toplot is None:
        toplot = ['prevs', 'ann', 'agg', 'alloc']
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
        outfigs = plot_alloc(all_res, optim=optim)
        allplots.update(outfigs)
    return allplots

def plot_prevs(all_res):
    """ Plot prevs for each scenario"""
    prevs = utils.default_trackers(prev=True, rate=False)
    lines = []
    figs = sc.odict()
    for i, prev in enumerate(prevs):
        fig = pl.figure(figsize=fig_size)
        ax = fig.add_axes(ax_size)
        ymax = 0
        leglabels = []
        # plot results
        for res in all_res:
            years = res.years
            out = res.get_outputs([prev], seq=True)[0]
            f = scipy.interpolate.PchipInterpolator(years, out, extrapolate=False)
            newx = np.linspace(years[0], years[-1], len(years)*10)
            out = f(newx) * 100
            thismax = max(out)
            if thismax > ymax: ymax = thismax
            line, = ax.plot(newx, out)
            lines.append(line)
            leglabels.append(res.name)
        # formatting
        sc.SIticks(ax=ax, axis='y')
#        ax.set_ylabel('Percentage') # Shown as tick labels
        ax.set_ylim([0, ymax + ymax*0.1])
        ax.set_xlabel('Years')
        ax.set_title(utils.relabel(prev))
        ax.legend(lines, [res.name for res in all_res], **legend_loc)
        figs['prevs_%0i'%i] = fig
    return figs

def plot_outputs(all_res, seq, name):
    outcomes = utils.default_trackers(prev=False, rate=False)
    width = 0.15 if seq else 0.35
    figs = sc.odict()
    scale = 1e1 # scales for formatting
    baseres = all_res[0]
    years = np.array(baseres.years) # assume these scenarios over same time horizon
    for i, outcome in enumerate(outcomes):
        fig = pl.figure(figsize=fig_size)
        ax = fig.add_axes(ax_size)
        ymax = 0
        perchange = []
        bars = []
        baseout = baseres.get_outputs(outcome, seq=seq)[0] / scale
        if not isinstance(baseout, np.ndarray): baseout = [baseout]
        offsets = np.arange(len(all_res)+1)*width # Calculate offset so tick is in the center of the bars
        offsets -= offsets.mean() - 0.5*width
        for r,res in enumerate(all_res):
            offset = offsets[r]
            xpos = years + offset if seq else offset
            output = res.get_outputs(outcome, seq=seq)[0] / scale
            if not isinstance(output, np.ndarray): output = [output]
            thimax = max(output)
            if thimax > ymax: ymax = thimax
            change = round_elements([utils.get_change(base, out) for out,base in zip(output, baseout)], dec=1)
            perchange.append(change)
            bar = ax.bar(xpos, output, width=width)
            bars.append(bar)
        if seq:
            ax.set_xlabel('Years')
            title = 'Annual'
        else:
            title = 'Cumulative'
            ax.set_xticks([])
            # display percentage change above bars
            for j, bar in enumerate(bars[1:],1):
                for k, rect in enumerate(bar):
                    change = perchange[j][k]
                    height = rect.get_height()
                    ax.text(rect.get_x() + rect.get_width() / 2., height,'{}%'.format(change), ha='center',
                                va='bottom')
        # formatting
        title += ' %s \n %s-%s'%(utils.relabel(outcome).lower(), baseres.years[0], baseres.years[-1])
        sc.SIticks(ax=ax, axis='y')
        ax.set_ylim([0, ymax + ymax * .1])
        ax.set_ylabel('Number')
        ax.legend(bars, [res.name for res in all_res], ncol=1, **legend_loc)
        ax.set_title(title)
        figs['%s_out_%0i'%(name, i)] = fig
    return figs

def plot_alloc(results, optim):
    """ Plots the average annual spending for each scenario, coloured by program.
    Legend will include all programs in the 'baseline' allocation which receive non-zero spending """
    #initialize
    width = 0.35
    fig = pl.figure(figsize=fig_size)
    ax = fig.add_axes(ax_size)
    figs = sc.odict()
    ref = results[0]
    progset = ref.prog_info.base_progset()
    colors = sc.gridcolors(ncolors=len(progset))
    leglabs = []
    x = np.arange(len(results))
    # group allocations by program
    avspend = []
    for prog in progset:
        thisprog = np.zeros(len(results))
        for i, res in enumerate(results):
            alloc = res.get_allocs(ref=False) # slightly inefficient to do this for every program
            try:
                progav = alloc[prog][1:].mean()
            except: # program not in scenario program set
                progav = 0

            thisprog[i] = progav
        avspend.append(thisprog)
    # make bar plots
    bars = []
    xlabs = [res.mult if res.mult else res.name for res in results]
    bottom = np.zeros(len(results))
    for i, spend in enumerate(avspend):
        if any(spend) > 0:    # only want to plot prog if spending is non-zero (solves legend issues)
            leglabs.append(progset[i])
            bar = ax.bar(x, spend, width=width, bottom=bottom, color=colors[i])
            bars.append(bar)
            bottom += spend
    ymax = max(bottom)
    if optim:
        title = 'Optimal allocation, %s-%s'% (ref.years[0], ref.years[-1])
        valuestr = str(results[1].prog_info.free / 1e6) # bit of a hack
        # format x axis
        if valuestr[1] == '.':
            valuestr = valuestr[:3]
        else:
            valuestr = valuestr[:2]
        xlab = 'Total available budget (relative to US$%sM)' % valuestr
    else:
        title = 'Average annual spending, %s-%s' % (ref.years[0], ref.years[-1])
        xlab = 'Scenario'
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(xlabs)
    ax.set_xlabel(xlab)
    ax.set_ylim((0, ymax+ymax*.1))
    ax.set_ylabel('Spending (US$)')
    sc.SIticks(ax=ax, axis='y')
    nprogs = len(leglabs)
    labelspacing = 0.1
    columnspacing = 0.1
    fontsize = None
    ncol = 1
    if nprogs>10:
        fontsize = 8
    if nprogs>12:
        fontsize = 6
    if nprogs>24:
        ncol = 2
    customizations = {'fontsize':fontsize, 'labelspacing':labelspacing, 'ncol':ncol, 'columnspacing':columnspacing}
    customizations.update(legend_loc)
    ax.legend(bars, leglabs, **customizations)
    figs['alloc'] = fig
    return figs

def get_costeff(parents, children, baselines):
    """
    Calculates the cost per impact of a scenario.
    (Total money spent on all programs (baseline + new) ) / (scneario outcome - zero cov outcome)
    :return: 3 levels of nested odicts, with keys (scen name, child name, pretty outcome) and value of type string
    """
    outcomes = utils.default_trackers(prev=False, rate=False)
    pretty = utils.relabel(outcomes)
    costeff = sc.odict()
    for i, parent in enumerate(parents):
        baseline = baselines[i]
        costeff[parent.name] = sc.odict()
        par_outs = parent.get_outputs(outcomes)
        allocs = parent.get_allocs(ref=False)
        baseallocs = baseline.get_allocs(ref=False)
        filteredbase = sc.odict({prog:spend for prog, spend in baseallocs.iteritems() if prog not in allocs})
        totalspend = allocs[:].sum() + filteredbase[:].sum()
        thesechildren = children[parent.name]
        for j, child in enumerate(thesechildren):
            if j > 0: # i.e. scenarios with individual scale-downs
                # only want spending on individual program in parent scen
                progspend = allocs[child.name]
                totalspend = sum(progspend)
            costeff[parent.name][child.name] = sc.odict()
            child_outs = child.get_outputs(outcomes)
            for k, out in enumerate(outcomes):
                impact = par_outs[k] - child_outs[k]
                if abs(impact) < 1e-3:
                    costimpact = 'No impact'
                else:
                    costimpact = totalspend / impact
                    costimpact = round(costimpact, 2)
                    # format
                    if out == 'thrive': # thrive should increase
                        if costimpact < 0:
                            costimpact = 'Negative impact'
                        else:
                            costimpact = '$%s per additional case' % format(costimpact, ',')
                    else: # all other outcomes should be negative
                        if costimpact > 0:
                            costimpact = 'Negative impact'
                        else:
                            costimpact = '$%s per case averted' % format(-costimpact, ',')
                costeff[parent.name][child.name][pretty[k]] = costimpact
    return costeff

def round_elements(mylist, dec=1):
    return [round(np.float64(x) * 100, dec) for x in mylist] # Type conversion to handle None
