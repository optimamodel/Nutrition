import pylab as pl, numpy as np, matplotlib.ticker as tk

def make_plots(res, toplot):
    """ Results is a Scen object from which all information can be extracted """
    # TODO: generate all plots, only show those requested
    ## Initialize
    allplots = {}
    if 'prevs' in toplot:
        prevfig = plot_prevs(res)
        allplots['prevs'] = prevfig
    # if 'outputs' in toplot: # todo: want to compare outcomes across scenarios
    #     outfig = plot_outputs(res)
    #     allplots['outputs'] = outfig
    if 'alloc' in toplot: # optimised allocations
        bars = plot_alloc(res)
        allplots['alloc'] = bars
    return allplots

def plot_prevs(res):
    # todo: if this is OptimResult, then need to access all the Scens to plot these prevs
    years = res.year_names
    allattr = res.model_attr()
    prevs = [attr for attr in allattr if 'prev' in attr]
    outputs = res.get_outputs(prevs, seq=True)
    fig, ax = pl.subplots(nrows=len(prevs),ncols=1, sharex=True)
    pl.xlabel('Years')
    pl.suptitle('Risk prevalences')
    for i, row in enumerate(ax):
        out = outputs[i]
        # out = round_elements(out)
        label = prevs[i]
        row.yaxis.set_major_formatter(tk.FormatStrFormatter('%.1f'))
        row.set_ylabel(label)
        row.plot(years, out)
    return fig

# def plot_outputs(res): # todo: this is not the desired usage
#     outcomes = ['thrive', 'child_deaths'] # not all yet, since not tracking them
#     years = res.year_names
#     outputs = res.get_outputs(outcomes, seq=True)
#     fig, ax = pl.subplots(nrows=len(outputs),ncols=1, sharex=True)
#     pl.xlabel('Years')
#     pl.suptitle('Risk prevalences')
#     for i, row in enumerate(ax):
#         out = outputs[i]
#         row.plot(years, out)
#     return fig

def plot_alloc(res):
    """ Plot the program allocations from an optimization, alongside current allocation """
    # TODO: WARNING: does not account for multiple objectives, accout for in future
    xlabs = ['current'] + res.mults
    x = np.arange(len(xlabs))
    width = 0.35
    # over the programs
    allocs = [res.curr_alloc] + res.optim_allocs
    charts = []
    all_y = []
    bottom = np.zeros(len(xlabs))
    for i, prog in enumerate(res.programs):
        y = []
        # get allocation for each multiple
        for j, mult in enumerate(xlabs):
            alloc = allocs[j]
            y = np.append(y, alloc[i])
        all_y.append(y)
        charts.append(pl.bar(x, all_y[i], width=width, bottom=bottom))
        bottom += all_y[i]
    pl.ylabel('Funding')
    pl.xticks(x, xlabs)
    legendart = [p[0] for p in charts]
    legendlab = [prog.name for prog in res.programs]
    pl.legend(legendart, legendlab)
    return charts

def round_elements(mylist, dec=1):
    return [round(x * 100, dec) for x in mylist]

















