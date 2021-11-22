import pylab as pl
import numpy as np
import scipy.interpolate
import sciris as sc
from . import utils
from . import programs
from .scenarios import run_scen, make_scens, make_default_scen
from .results import reduce_results, resampled_key_str
import seaborn as sns

with sns.axes_style("white"):
    sns.set_style("ticks")
    sns.set_context("talk")
from matplotlib.legend_handler import HandlerBase
from matplotlib.text import Text
from matplotlib.legend import Legend
import string

# Choose where the legend appears: outside right or inside right
for_frontend = True
if for_frontend:
    legend_loc = {"bbox_to_anchor": (1.0, 1.0)}
    fig_size = (8, 4)
    ax_size = [0.2, 0.18, 0.40, 0.72]
    pltstart = 1
    hueshift = 0.05
    refprogs = False  # include ref spending?
else:
    legend_loc = {"loc": "right"}
    ax_size = [0.2, 0.10, 0.65, 0.75]
    pltstart = 1
    hueshift = 0.05
    refprogs = False  # include ref spending?


def save_figs(figs, path=".", prefix="", fnames=None) -> None:
    """
    Adapted from Atomica save_figs

    Save figures to disk as PNG files

    Functions like `plot_series` and `plot_bars` can generate multiple figures, depending on
    the data and legend options. This function facilitates saving those figures together.
    The name for the file can be automatically selected when saving figures generated
    by `plot_series` and `plot_bars`. This function also deals with cases where the figure
    list may or may not contain a separate legend (so saving figures with this function means
    the legend mode can be changed freely without having to change the figure saving code).

    :param figs: A figure or list of figures
    :param path: Optionally append a path to the figure file name
    :param prefix: Optionally prepend a prefix to the file name
    :param fnames: Optionally an array of file names. By default, each figure is named
    using its 'label' property. If a figure has an empty 'label' string it is assumed to be
    a legend and will be named based on the name of the figure immediately before it.
    If you provide an empty string in the `fnames` argument this same operation will be carried
    out. If the last figure name is omitted, an empty string will automatically be added.

    """
    import os, errno

    settings = dict()
    settings["legend_mode"] = "together"  # Possible options are ['together','separate','none']
    settings["bar_width"] = 1.0  # Width of bars in plot_bars()
    settings["line_width"] = 3.0  # Width of lines in plot_series()
    settings["marker_edge_width"] = 3.0
    settings["dpi"] = 150  # average quality
    settings["transparent"] = False

    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno != errno.EEXIST:
            raise

    if isinstance(figs, dict):
        if fnames is None:
            fnames = list(figs.keys())
        figs = figs.values()

    # Sanitize fig array input
    if not isinstance(figs, list):
        figs = [figs]

    # Sanitize and populate default fnames values
    if fnames is None:
        fnames = [fig.get_label() for fig in figs]
    elif not isinstance(fnames, list):
        fnames = [fnames]

    # Add legend figure to the end
    if len(fnames) < len(figs):
        fnames.append("")
    assert len(fnames) == len(figs), "Number of figures must match number of specified filenames, or the last figure must be a legend with no label"
    assert fnames[0], "The first figure name cannot be empty"

    for i, fig in enumerate(figs):
        if not fnames[i]:  # assert above means that i>0
            fnames[i] = fnames[i - 1] + "_legend"
            legend = fig.findobj(Legend)[0]
            renderer = fig.canvas.get_renderer()
            fig.draw(renderer=renderer)
            bbox = legend.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
        else:
            bbox = "tight"
        fname = prefix + fnames[i] + ".png"
        fname = sc.sanitizefilename(fname)  # parameters may have inappropriate characters
        fig.savefig(os.path.join(path, fname), bbox_inches=bbox, dpi=settings["dpi"], transparent=settings["transparent"])
        # logger.info('Saved figure "%s"', fname)


def make_plots(all_res=None, toplot=None, optim=False, geo=False):
    """
    This function controls all the plotting types a user can ask for
    :param all_res: all the results that should be plotted (list of ScenResult objects)
    :param toplot: type of plots to produce (list of strings)
    :param optim: are these the results of a national optimization? (boolean)
    :param geo: are these the results of a geospatial optimization? (boolean)
    :return: figures to be plotted (odict)
    """
    ## Initialize
    allplots = sc.odict()
    if toplot is None:
        toplot = ["prevs", "prev_reduce", "ann", "agg", "alloc", "annu_alloc", "clust_annu_alloc"]
    toplot = sc.promotetolist(toplot)
    if all_res is not None:
        all_res = sc.promotetolist(sc.dcp(all_res))  # Without dcp(), modifies the original and breaks things
        all_reduce = reduce_results(all_res)        
    
    if not all_res or not all_reduce:
        print('WARNING: No results to plot!')
        return allplots
    

    if "clust_annu_alloc" in toplot:  # optimized allocations
        outfigs = plot_clustered_annu_alloc(all_res, optim=optim, geo=geo)
        allplots.update(outfigs)
    if "alloc" in toplot:  # optimized allocations
        outfigs = plot_alloc(all_res, optim=optim, geo=geo)
        allplots.update(outfigs)
    if "prev_reduce" in toplot:
        prev_reducefigs = plot_prevs_reduce(all_res, all_reduce)
        allplots.update(prev_reducefigs)
    if "ann" in toplot:
        outfigs = plot_outputs_reduced(all_res, all_reduce, True, "ann")
        allplots.update(outfigs)
    if "agg" in toplot:
        outfigs = plot_outputs_reduced(all_res, all_reduce, False, "agg")
        allplots.update(outfigs)
    # if 'annu_alloc' in toplot: # optimized allocations
    # outfigs = plot_annu_alloc(all_res, optim=optim, geo=geo)
    # allplots.update(outfigs)

    return allplots


def plot_prevs_reduce(all_res, all_reduce):
    """ Plot prevs for each scenario generated through resampling"""
    prevs = utils.default_trackers(prev=True, rate=False)
    lines = []
    years = all_res[0].years
    figs = sc.odict()
    colors = sc.gridcolors(ncolors=len(all_reduce), hueshift=hueshift)
    for i, prev in enumerate(prevs):
        fig = pl.figure(figsize=fig_size)
        ax = fig.add_axes(ax_size)
        ymax = 0
        leglabels = []
        for r, res in enumerate(all_reduce):
            out_p = all_reduce[res][prev]["point"]
            out_l = all_reduce[res][prev]["low"]
            out_h = all_reduce[res][prev]["high"]
            newx = np.linspace(years[0], years[-1], len(years) * 10)
            fp = scipy.interpolate.PchipInterpolator(years, out_p, extrapolate=False)
            fl = scipy.interpolate.PchipInterpolator(years, out_l, extrapolate=False)
            fh = scipy.interpolate.PchipInterpolator(years, out_h, extrapolate=False)
            out_p = fp(newx) * 100
            out_l = fl(newx) * 100
            out_h = fh(newx) * 100
            thismax = max(out_h)
            if thismax > ymax:
                ymax = thismax
            (line,) = ax.plot(newx, out_p, color=colors[r])
            ax.fill_between(newx, out_l, out_h, alpha=0.2)
            lines.append(line)
            leglabels.append(res)
        ax.set_ylabel("Prevalence (%)")  # Shown as tick labels
        ax.set_ylim([0, ymax * 1.1])
        ax.set_xlabel("Years")
        ax.set_title(utils.relabel(prev))
        ax.legend(lines, [res for res in all_reduce if res != "Excess budget not allocated"], **legend_loc)
        figs["prevs_%0i" % i] = fig
    return figs


def plot_outputs_reduced(all_res, all_reduce, seq, name):
    """ Plot annual outputs and cumulative outputs for each scenario generated through resampling"""
    outcomes = utils.default_trackers(prev=False, rate=False)
    width = 0.2
    figs = sc.odict()

    baseres = all_res[0]
    years = np.array(baseres.years)  # assume these scenarios over same time horizon
    colors = sc.gridcolors(ncolors=len(all_reduce), hueshift=hueshift)
    for i, outcome in enumerate(outcomes): 
        if "cost" not in outcome and "pop_rate" not in outcome:
            fig = pl.figure(figsize=fig_size)
            ax = fig.add_axes(ax_size)
            ymax = 0
            perchange = []
            bars = []
    
            baseout = sc.promotetoarray(baseres.get_outputs(outcome, seq=seq)[0])
            scale = 1e6 if baseout.max() > 1e6 else 1
            baseout /= scale
            offsets = np.arange(len(all_reduce) + 1) * width  # Calculate offset so tick is in the center of the bars
            offsets -= offsets.mean() - 0.5 * width
            for r, res in enumerate(all_reduce):
    
                offset = offsets[r]
                xpos = years + offset if seq else offset
                if seq:
                    output_p = sc.promotetoarray(all_reduce[res][outcome]["point"])
                    output_l = sc.promotetoarray(all_reduce[res][outcome]["low"])
                    output_h = sc.promotetoarray(all_reduce[res][outcome]["high"])
                if not seq:
                    output_p = sc.promotetoarray(all_reduce[res][outcome]["point"].sum())
                    output_l = sc.promotetoarray(all_reduce[res][outcome]["low"].sum())
                    output_h = sc.promotetoarray(all_reduce[res][outcome]["high"].sum())
    
                output_p /= scale
                output_l /= scale
                output_h /= scale
                length = len(output_p)
                error = output_h[length - 1] - output_l[length - 1]
                thimax = output_h.max()
                kwargs = {"linewidth": 0.25}
                if thimax > ymax:
                    ymax = thimax
                change = round_elements([utils.get_change(base, out) for out, base in zip(output_p, baseout)], dec=1)
                perchange.append(change)
    
                if seq:
                    bar = ax.bar(xpos, output_p, width=width, color=colors[r], yerr=output_h - output_l, capsize=2, **kwargs)
                if not seq:
                    bar = ax.bar(xpos, output_p, width=width, color=colors[r])
                    ax.errorbar(xpos, output_p[length - 1], yerr=error, capsize=2, color="black")
                bars.append(bar)
    
            if seq:
                ax.set_xlabel("Years")
                title = "Annual"
            else:
                title = "Cumulative"
                ax.set_xticks([])
    
                # display percentage change above bars
                for j, bar in enumerate(bars[1:], 1):
                    rect = bar[-1]
                    change = perchange[j][0]
                    height = rect.get_height()
                    ax.text(rect.get_x() + rect.get_width() / 2.0, height, "{}%".format(change), ha="center", va="bottom", fontsize=10)
            # formatting
            title += " %s \n %s-%s" % (utils.relabel(outcome).lower(), baseres.years[pltstart], baseres.years[-1])
            sc.SIticks(ax=ax, axis="y")
            ax.set_ylim([0, ymax * 1.1])
            if scale == 1:
                ylabel = "Number"
            elif scale == 1e6:
                ylabel = "Number (millions)"
            else:
                raise Exception("Scale value must be 1 or 1e6, not %s" % scale)
            ax.set_ylabel(ylabel)
            ax.legend(bars, [res for res in all_reduce if res != "Excess budget not allocated"], ncol=1, **legend_loc)
            ax.set_title(title)
            figs["%s_out_%0i" % (name, i)] = fig
    return figs


# =============================================================================
# def plot_prevs(all_res):
#     """ Plot prevs for each scenario (optimized and no resampling)"""
#     prevs = utils.default_trackers(prev=True, rate=False)
#     lines = []
#     figs = sc.odict()
#     colors = sc.gridcolors(ncolors=len(all_res), hueshift=hueshift)
#     for i, prev in enumerate(prevs):
#         fig = pl.figure(figsize=fig_size)
#         ax = fig.add_axes(ax_size)
#         ymax = 0
#         leglabels = []
#         # plot results
#         for r, res in enumerate(all_res):
#             if res.name != "Excess budget not allocated":
#                 years = res.years
#                 out = res.get_outputs([prev], seq=True)[0]
#                 f = scipy.interpolate.PchipInterpolator(years, out, extrapolate=False)
#                 newx = np.linspace(years[0], years[-1], len(years) * 10)
#                 out = f(newx) * 100
#                 mean = np.mean(out, axis=0)
#                 standard_dev = np.std(out, axis=0)
#                 thismax = max(out)
#                 if thismax > ymax:
#                     ymax = thismax
#                 (line,) = ax.plot(newx, out, color=colors[r])
#                 lines.append(line)
#                 leglabels.append(res.name)
#         # formatting
#         #        sc.SIticks(ax=ax, axis='y')
#         ax.set_ylabel("Prevalence (%)")  # Shown as tick labels
#         ax.set_ylim([0, ymax * 1.1])
#         ax.set_xlabel("Years")
#         ax.set_title(utils.relabel(prev))
#         ax.legend(lines, [res.name for res in all_res if res.name != "Excess budget not allocated"], **legend_loc)
#         figs["prevs_%0i" % i] = fig
#     return figs
# =============================================================================


# =============================================================================
# def plot_outputs(all_res, all_reduce, seq, name):
#     """ Plot annual outputs and cumulative outputs for each scenario (optimized and no resampling)"""
#     outcomes = utils.default_trackers(prev=False, rate=False)
#     width = 1 / (len(all_res) + 1)
#     figs = sc.odict()
# 
#     baseres = all_res[0]
#     years = np.array(baseres.years)  # assume these scenarios over same time horizon
#     colors = sc.gridcolors(ncolors=len(all_res), hueshift=hueshift)
#     for i, outcome in enumerate(outcomes):
#         fig = pl.figure(figsize=fig_size)
#         ax = fig.add_axes(ax_size)
#         ymax = 0
#         perchange = []
#         bars = []
# 
#         baseout = sc.promotetoarray(baseres.get_outputs(outcome, seq=seq)[0])
#         scale = 1e6 if baseout.max() > 1e6 else 1
#         baseout /= scale
#         offsets = np.arange(len(all_res) + 1) * width  # Calculate offset so tick is in the center of the bars
#         offsets -= offsets.mean() - 0.5 * width
#         for r, res in enumerate(all_res):
#             if res.name != "Excess budget not allocated":
#                 offset = offsets[r]
#                 xpos = years + offset if seq else offset
#                 output = sc.promotetoarray(res.get_outputs(outcome, seq=seq)[0])
#                 output /= scale
#                 thimax = output.max()
#                 if thimax > ymax:
#                     ymax = thimax
#                 change = round_elements([utils.get_change(base, out) for out, base in zip(output, baseout)], dec=1)
#                 perchange.append(change)
#                 bar = ax.bar(xpos, output, width=width, color=colors[r])
#                 bars.append(bar)
#         if seq:
#             ax.set_xlabel("Years")
#             title = "Annual"
#         else:
#             title = "Cumulative"
#             ax.set_xticks([])
# 
#             # display percentage change above bars
#             for j, bar in enumerate(bars[1:], 1):
#                 for k, rect in enumerate(bar):
#                     change = perchange[j][k]
#                     height = rect.get_height()
#                     ax.text(rect.get_x() + rect.get_width() / 2.0, height, "{}%".format(change), ha="center", va="bottom", fontsize=10)
#         # formatting
#         title += " %s \n %s-%s" % (utils.relabel(outcome).lower(), baseres.years[pltstart], baseres.years[-1])
#         sc.SIticks(ax=ax, axis="y")
#         ax.set_ylim([0, ymax * 1.1])
#         if scale == 1:
#             ylabel = "Number"
#         elif scale == 1e6:
#             ylabel = "Number (millions)"
#         else:
#             raise Exception("Scale value must be 1 or 1e6, not %s" % scale)
#         ax.set_ylabel(ylabel)
#         ax.legend(bars, [res.name for res in all_res if res.name != "Excess budget not allocated"], ncol=1, **legend_loc)
#         ax.set_title(title)
#         figs["%s_out_%0i" % (name, i)] = fig
#     return figs
# =============================================================================


def plot_alloc(results, optim, geo):
    """Plots the average annual spending for each scenario, coloured by program.
    Legend will include all programs in the 'baseline' allocation which receive non-zero spending in any scenario
    Generates a single plot considering the mean spend over whole period"""

    # Initialize
    width = 0.35
    fig = pl.figure(figsize=fig_size)
    ax = fig.add_axes(ax_size)
    figs = sc.odict()
    ref = results[0]
    progset = ref.prog_info.base_progset()
    colors = sc.gridcolors(ncolors=len(progset), hueshift=hueshift)
    leglabs = []
    res_list = [res for res in results if "#" not in res.name]
    x = np.arange(len(res_list))

    # Group allocations by program
    avspend = []
    for prog in progset:
        thisprog = np.zeros(len(res_list))
        for i, res in enumerate(res_list):
            alloc = res.get_allocs(ref=refprogs)  # slightly inefficient to do this for every program
            try:
                progav = alloc[prog][1:].mean()
            except:  # program not in scenario program set
                progav = 0
            thisprog[i] = progav
        avspend.append(thisprog)

    # Scale
    avspend = np.array(avspend)
    if avspend.max() > 1e6:
        scale = 1e6
    else:
        scale = 1e1
    avspend /= scale

    # Make bar plots
    bars = []
    # xlabs = [res.mult if res.mult is not None else res.name for res in res_list]
    bottom = np.zeros(len(res_list))
    for i, spend in enumerate(avspend):
        if any(spend) > 0:  # only want to plot prog if spending is non-zero (solves legend issues)
            leglabs.append(progset[i])
            bar = ax.barh(x, spend, width, bottom, color=colors[i])
            bars.append(bar)
            bottom += spend
    ymax = max(bottom)
    if optim or geo:
        xlabs = [res.name for res in results if "#" not in res.name]
        title = "Optimal allocation, %s-%s" % (ref.years[pltstart], ref.years[-1])
        valuestr = str(results[1].prog_info.free / 1e6)  # bit of a hack
        # format x axis
        if valuestr[1] == ".":
            valuestr = valuestr[:3]
        else:
            valuestr = valuestr[:2]
        if geo:
            xlab = "Region"
        else:
            xlab = "Total available budget (relative to US$%sM)" % valuestr
    else:
        xlabs = [res.mult if res.mult is not None else res.name for res in res_list if "#" not in res.name]
        title = "Average annual spending, %s-%s" % (ref.years[pltstart], ref.years[-1])
        xlab = ""  # 'Scenario' # Collides with tick labels
    ax.set_title(title)
    ax.set_yticks(x)
    ax.set_yticklabels(xlabs)
    ax.set_ylabel(xlab)
    ax.set_xlim((0, ymax + ymax * 0.1))
    if scale == 1e1:
        ylabel = "Spending (US$)"
    elif scale == 1e6:
        ylabel = "Spending (US$M)"
    else:
        raise Exception("Scale value must be 1e1 or 1e6, not %s" % scale)
    ax.set_xlabel(ylabel)
    #    sc.SIticks(ax=ax, axis='y')
    nprogs = len(leglabs)
    labelspacing = 0.1
    columnspacing = 0.1
    fontsize = None
    ncol = 1
    if nprogs > 10:
        fontsize = 8
    if nprogs > 12:
        fontsize = 6
    if nprogs > 24:
        ncol = 2
    customizations = {"fontsize": fontsize, "labelspacing": labelspacing, "ncol": ncol, "columnspacing": columnspacing}
    customizations.update(legend_loc)
    ax.legend(bars, leglabs, **customizations)
    figs["alloc"] = fig
    return figs


def plot_annu_alloc(results, optim, geo):
    """Plots the annual spending for each scenario, coloured by program.
    Legend will include all programs in the 'baseline' allocation which receive non-zero spending in any scenario
    Generates a plot for each year"""

    # Initialize
    width = 0.35
    figs = sc.odict()
    year = results[0].years
    ref = results[0]
    progset = ref.prog_info.base_progset()
    colors = sc.gridcolors(ncolors=len(progset), hueshift=hueshift)
    leglabs = []
    res_list = [res for res in results if "#" not in res.name]
    x = np.arange(len(res_list))

    for k in range(1, len(year)):
        fig = pl.figure(figsize=fig_size)
        ax = fig.add_axes(ax_size)

        # Group allocations by program
        avspend = []

        for prog in progset:
            thisprog = np.zeros(len(res_list))
            for i, res in enumerate(res_list):
                alloc = res.get_allocs(ref=refprogs)  # slightly inefficient to do this for every program
                try:
                    progav = alloc[prog][k]  # extracting the spend for each year for each program
                except:  # program not in scenario program set
                    progav = 0
                thisprog[i] = progav
            avspend.append(thisprog)

        # Scale
        avspend = np.array(avspend)
        if avspend.max() > 1e6:
            scale = 1e6
        else:
            scale = 1e1
        # avspend /= scale
        avspend = np.divide(avspend, scale)
        # Make bar plots
        bars = []
        # xlabs = [res.mult if res.mult is not None else res.name for res in results if '#' not in res.name]
        bottom = np.zeros(len(res_list))
        for i, spend in enumerate(avspend):
            if any(spend) > 0:  # only want to plot prog if spending is non-zero (solves legend issues)
                leglabs.append(progset[i])
                bar = ax.bar(x, spend, width, bottom, color=colors[i])
                bars.append(bar)
                bottom += spend
        ymax = max(bottom)
        if optim or geo:
            xlabs = [res.name for res in results]
            title = "Optimal allocation, %s-%s" % (ref.years[pltstart], ref.years[-1])
            valuestr = str(results[1].prog_info.free / 1e6)  # bit of a hack
            # format x axis
            if valuestr[1] == ".":
                valuestr = valuestr[:3]
            else:
                valuestr = valuestr[:2]
            if geo:
                xlab = "Region"
            else:
                xlab = "Total available budget (relative to US$%sM)" % valuestr
        else:
            xlabs = [res.mult if res.mult is not None else res.name for res in results if "#" not in res.name]
            title = "Annual spending for year %s" % year[k]
            xlab = ""  # 'Scenario' # Collides with tick labels
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(xlabs, fontsize=8, rotation=90)
        ax.set_xlabel(xlab)
        ax.set_ylim((0, ymax + ymax * 0.1))
        if scale == 1e1:
            ylabel = "Spending (US$)"
        elif scale == 1e6:
            ylabel = "Spending (US$M)"
        else:
            raise Exception("Scale value must be 1e1 or 1e6, not %s" % scale)
        ax.set_ylabel(ylabel)
        #   sc.SIticks(ax=ax, axis='y')
        nprogs = len(leglabs)
        labelspacing = 0.1
        columnspacing = 0.1
        fontsize = None
        ncol = 1
        if nprogs > 10:
            fontsize = 8
        if nprogs > 12:
            fontsize = 6
        if nprogs > 24:
            ncol = 2
        customizations = {"fontsize": fontsize, "labelspacing": labelspacing, "ncol": ncol, "columnspacing": columnspacing}
        customizations.update(legend_loc)
        ax.legend(bars, leglabs, **customizations)
        figs["annu_alloc"] = fig
    return figs


def plot_clustered_annu_alloc(results, optim: bool, geo: bool):
    """Plots the annual spending for each scenario, coloured by program.
    Legend will include all programs in the 'baseline' allocation which receive non-zero spending in any scenario
    Generates a single plot that represent allocations for each scenario annually
    :param results: a list of ScenResults objects
    :param optim: True if these are optimization results, False if not (a slightly different format of results)
    :param geo: True if these are geospatial results, False if not (a slightly different format of results)
    
    :return a list of figures
    """
    
    res_list = [res for res in results if resampled_key_str not in res.name]

    # Initialize
    width = 1.0 / (len(res_list) + 1)
    epsilon = 0.015
    figs = sc.odict()
    year = results[0].years
    ref = res_list[0]
    progset = ref.prog_info.base_progset()
    colors = sc.gridcolors(ncolors=len(progset), hueshift=hueshift)
    leglabs = []
    fig = pl.figure(figsize=(20, 6))
    ax = fig.add_axes(ax_size)
    
    x_base = np.arange(len(res_list))
    x = np.multiply(x_base, width)
    year_ticks = np.arange(len(year))

    for k in range(1, len(year)):
        # Group allocations by program
        avspend = []

        for prog in progset:
            thisprog = np.zeros(len(res_list))
            for i, res in enumerate(res_list):
                # if 'resampled' not in res.name:
                if not (optim or geo) or (res.name != "Excess budget not allocated"):
                
                    alloc = res.get_allocs(ref=refprogs)  # slightly inefficient to do this for every program
                    try:
                        progav = alloc[prog][k]  # extracting the spend for each year for each program
    
                    except:  # program not in scenario program set
                        progav = 0
                    thisprog[i] = progav
            avspend.append(thisprog)

        # Scale
        avspend = np.array(avspend)
        if avspend.max() > 1e6:
            scale = 1e6
        else:
            scale = 1e1
        # avspend /= scale
        avspend = np.divide(avspend, scale)
        # Make bar plots
        bars = []
        
        xlabs = [res.name for res in res_list]
        
        bottom = np.zeros(len(res_list))
        for i, spend in enumerate(avspend):
            if any(spend) > 0:  # only want to plot prog if spending is non-zero (solves legend issues)
                leglabs.append(progset[i])
                bar = ax.bar(x + year[k], spend, width, bottom, color=colors[i])  # bars for each year in iteration
                bars.append(bar)
                bottom += spend
        ymax = max(bottom)
        if optim or geo:
            title = "Optimal allocation, %s-%s" % (ref.years[pltstart], ref.years[-1])
            valuestr = str(results[1].prog_info.free / 1e6)  # bit of a hack TODO almost certainly this is broken now??
            # format x axis
            if valuestr[1] == ".":
                valuestr = valuestr[:3]
            else:
                valuestr = valuestr[:2]
            if geo:
                xlab = "Region"
            else:
                xlab = "Total available budget (relative to US$%sM)" % valuestr
        else:
            title = "Annual spending, %s-%s" % (ref.years[pltstart], ref.years[-1])
            xlab = "Years"
    ax.set_title(title)
    ax.set_xticks(np.array(year[1:]) + ((len(res_list) - 1) / 2) * width)  # ignoring base year and makingsure tick is at the middle of the bar group
    #ax.set_xticklabels(year[1:], fontsize=10)
    ax.set_xlabel(xlab)
    ax.set_ylim((0, ymax + ymax * 0.1))
    if scale == 1e1:
        ylabel = "Spending (US$)"
    elif scale == 1e6:
        ylabel = "Spending (US$M)"
    else:
        raise Exception("Scale value must be 1e1 or 1e6, not %s" % scale)
    ax.set_ylabel(ylabel)
    #   sc.SIticks(ax=ax, axis='y')
    nprogs = len(leglabs)
    labelspacing = 0.1
    columnspacing = 0.1
    fontsize = None
    ncol = 1
    if nprogs > 10:
        fontsize = 10
    if nprogs > 12:
        fontsize = 8
    if nprogs > 24:
        ncol = 2
    customizations = {"fontsize": fontsize, "labelspacing": labelspacing, "ncol": ncol, "columnspacing": columnspacing}
    customizations.update(legend_loc)
    legend_1 = ax.legend(bars, leglabs, **customizations)
    handles = [f"Bar {j}: " for j in range(1, len(xlabs) + 1)]
    ax.legend(handles=handles, labels=xlabs, loc="center left", bbox_to_anchor=(1.0, 0.3), fontsize=10, borderpad=1.2)
    figs["clust_annu_alloc"] = fig
    fig.add_artist(legend_1)
    return figs

def plot_costcurve(results):
    """Plots the cost coverage curves.
    Really only used as a diagnostic plotting tool, since with lots of programs it may not be very informative for a user."""
    fig = pl.figure()
    ax = fig.add_axes(ax_size)
    leglabs = []
    for res in results[:1]:
        allocs = res.get_allocs()
        maxspend = 0
        for name in res.programs.iterkeys():
            thisspend = allocs[name]
            leglabs.append(name)
            if maxspend < np.max(thisspend):
                maxspend = np.max(thisspend)
        x = np.linspace(0, 2e7, 10000)
        for prog in res.programs.itervalues():
            y = prog.func(x)
            ax.plot(x, y)
    ax.set_ylim([0, 1])
    ax.set_xlim([0, 2e7])
    ax.set_ylabel("Coverage (%)")
    ax.set_xlabel("Spending ($US)")
    ax.legend(leglabs)
    return fig


def get_costeff(project, results):
    """
    Calculates the cost per impact of a scenario.
    (Total money spent on all programs (baseline + new) ) / (scneario outcome - zero cov outcome)
    :return: 3 levels of nested odicts, with keys (scen name, child name, pretty outcome) and value of type string
    """
    parents = []
    baselines = []
    children = sc.odict()
    for r, res in enumerate(results):
        print("Running cost-effectiveness result %s of %s" % (r + 1, len(results)))
        children[res.name] = []
        model = project.model(res.model_name)
        parents.append(res)
        # generate a baseline for each scenario
        baseline = make_default_scen(res.model_name, model)
        baseres = run_scen(baseline, model)
        baselines.append(baseres)
        # get all the 'child' results for each scenario
        childkwargs = res.get_childscens()
        childscens = make_scens(childkwargs)
        for child in childscens:
            if child.name != "Excess budget":
                if "Excess budget not allocated" in child.prog_set:
                    child.prog_set.remove("Excess budget not allocated")
                childres = run_scen(child, model)
                children[res.name].append(childres)
    outcomes = utils.default_trackers(prev=False, rate=False)
    pretty = utils.relabel(outcomes)
    costeff = sc.odict()
    for i, parent in enumerate(parents):
        if parent.name != "Excess budget":
            baseline = baselines[i]
            costeff[parent.name] = sc.odict()
            par_outs = parent.get_outputs(outcomes)
            allocs = parent.get_allocs(ref=refprogs)
            baseallocs = baseline.get_allocs(ref=refprogs)
            filteredbase = sc.odict({prog: spend for prog, spend in baseallocs.items() if prog not in allocs})
            totalspend = allocs[:].sum() + filteredbase[:].sum()
            thesechildren = children[parent.name]
            for j, child in enumerate(thesechildren):
                if j > 0:  # i.e. scenarios with individual scale-downs
                    # only want spending on individual program in parent scen
                    progspend = allocs[child.name]
                    totalspend = sum(progspend)
                costeff[parent.name][child.name] = sc.odict()
                child_outs = child.get_outputs(outcomes)
                for k, out in enumerate(outcomes):
                    impact = par_outs[k] - child_outs[k]
                    if abs(impact) < 1 or totalspend < 1:  # should only be used for number of people, not prevalence or rates
                        # total spend < 1 will catch the scale-down of reference programs, since they will return $0 expenditure
                        costimpact = "No impact"
                    else:
                        costimpact = totalspend / impact
                        costimpact = round(costimpact, 2)
                        # format
                        if out == "thrive":  # thrive should increase
                            if costimpact < 0:
                                costimpact = "Negative impact"
                            else:
                                costimpact = "$%s per additional case" % format(costimpact, ",")
                        else:  # all other outcomes should be negative
                            if costimpact > 0:
                                costimpact = "Negative impact"
                            else:
                                costimpact = "$%s per case averted" % format(-costimpact, ",")
                    costeff[parent.name][child.name][pretty[k]] = costimpact
    return costeff


def round_elements(mylist, dec=1):
    return [round(np.float64(x) * 100, dec) for x in mylist]  # Type conversion to handle None


class TextHandlerB(HandlerBase):
    """This class can be used to modify the legend handle of any plot. Usually
    there is no in-built option to do that to change the handle for string type"""

    def create_artists(self, legend, text, xdescent, ydescent, width, height, fontsize, trans):
        tx = Text(width / 2.0, height / 2, text, fontsize=fontsize, ha="center", va="center", fontweight="bold")
        return [tx]


Legend.update_default_handler_map({str: TextHandlerB()})
