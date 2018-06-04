def make_plots(results):
    """ Results is a Scen object from which all information can be extracted """
    # HARDCODED JUST FOR DEMONSTRATION PURPOSES
    ## Initialize
    import pylab as pl
    mymodel = results.model
    years = results.year_names
    fig = pl.figure()

    outcome = round_elements(mymodel.wasting_prev, 1)
    ax2 = fig.add_subplot(211)
    ax2.set_ylabel('Wasting prevalence (%)')
    ax2.set_xlabel('Year')
    ax2.plot(years, outcome)

    pl.show()
    return fig


def round_elements(mylist, dec):
    return [round(x * 100, dec) for x in mylist]

















