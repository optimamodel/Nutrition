def make_plots(results):
    """ Results is a Scen object from which all information can be extracted """
    # HARDCODED JUST FOR DEMONSTRATION PURPOSES
    ## Initialize
    import pylab as pl
    mymodel = results.model
    years = results.year_names
    figsize = (5,3)
    axsize = (0.15, 0.15, 0.8, 0.8)
    fig = pl.figure(facecolor='none', figsize=figsize)

    outcome = round_elements(mymodel.wasting_prev, 1)
    ax2 = fig.add_axes(axsize)
    ax2.set_ylabel('Wasting prevalence (%)')
    ax2.set_xlabel('Year')
    ax2.plot(years, outcome)
    ax2.set_facecolor('none')
    ax2.set_ylim((0,pl.ylim()[1]))

    pl.show()
    return fig


def round_elements(mylist, dec):
    return [round(x * 100, dec) for x in mylist]

















