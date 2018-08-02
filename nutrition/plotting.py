import pylab as pl
import numpy as np
import matplotlib.ticker as tk
import sciris.core as sc
import utils
import scipy.interpolate

# Choose where the legend appears: outside right or inside right
for_frontend = True
if for_frontend:
    legend_loc = {'bbox_to_anchor':(1,0.8)}
    legend_loc_prev = {'loc':'best'} # No idea why this has to be different, but it does
    ax_size = [0.2,0.12,0.50,0.75]
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
    if None in all_res:
        all_res = [x for x in all_res if x is not None]
        if not all_res:
            return sc.printv('Warning, no results to plot')
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
        fig = pl.figure()
        ax = fig.add_axes(ax_size)
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
        ax.set_ylabel('Percentage')
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
    scale = 1e6 # scales for formatting
    baseres = all_res[0]
    years = np.array(baseres.years) # assume these scenarios over same time horizon
    for i, outcome in enumerate(outcomes):
        fig = pl.figure()
        ax = fig.add_axes(ax_size)
        ymax = 0
        perchange = []
        bars = []
        offset = -width
        baseout = baseres.get_outputs(outcome, seq=seq)[0] / scale
        for res in all_res:
            offset += width
            xpos = years + offset if seq else offset
            output = res.get_outputs(outcome, seq=seq)[0] / scale
            thimax = max(output)
            if thimax > ymax: ymax = thimax
            change = round_elements([utils.get_change(base, out) for out,base in zip(output, baseout)], dec=1)
            perchange.append(change)
            bar = ax.bar(xpos, output, width=width)
            bars.append(bar)
        if seq:
            # ax.set_xticks(years+offset/2.)
            # ax.set_xticklabels(years)
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
        ax.set_ylim([0, ymax + ymax * .1])
        ax.set_ylabel('Number (millions)')
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
    mag = 1e6
    fig = pl.figure()
    ax = fig.add_axes(ax_size)
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
    colors = sc.gridcolors(ncolors=len(ref.programs))
    for i,prog in enumerate(ref.programs):
        y = []
        # get allocation for each multiple
        for j, res in enumerate(all_res):
            pos = res.mult if res.mult else res.name
            xlabs.append(utils.relabel(pos))
            # adjust spending so does not display reference spending
            alloc = res.programs[i].annual_spend[1] - ref_spend[i] # spending is same after first year in optimization
            # scale for axis
            alloc /= mag
            y = np.append(y, alloc)
        bar = ax.bar(x, y, width=width, bottom=bottom, color=colors[i])
        bars.append(bar)
        bottom += y
    ymax = max(bottom)
    # formatting
    if ref.obj is not None: title = utils.relabel(ref.obj).lower()
    else: title = '' # WARNING, should probably fix this properly
    ax.set_title('To optimize the \n %s %s-%s'%(title, ref.years[0], ref.years[-1]))
    ax.set_xticks(x)
    ax.set_xticklabels(xlabs)
    ax.set_ylim((0, ymax+ymax*.1))
    ax.set_ylabel('Annual spending on programs (million US$)')
    try:
        valuestr = int(str(res.prog_info.free)[:2])
        string = 'Total available budget (as a multiple of US$%sM)'%valuestr
    except:
        string = 'Total available budget (relative to %s)' % str(res.prog_info.free)
    ax.set_xlabel(string)
    ax.yaxis.set_major_formatter(tk.FormatStrFormatter('%3.0f'))
    ax.legend(bars, [prog.name for prog in ref.programs], **legend_loc)
    figs['alloc'] = fig
    return figs

def round_elements(mylist, dec=1):
    return [round(np.float64(x) * 100, dec) for x in mylist] # Type conversion to handle None













