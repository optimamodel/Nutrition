import pylab as pl, numpy as np, matplotlib.ticker as tk


def make_plots(res, toplot):
    """ Results is a Scen object from which all information can be extracted """
    # TODO: generate all plots, only show those requested
    ## Initialize
    allplots = {}
    if 'prevs' in toplot:
        prevfig = plot_prevs(res)
        allplots['prevs'] = prevfig
    if 'outputs' in toplot:
        outfig = plot_outputs(res)
        allplots['outputs'] = outfig
    return allplots

def plot_prevs(res):
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

def plot_outputs(res): # todo: this is not the desired usage
    outcomes = ['thrive', 'child_deaths']
    years = res.year_names
    outputs = res.get_outputs(outcomes, seq=True)
    fig, ax = pl.subplots(nrows=len(outputs),ncols=1, sharex=True)
    pl.xlabel('Years')
    pl.suptitle('Risk prevalences')
    for i, row in enumerate(ax):
        out = outputs[i]
        row.plot(years, out)
    return fig

def round_elements(mylist, dec):
    return [round(x * 100, dec) for x in mylist]

















