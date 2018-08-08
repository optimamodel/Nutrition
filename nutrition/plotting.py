import pylab as pl
import numpy as np
import sciris.core as sc
import utils
import scipy.interpolate

# Choose where the legend appears: outside right or inside right
for_frontend = True
if for_frontend:
    legend_loc = {'bbox_to_anchor':(1,1.0)}
    legend_loc_prev = {'loc':'best'} # No idea why this has to be different, but it does
    fig_size = (8,3)
    ax_size = [0.2,0.12,0.40,0.75]
else:
    legend_loc = {'loc':'right'}
    ax_size = [0.2,0.10,0.65,0.75]


def make_plots(all_res=None, toplot=None, optim=False):
    """ res is a ScenResult or Result object (could be a list of these objects) from which all information can be extracted """
    ## Initialize
    allplots = sc.odict()
    if toplot is None:
        toplot = ['prevs', 'ann', 'agg']
        if optim:
            toplot.append('alloc')
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
    return allplots

def plot_prevs(all_res):
    """ Plot prevs for each scenario"""
    allattr = all_res[0].model_attr()
    prevs = [attr for attr in allattr if 'prev' in attr]
    
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
        ax.legend(lines, [res.name for res in all_res], **legend_loc_prev)
        figs['prevs_%0i'%i] = fig
    return figs

def plot_outputs(all_res, seq, name):
    outcomes = ['thrive', 'child_deaths']
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
        offset = -width
        baseout = baseres.get_outputs(outcome, seq=seq)[0] / scale
        offsets = np.arange(len(all_res)+1)*width # Calculate offset so tick is in the center of the bars
        offsets -= offsets.mean() - 0.5*width
        for r,res in enumerate(all_res):
            offset = offsets[r]
            xpos = years + offset if seq else offset
            output = res.get_outputs(outcome, seq=seq)[0] / scale
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

def plot_alloc(all_res):
    """ Plot the program allocations from an optimization, alongside baseline allocation.
     Note that scenarios not generated from optimization cannot be plotted using this function,
     as assumed structure for spending is different """
    #initialize
    width = 0.35
    scale = 1
    fig = pl.figure(figsize=fig_size)
    ax = fig.add_axes(ax_size)
    figs = sc.odict()
    ref = all_res[1] # assumes baseline at index 0
    ref_spend = ref.prog_info.refs
    x = np.arange(len(all_res))
    xlabs = []
    bars = []
    bottom = np.zeros(len(all_res))
    colors = sc.gridcolors(ncolors=len(ref.programs))
    for i,prog in ref.programs.enumvals():
        y = []
        # get allocation for each multiple
        for j, res in enumerate(all_res):
            pos = res.mult if res.mult else res.name
            xlabs.append(utils.relabel(pos))
            # adjust spending so does not display reference spending
            alloc = res.programs[i].annual_spend[1] - ref_spend[i] # spending is same after first year in optimization
            # scale for axis
            alloc /= scale
            y = np.append(y, alloc)
        bar = ax.bar(x, y, width=width, bottom=bottom, color=colors[i])
        bars.append(bar)
        bottom += y
    ymax = max(bottom)
    ax.set_title('Optimal allocation, %s-%s'% (ref.years[0], ref.years[-1]))
    ax.set_xticks(x)
    ax.set_xticklabels(xlabs)
    ax.set_ylim((0, ymax+ymax*.1))
    ax.set_ylabel('Annual spending on programs (US$)')
    valuestr = str(res.prog_info.free/1e6)
    # format x axis
    if valuestr[1] == '.':
        valuestr = valuestr[:3]
    else:
        valuestr = valuestr[:2]
    string = 'Total available budget (relative to US$%sM)'%valuestr
    ax.set_xlabel(string)
    sc.SIticks(ax=ax, axis='y')
    nprogs = len(ref.programs)
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
    ax.legend(bars, ref.programs.keys(), **customizations)
    figs['alloc'] = fig
    return figs

def round_elements(mylist, dec=1):
    return [round(np.float64(x) * 100, dec) for x in mylist] # Type conversion to handle None













