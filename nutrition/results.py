import sciris as sc
from .utils import default_trackers, pretty_labels
import numpy as np
import math as mt



class ScenResult(sc.prettyobj):
    def __init__(self, name, model_name, model, obj=None, mult=None, weight=None, growth=False):
        self.name = name
        self.model_name = model_name
        self.model = model
        self.prog_info = self.model.prog_info  # provides access to costing info
        self.programs = self.prog_info.programs
        self.pops = self.model.pops
        self.mult = mult
        self.weight = weight
        self.obj = obj
        self.years = list(range(model.t[0], model.t[1] + 1))
        self.uid = sc.uuid()
        self.created = sc.now()
        self.modified = sc.now()
        self.growth = growth
        # self.results = []

    def model_attr(self):
        return self.model.__dict__

    def get_outputs(self, outcomes=None, seq=False, asdict=True, pretty=False):
        """
        outcomes: a list of model outcomes to return
        return: a list of outputs with same order as outcomes
        """
        if outcomes is None:
            outcomes = default_trackers()
        if sc.isstring(outcomes):
            outcomes = sc.promotetolist(outcomes)
        outs = self.model.get_output(outcomes, seq=seq)
        if asdict:
            output = sc.odict()
            for o, outcome in enumerate(outcomes):
                output[outcome] = outs[o]
        else:
            output = outs
            if pretty and not seq:
                prettyvals = []
                for out, val in zip(outcomes, output):
                    if "prev" in out:
                        prettyval = round(val * 100, 2)
                    else:
                        prettyval = round(val, 0)
                    prettyvals.append(prettyval)
                output = prettyvals
        return output

    def get_covs(self, ref=True, unrestr=True):
        covs = sc.odict()

        for name, prog in self.programs.iteritems():
            if self.growth:
                covs[name] = prog.annual_restr_cov
            else:
                covs[name] = prog.annual_cov
        return covs

    def get_allocs(self, ref=True, current=False):
        allocs = sc.odict()

        for name, prog in self.programs.items():
            prog_cov = prog.get_cov(unrestr=True)
            allocs[name] = prog.annual_spend

        return allocs

    def get_freefunds(self):
        free = self.model.prog_info.free
        if self.mult is not None:
            free *= self.mult
        return free

    def get_currspend(self):
        return self.model.prog_info.curr

    def get_basefunds(self):
        return self.model.prog_info.fixed

    def get_populations(self):
        total_population = self.model.children.total_pop()
        return total_population

    def get_childscens(self):
        """ For calculating the impacts of each scenario with single intervention set to 0 coverage """
        cov = [0]
        allkwargs = []
        progset = self.programs.keys()
        base_progset = self.prog_info.base_progset()
        # zero cov scen
        kwargs = {"name": "Scenario overall", "model_name": self.model_name, "scen_type": "budget", "progvals": {prog: cov for prog in base_progset}}
        allkwargs.append(kwargs)
        # scale down each program to 0 individually
        progvals = self.get_allocs(ref=True)
        for prog in progset:
            new_progvals = sc.dcp(progvals)
            new_progvals[prog] = cov
            kwargs = {"name": prog, "model_name": self.model_name, "scen_type": "budget", "progvals": new_progvals}
            allkwargs.append(kwargs)
        return allkwargs

    def plot(self, toplot=None):
        from .plotting import make_plots  # This is here to avoid a circular import

        figs = make_plots(all_res=self, toplot=toplot)
        return figs


def reduce_results(results, point_estimate:str="best", bounds:str = "quantiles", stddevs=None, quantiles=None, keep_raw=False):
    """Function to reduce a list of results including sampled results to a list of main results with point estimates, and upper and lower bounds
    Should return a subset of results excluding anything that was sampled
    :param results: a list of ScenResult objects
    :param point_estimate: 'best' = the outcome values from the non-sampled result, 'mean' = the mean of sampled results at each timestep, 'median' = the median of sampled results at each timestep
    :param bounds: 'best' = the outcome values from the non-sampled result, 'stddevs' = the value stddevs away from the (mean) point estimate, 'quantiles' = upper and lower quantiles from the sampled results
    :param stddevs: number of standard deviations away from the mean to return, only used if bounds == stddevs
    :param quantiles: the lower and upper quantiles to return, as a dict or tuple, only used if bounds == quantiles
    :param keep_raw: also keep all of the individual sampled results (troubleshooting or alternative plot methods might use this)
    
    :return results dict of the key outcomes for each main result, not the full results
    """
    sampled_pattern = " resampled__#" #must match project run_scen pattern (should be in universal constants somewhere instead)
    
    years = results[0].years
    estimate_keys = ["point", "low", "high"]
    outcomes = default_trackers()
    if bounds == "stddevs":
        assert point_estimate == "mean", 'If bounds are stddevs, point_estimate should be mean'
        if stddevs is None:
            stddevs = 2
    elif bounds == "quantiles":
        if quantiles is None:
            quantiles = {"low": 0.1, "high": 0.9}
        if not isinstance(quantiles, dict):
            try:
                quantiles = {"low": float(quantiles[0]), "high": float(quantiles[1])}
            except Exception as E:
                errormsg = f"Could not figure out how to convert {quantiles} into a quantiles object: must be a dict with keys low, high or a 2-element array ({str(E)})"
                raise ValueError(errormsg)
    
    res_unc = {} #this will be the returned results with uncertainty and without sampled results

    for res in results:
        if sampled_pattern not in res.name: #e.g. it's a "real" point estimate result
            # print ('Evaluating', res.name)
            res_unc[res.name] = {o: {es: np.zeros(len(years)) for es in estimate_keys} for o in outcomes}
            
            sampled_results = [sr for sr in results if res.name + sampled_pattern in sr.name]
            n_sampled_runs = len(sampled_results)


            raw = {o: {n: np.zeros(len(years)) for n in range(n_sampled_runs)} for o in outcomes}
            
            for sr, sampled_result in enumerate(sampled_results):
                sampled_out = sampled_result.get_outputs(outcomes, seq=True, pretty=True)
                for out_key in outcomes:
                    raw[out_key][sr] = sampled_out[out_key]
                    
            # for default tracker outcomes
            # note that if there are no sampled runs it uses the 'best' (non-sampled) result for all estimates
            best_estimates = res.get_outputs(outcomes, seq=True, pretty=True)
            
            for out_key in outcomes:
                best_estimate = best_estimates[out_key]
                axis = 0
                #Choose a method for the point estimate
                if point_estimate == "best" or n_sampled_runs == 0:
                    res_unc[res.name][out_key]["point"] = sc.dcp(best_estimate)
                elif point_estimate == "mean": 
                    r_mean = np.mean(list(raw[out_key].values()), axis=axis)
                    res_unc[res.name][out_key]["point"] = r_mean
                elif point_estimate == "median":
                    res_unc[res.name][out_key]["point"] = np.quantile(list(raw[out_key].values()), q=0.5, axis=axis)
                else:
                    raise Exception(f'Point estimate must be "best" (non-sampled), "mean" (from samples), or "median" (from samples), {point_estimate} not a valid choice.')
                
                 #Choose a method for the lower and upper bounds
                if bounds == "best" or n_sampled_runs == 0:
                    res_unc[res.name][out_key]["low"] = sc.dcp(best_estimate)
                    res_unc[res.name][out_key]["high"] = sc.dcp(best_estimate)
                elif bounds == "stddevs":
                    r_mean = np.mean(list(raw[out_key].values()), axis=axis)
                    r_std = np.std(list(raw[out_key].values()), axis=axis)
                    res_unc[res.name][out_key]["low"] = r_mean - stddevs * r_std
                    res_unc[res.name][out_key]["high"] = r_mean + stddevs * r_std
                elif bounds == "quantiles":
                    res_unc[res.name][out_key]["low"] = np.quantile(list(raw[out_key].values()), q=quantiles["low"], axis=axis)
                    res_unc[res.name][out_key]["high"] = np.quantile(list(raw[out_key].values()), q=quantiles["high"], axis=axis)
                else:
                    raise Exception(f'Bounds must be "best" (non-sampled), "stddevs" (from samples, using stddevs for number), or "quantiles" (from samples, using quantiles), {bounds} not a valid choice.')
                
                if keep_raw:
                    res_unc[res.name][out_key]["raw"] = [sc.dcp(best_estimate)] + raw[out_key]
                
    # import pandas as pd   
    # df = pd.DataFrame(res_unc)
    # df.to_excel('reduce_test.xlsx')
    return res_unc


def write_results(results, reduced_results={}, projname=None, filename=None, folder=None, full_outcomes=False):
    """Writes outputs and program allocations to an xlsx book.
    For each scenario, book will include:
        - sheet called 'outcomes' which contains all outputs over time
        - sheet called 'budget and coverage' which contains all program cost and coverages over time"""
    if reduced_results:
        filepath = write_reduced_results(results, reduced_results, projname=projname, filename=filename, folder=folder)
        if not full_outcomes:
            return filepath
        filename = "full_" + filename

    years = results[0].years
    rows, filepath, outputs, outcomes, sheetnames, nullrow, allformats, alldata = _write_results_outcomes(projname, filename, folder, years)

    ### Outcomes sheet
    headers = [["Scenario", "Outcome"] + years + ["Cumulative"]]
    for r, res in enumerate(results):
        if res.name != "Excess budget":
            out = res.get_outputs(outcomes, seq=True, pretty=True)
            # print(out)
            for o, outcome in enumerate(rows):
                name = [res.name] if o == 0 else [""]
                thisout = out[o]
                if "prev" in outcome.lower():
                    cumul = "N/A"
                elif "mortality" in outcome.lower():
                    cumul = "N/A"
                else:
                    cumul = sum(thisout)
                outputs.append(name + [outcome] + list(thisout) + [cumul])
            outputs.append(nullrow)
    data = headers + outputs
    alldata.append(data)

    nrows, ncols, formatdata, allformats, outputs, headers = _write_results_costcov(data, allformats, years)

    for r, res in enumerate(results):
        if res.name != "Excess budget":
            rows = res.programs.keys()
            spend = res.get_allocs(ref=True)
            cov = res.get_covs(unrestr=True)
            # print(spend)
            # collate coverages first
            for r, prog in enumerate(rows):
                name = [res.name] if r == 0 else [""]
                costcov = res.programs[prog].costtype
                thiscov = cov[prog]
                outputs.append(name + [prog] + ["Coverage"] + [costcov] + list(thiscov))
            # collate spending second
            for r, prog in enumerate(rows):
                thisspend = spend[prog]
                costcov = res.programs[prog].costtype
                outputs.append([""] + [prog] + ["Budget"] + [costcov] + list(thisspend))
            outputs.append(nullrow)
        else:
            spend = res.get_allocs(ref=True)
            thisspend = spend["Excess budget not allocated"]
            outputs.append(["Excess budget not allocated"] + ["N/A"] + ["Budget"] + ["N/A"] + list(thisspend))
            outputs.append(nullrow)
    data = headers + outputs
    alldata.append(data)

    _write_results_finalise(data, allformats, filename, alldata, sheetnames)

    return filepath


def write_reduced_results(results, reduced_results, projname=None, filename=None, folder=None):
    """Writes outputs and program allocations to an xlsx book.
    For each scenario, book will include:
        - sheet called 'outcomes' which contains all outputs over time
        - sheet called 'budget and coverage' which contains all program cost and coverages over time"""

    estimate_labels = list(reduced_results[list(reduced_results.keys())[0]][list(reduced_results[list(reduced_results.keys())[0]].keys())[0]].keys())
    years = results[0].years
    rows, filepath, outputs, outcomes, sheetnames, nullrow, allformats, alldata = _write_results_outcomes(projname, filename, folder, years)

    ### Outcomes sheet
    headers = [["Scenario", "Estimate", "Outcome"] + years + ["Cumulative"]]
    for r, res in enumerate(reduced_results):
        for esti in estimate_labels:
            if res != "Excess budget":
                out = []
                for measure in list(reduced_results[res].keys()):
                    out.append(reduced_results[res][measure][esti])
                    # print(out)
                for o, outcome in enumerate(rows):
                    name = [res] if o == 0 else [""]
                    thisout = out[o]
                    if "prev" in outcome.lower():
                        cumul = "N/A"
                    elif "mortality" in outcome.lower():
                        cumul = "N/A"
                    else:
                        cumul = sum(thisout)
                    outputs.append(name + [esti] + [outcome] + list(thisout) + [cumul])
                outputs.append(nullrow)
    data = headers + outputs
    alldata.append(data)

    nrows, ncols, formatdata, allformats, outputs, headers = _write_results_costcov(data, allformats, years)

    ### Cost & coverage sheet
    # this is grouped not by program, but by coverage and cost (within each scenario)

    for r, res in enumerate(results):
        if res.name != "Excess budget" and "#" not in res.name:
            rows = res.programs.keys()
            spend = res.get_allocs(ref=True)
            cov = res.get_covs(unrestr=True)
            # print(spend)
            # collate coverages first
            for p, prog in enumerate(rows):
                name = [res.name] if p == 0 else [""]
                costcov = res.programs[prog].costtype
                thiscov = cov[prog]
                outputs.append(name + [prog] + ["Coverage"] + [costcov] + list(thiscov))
            # collate spending second
            for p, prog in enumerate(rows):
                thisspend = spend[prog]
                costcov = res.programs[prog].costtype
                outputs.append([""] + [prog] + ["Budget"] + [costcov] + list(thisspend))
            outputs.append(nullrow)
        elif "#" not in res.name:
            spend = res.get_allocs(ref=True)
            thisspend = spend["Excess budget not allocated"]
            outputs.append(["Excess budget not allocated"] + ["N/A"] + ["Budget"] + ["N/A"] + list(thisspend))
            outputs.append(nullrow)
    data = headers + outputs
    alldata.append(data)

    _write_results_finalise(data, allformats, filename, alldata, sheetnames)

    return filepath


def _write_results_outcomes(projname, filename, folder, years):
    from .version import version
    from datetime import date

    if projname is None:
        projname = ""
    outcomes = default_trackers()
    labs = pretty_labels()
    rows = [labs[out] for out in outcomes]
    if filename is None:
        filename = "outputs.xlsx"
    filepath = sc.makefilepath(filename=filename, folder=folder, ext="xlsx", default="%s outputs.xlsx" % projname)
    outputs = []
    sheetnames = ["Version", "Outcomes", "Budget & coverage"]
    alldata = []
    allformats = []
    # print(results[1])
    nullrow = [""] * len(years)
    ### Version sheet
    data = [["Version", "Date"], [version, date.today()]]
    alldata.append(data)

    # Formatting
    nrows = len(data)
    ncols = len(data[0])
    formatdata = np.zeros((nrows, ncols), dtype=object)
    formatdata[:, :] = "plain"  # Format data as plain
    formatdata[:, 0] = "bold"  # Left side bold
    formatdata[0, :] = "header"  # Top with green header
    allformats.append(formatdata)

    return rows, filepath, outputs, outcomes, sheetnames, nullrow, allformats, alldata


def _write_results_costcov(data, allformats, years):
    # Formatting
    nrows = len(data)
    ncols = len(data[0])
    formatdata = np.zeros((nrows, ncols), dtype=object)
    formatdata[:, :] = "plain"  # Format data as plain
    formatdata[:, 0] = "bold"  # Left side bold
    formatdata[0, :] = "header"  # Top with green header
    allformats.append(formatdata)

    outputs = []
    headers = [["Scenario", "Program", "Type", "Cost-coverage type"] + years]

    return nrows, ncols, formatdata, allformats, outputs, headers


def _write_results_finalise(data, allformats, filename, alldata, sheetnames):
    # Formatting
    nrows = len(data)
    ncols = len(data[0])
    formatdata = np.zeros((nrows, ncols), dtype=object)
    formatdata[:, :] = "plain"  # Format data as plain
    formatdata[:, 0] = "bold"  # Left side bold
    formatdata[0, :] = "header"  # Top with green header
    allformats.append(formatdata)

    formats = {"header": {"bold": True, "bg_color": "#3c7d3e", "color": "#ffffff"}, "plain": {}, "bold": {"bold": True}}
    sc.savespreadsheet(filename=filename, data=alldata, sheetnames=sheetnames, formats=formats, formatdata=allformats)

    return
