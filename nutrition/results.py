import sciris as sc
from .utils import default_trackers, pretty_labels
import numpy as np
from . import project
from . import ui

class ScenResult(sc.prettyobj):
    def __init__(self, name, model_name, model, obj=None, mult=None):
        self.name = name
        self.model_name = model_name
        self.model = model
        self.prog_info = self.model.prog_info # provides access to costing info
        self.programs = self.prog_info.programs
        self.pops = self.model.pops
        self.mult = mult
        self.obj = obj
        self.years = list(range(model.t[0], model.t[1]+1))
        self.uid = sc.uuid()
        self.created = sc.now()
        self.modified = sc.now()
        
    def model_attr(self):
        return self.model.__dict__
    
    def get_outputs(self, outcomes=None, seq=False, asdict=False, pretty=False):
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
            for o,outcome in enumerate(outcomes):
                output[outcome] = outs[o]
        else: 
            output = outs
            if pretty and not seq:
                prettyvals = []
                for out, val in zip(outcomes, output):
                    if 'prev' in out:
                        prettyval = round(val* 100, 2)
                    else:
                        prettyval = round(val,0)
                    prettyvals.append(prettyval)
                output = prettyvals
        return output

    def get_allocs(self, ref=True, current=False):
        allocs = sc.odict()
        for name, prog in self.programs.items():
            spend = prog.annual_spend
            if not ref and prog.reference:
                spend -= spend[0] # baseline year is reference spending, subtracted from every year
            if current:
                spend = spend[:1]
            # if not fixed and not prog.reference:
            #     spend -= spend[0]
            allocs[name] = spend
        return allocs

    def get_covs(self, ref=True, unrestr=True):
        covs = sc.odict()
        for name, prog in self.programs.iteritems():
            cov = prog.get_cov(unrestr=unrestr)
            if not ref and prog.reference:
                cov -= cov[0] # baseline year is reference cov, subtracted from every year
            covs[name] = cov
        return covs

    def get_freefunds(self):
        free = self.model.prog_info.free
        if self.mult is not None:
            free *= self.mult
        return free

    def get_currspend(self):
        return self.model.prog_info.curr

    def get_childscens(self):
        """ For calculating the impacts of each scenario with single intervention set to 0 coverage """
        cov = [0]
        allkwargs = []
        progset = self.programs.keys()
        base_progset = self.prog_info.base_progset()
        # zero cov scen
        kwargs = {'name': 'Scenario overall',
                  'model_name': self.model_name,
                  'scen_type': 'budget',
                  'progvals': {prog: cov for prog in base_progset}}
        allkwargs.append(kwargs)
        # scale down each program to 0 individually
        progvals = self.get_allocs(ref=True)
        for prog in progset:
            new_progvals = sc.dcp(progvals)
            new_progvals[prog] = cov
            kwargs = {'name': prog,
                      'model_name': self.model_name,
                      'scen_type': 'budget',
                      'progvals': new_progvals}
            allkwargs.append(kwargs)
        return allkwargs

    def plot(self, toplot=None):
        from .plotting import make_plots # This is here to avoid a circular import
        figs = make_plots(self, toplot=toplot)
        return figs

def write_results(results, projname=None, filename=None, folder=None):
    """ Writes outputs and program allocations to an xlsx book.
    For each scenario, book will include:
        - sheet called 'outcomes' which contains all outputs over time
        - sheet called 'budget and coverage' which contains all program cost and coverages over time """
    if projname is None: projname = ''
    outcomes = [
        'stunted',
        'wasted',
        'child_anaemic',
        'child_deaths'
    ]
    #default_trackers()
    labs = pretty_labels()
    rows = [labs[out] for out in outcomes]
    if filename is None: filename = 'outputs.xlsx'
    filepath = sc.makefilepath(filename=filename, folder=folder, ext='xlsx', default='%s outputs.xlsx' % projname)
    outputs = []
    sheetnames = ['Outcomes', 'Budget & coverage']
    alldata = []
    allformats = []
    years = results[0].years
    nullrow = [''] * len(years)

    ### Outcomes sheet
    headers = [['Scenario', 'Outcome'] + years + ['Cumulative']]
    for r, res in enumerate(results):
        out = res.get_outputs(outcomes, seq=True, pretty=True)
        for o, outcome in enumerate(rows):
            name = [res.name] if o == 0 else ['']
            thisout = out[o]
            if 'prev' in outcome.lower():
                cumul = 'N/A'
            elif 'mortality' in outcome.lower():
                cumul = 'N/A'
            else:
                cumul = sum(thisout)
            outputs.append(name + [outcome] + list(thisout) + [cumul])
        outputs.append(nullrow)
    data = headers + outputs
    alldata.append(data)

    # Formatting
    nrows = len(data)
    ncols = len(data[0])
    formatdata = np.zeros((nrows, ncols), dtype=object)
    formatdata[:, :] = 'plain'  # Format data as plain
    formatdata[:, 0] = 'bold'  # Left side bold
    formatdata[0, :] = 'header'  # Top with green header
    allformats.append(formatdata)

    ### Cost & coverage sheet
    # this is grouped not by program, but by coverage and cost (within each scenario)
    outputs = []
    headers = [['Scenario', 'Program', 'Type'] + years]
    for r, res in enumerate(results):
        rows = res.programs.keys()
        spend = res.get_allocs(ref=True)
        cov = res.get_covs(unrestr=False)
        # collate coverages first
        for r, prog in enumerate(rows):
            name = [res.name] if r == 0 else ['']
            thiscov = cov[prog]
            outputs.append(name + [prog] + ['Coverage'] + list(thiscov))
        # collate spending second
        for r, prog in enumerate(rows):
            thisspend = spend[prog]
            outputs.append([''] + [prog] + ['Budget'] + list(thisspend))
        outputs.append(nullrow)
    data = headers + outputs
    alldata.append(data)

    # Formatting
    nrows = len(data)
    ncols = len(data[0])
    formatdata = np.zeros((nrows, ncols), dtype=object)
    formatdata[:, :] = 'plain'  # Format data as plain
    formatdata[:, 0] = 'bold'  # Left side bold
    formatdata[0, :] = 'header'  # Top with green header
    allformats.append(formatdata)

    formats = {
        'header': {'bold': True, 'bg_color': '#3c7d3e', 'color': '#ffffff'},
        'plain': {},
        'bold': {'bold': True}}
    sc.savespreadsheet(filename=filename, data=alldata, sheetnames=sheetnames, formats=formats, formatdata=allformats)
    return filepath

def write_results_collected(results, combs, countries, projname=None, filename=None, folder=None, short_names=None):
    """ Writes outputs and program allocations to an xlsx book.
    For each scenario, book will include:
        - sheet called 'outcomes' which contains all outputs over time
        - sheet called 'budget and coverage' which contains all program cost and coverages over time """
    num_combs = combs
    num_countries = countries
    if projname is None: projname = ''
    outcomes = [
        'child_deaths',
        'stunted',
        'wasted',
        'child_anaemic'
    ]
    labs = pretty_labels()
    rows = [labs[out] for out in outcomes]
    if filename is None: filename = 'outputs.xlsx'
    filepath = sc.makefilepath(filename=filename, folder=folder, ext='xlsx', default='%s outputs.xlsx' % projname)
    outputs = []
    sheetnames = []
    for name in short_names:
        if isinstance(name, str):
            sheetnames.append(name)
        elif len(name) == 2:
            concat = name[0] + '_' + name[1]
            sheetnames.append(concat)
        else:
            concat = name[0] + '_' + name[1] + '_' + name[2]
            sheetnames.append(concat)
    alldata = []
    allformats = []
    years = results[0].years
    nullrow = [''] * len(years)

    ### Outcomes sheet
    for comb_num in list(range(num_combs)):
        headers = [['Country', 'Outcome'] + years + ['Cumulative']]
        for r, res in enumerate(results[comb_num * num_countries: (comb_num + 1) * num_countries]):
            out = res.get_outputs(outcomes, seq=True, pretty=True)
            for o, outcome in enumerate(rows):
                name = [res.name] if o == 0 else ['']
                thisout = out[o]
                if 'prev' in outcome.lower():
                    cumul = 'N/A'
                elif 'mortality' in outcome.lower():
                    cumul = 'N/A'
                else:
                    cumul = sum(thisout)
                outputs.append(name + [outcome] + list(thisout) + [cumul])
            outputs.append(nullrow)
        data = headers + outputs
        alldata.append(data)
        outputs = []

        # Formatting
        nrows = len(data)
        ncols = len(data[0])
        formatdata = np.zeros((nrows, ncols), dtype=object)
        formatdata[:, :] = 'plain'  # Format data as plain
        formatdata[:, 0] = 'bold'  # Left side bold
        formatdata[0, :] = 'header'  # Top with green header
        allformats.append(formatdata)
        del data
    '''
    ### Cost & coverage sheet
    # this is grouped not by program, but by coverage and cost (within each scenario)
    outputs = []
    headers = [['Scenario', 'Program', 'Type'] + years]
    for r, res in enumerate(results):
        rows = res.programs.keys()
        spend = res.get_allocs(ref=True)
        cov = res.get_covs(unrestr=False)
        # collate coverages first
        for r, prog in enumerate(rows):
            name = [res.name] if r == 0 else ['']
            thiscov = cov[prog]
            outputs.append(name + [prog] + ['Coverage'] + list(thiscov))
        # collate spending second
        for r, prog in enumerate(rows):
            thisspend = spend[prog]
            outputs.append([''] + [prog] + ['Budget'] + list(thisspend))
        outputs.append(nullrow)
    data = headers + outputs
    alldata.append(data)

    # Formatting
    nrows = len(data)
    ncols = len(data[0])
    formatdata = np.zeros((nrows, ncols), dtype=object)
    formatdata[:, :] = 'plain'  # Format data as plain
    formatdata[:, 0] = 'bold'  # Left side bold
    formatdata[0, :] = 'header'  # Top with green header
    allformats.append(formatdata)
    '''
    formats = {
        'header': {'bold': True, 'bg_color': '#3c7d3e', 'color': '#ffffff'},
        'plain': {},
        'bold': {'bold': True}}
    sc.savespreadsheet(filename=filename, data=alldata, sheetnames=sheetnames, formats=formats, formatdata=allformats)
    return filepath

def write_cost_effectiveness(cost_effectiveness_data, projname=None, filename=None, folder=None):
    filepath = sc.makefilepath(filename=filename, folder=folder, ext='xlsx', default='%s outputs.xlsx' % projname)
    outputs = []
    sheetnames = 'Cost effectiveness'
    alldata = []
    allformats = []

    ### Outcomes sheet
    headers = [['Scenario', 'Outcome']]
    for r, res in enumerate(cost_effectiveness_data.keys()):
        for o, outcome in enumerate(res):
            if o == 0:
                outputs.append([res] + [outcome])
            else:
                outputs.append([''] + [outcome])
    data = headers + outputs
    alldata.append(data)

    # Formatting
    nrows = len(data)
    ncols = len(data[0])
    formatdata = np.zeros((nrows, ncols), dtype=object)
    formatdata[:, :] = 'plain'  # Format data as plain
    formatdata[:, 0] = 'bold'  # Left side bold
    formatdata[0, :] = 'header'  # Top with green header
    allformats.append(formatdata)
    formats = {
        'header': {'bold': True, 'bg_color': '#3c7d3e', 'color': '#ffffff'},
        'plain': {},
        'bold': {'bold': True}}
    sc.savespreadsheet(filename=filename, data=alldata, sheetnames=sheetnames, formats=formats, formatdata=allformats)
    return filepath

def run_analysis(country):
    cov = 1.0
    progval = sc.odict(
        {'Balanced energy-protein supplementation': cov, 'Calcium supplementation': cov, 'Cash transfers': cov,
         'Delayed cord clamping': cov, 'IFA fortification of maize': cov, 'IFAS (community)': cov,
         'IFAS for pregnant women (community)': cov, 'IPTp': cov, 'Iron and iodine fortification of salt': cov,
         'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
         'Long-lasting insecticide-treated bednets': cov, 'Mg for eclampsia': cov, 'Mg for pre-eclampsia': cov,
         'Micronutrient powders': cov, 'Multiple micronutrient supplementation': cov,
         'Oral rehydration salts': cov, 'Public provision of complementary foods': cov, 'Treatment of SAM': cov,
         'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov, 'Zinc supplementation': cov})

    prog_list = sc.dcp(progval.keys())

    stunt_progs = sc.odict({'Balanced energy-protein supplementation': cov, 'Cash transfers': cov,
                            'IFAS for pregnant women (community)': cov, 'IPTp': cov,
                            'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                            'Long-lasting insecticide-treated bednets': cov,
                            'Multiple micronutrient supplementation': cov,
                            'Oral rehydration salts': cov, 'Public provision of complementary foods': cov,
                            'Treatment of SAM': cov,
                            'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov,
                            'Zinc supplementation': cov})
    wast_progs = sc.odict({'Balanced energy-protein supplementation': cov, 'Cash transfers': cov,
                           'IFAS for pregnant women (community)': cov, 'IPTp': cov,
                           'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                           'Long-lasting insecticide-treated bednets': cov,
                           'Multiple micronutrient supplementation': cov,
                           'Oral rehydration salts': cov, 'Public provision of complementary foods': cov,
                           'Treatment of SAM': cov,
                           'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov,
                           'Zinc supplementation': cov})
    anaem_progs = sc.odict({'Cash transfers': cov,
                            'Delayed cord clamping': cov, 'IFA fortification of maize': cov,
                            'Iron and iodine fortification of salt': cov,
                            'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                            'Long-lasting insecticide-treated bednets': cov,
                            'Micronutrient powders': cov, 'Oral rehydration salts': cov,
                            'Public provision of complementary foods': cov,
                            'Treatment of SAM': cov, 'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov,
                            'Zinc supplementation': cov})
    mort_progs = sc.odict({'Cash transfers': cov, 'IFA fortification of maize': cov,
                           'IFAS for pregnant women (community)': cov, 'IPTp': cov,
                           'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                           'Long-lasting insecticide-treated bednets': cov,
                           'Multiple micronutrient supplementation': cov,
                           'Oral rehydration salts': cov, 'Public provision of complementary foods': cov,
                           'Treatment of SAM': cov,
                           'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov,
                           'Zinc supplementation': cov})

    tol = [20000, 200000, 50000, 150000]
    p = project.Project(country + ' scaled up')
    p.load_data(country='costed_baseline_' + country, name=country, time_trend=False)
    baseline = p.run_baseline(country, prog_list)
    stunting_CE, stunting_cost, stunting_impact, best_stunting_progs = calc_CE(country, 'stunting', p, baseline,
                                                                               stunt_progs, prog_list, tol[0])
    wasting_CE, wasting_cost, wasting_impact, best_wasting_progs = calc_CE(country, 'wasting', p, baseline,
                                                                           wast_progs, prog_list, tol[1])
    anaemia_CE, anaemia_cost, anaemia_impact, best_anaemia_progs = calc_CE(country, 'anaemia', p, baseline,
                                                                               anaem_progs, prog_list, tol[2])
    mortality_CE, mortality_cost, mortality_impact, best_mortality_progs = calc_CE(country, 'mortality', p, baseline,
                                                                               mort_progs, prog_list, tol[3])
    CE_data = [[stunting_CE[:-1], stunting_cost[:-1], stunting_impact[:-1], best_stunting_progs[:-1]],
               [wasting_CE[:-1], wasting_cost[:-1], wasting_impact[:-1], best_wasting_progs[:-1]],
               [anaemia_CE[:-1], anaemia_cost[:-1], anaemia_impact[:-1], best_anaemia_progs[:-1]],
               [mortality_CE[:-1], mortality_cost[:-1], mortality_impact[:-1], best_mortality_progs[:-1]]]
    return CE_data

def run_total_analysis(country_list):
    cov = 1.0
    progval = sc.odict(
        {'Balanced energy-protein supplementation': cov, 'Calcium supplementation': cov, 'Cash transfers': cov,
         'Delayed cord clamping': cov, 'IFA fortification of maize': cov, 'IFAS (community)': cov,
         'IFAS for pregnant women (community)': cov, 'IPTp': cov, 'Iron and iodine fortification of salt': cov,
         'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
         'Long-lasting insecticide-treated bednets': cov, 'Mg for eclampsia': cov, 'Mg for pre-eclampsia': cov,
         'Micronutrient powders': cov, 'Multiple micronutrient supplementation': cov,
         'Oral rehydration salts': cov, 'Public provision of complementary foods': cov, 'Treatment of SAM': cov,
         'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov, 'Zinc supplementation': cov})

    prog_list = sc.dcp(progval.keys())

    stunt_progs = sc.odict({'IFAS for pregnant women (community)': cov, 'IPTp': cov,
                            'IYCF 1': cov, 'Multiple micronutrient supplementation': cov,
                            'Public provision of complementary foods': cov,
                            'Treatment of SAM': cov,
                            'Vitamin A supplementation': cov, 'Zinc supplementation': cov})
    wast_progs = sc.odict({'Cash transfers': cov, 'Vitamin A supplementation': cov, 'Zinc supplementation': cov})
    anaem_progs = sc.odict({'IFA fortification of maize': cov, 'Iron and iodine fortification of salt': cov,
                            'Long-lasting insecticide-treated bednets': cov,
                            'Micronutrient powders': cov})
    mort_progs = sc.odict({'IFA fortification of maize': cov,
                           'IFAS for pregnant women (community)': cov, 'IPTp': cov,
                           'IYCF 1': cov, 'Kangaroo mother care': cov, 'Long-lasting insecticide-treated bednets': cov,
                           'Multiple micronutrient supplementation': cov,
                           'Oral rehydration salts': cov, 'Public provision of complementary foods': cov,
                           'Treatment of SAM': cov,
                           'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov,
                           'Zinc supplementation': cov})


    programs = [stunt_progs, wast_progs, anaem_progs, mort_progs]
    tol = [20000, 200000, 50000, 150000]
    p = project.Project('scaled up')
    iptp_trigger = sc.odict()
    for country in country_list:
        p.load_data(country='costed_baseline_' + country, name=country, time_trend=False)
        if p.datasets[-1].demo_data.demo['Percentage of population at risk of malaria'] <= 0.005:
            iptp_trigger[country] = True
        else:
            iptp_trigger[country] = False
    for o, outcome in enumerate(['stunting', 'wasting']):#, 'anaemia', 'mortality']):
        effectiveness = 1.0
        baseline = 0
        objective_cost = []
        objective_impact = []
        objective_CE = []
        for country in country_list:
            if outcome == 'stunting':
                baseline += np.sum(p.run_baseline(country, prog_list).model.stunted)
            elif outcome == 'wasting':
                baseline += np.sum(p.run_baseline(country, prog_list).model.wasted)
            elif outcome == 'anaemia':
                baseline += np.sum(p.run_baseline(country, prog_list).model.child_anaemic)
            elif outcome == 'mortality':
                baseline += np.sum(p.run_baseline(country, prog_list).model.child_deaths)
        effective_progs = sc.odict()
        while effectiveness < tol[o] and programs[o]:
            trials = []
            trial = np.zeros(len(programs[o]))
            cost = np.zeros(len(programs[o]))
            for prog_num, prog in enumerate(programs[o].keys()):
                if prog == 'IPTp' or prog == 'Long-lasting insecticide-treated bednets':
                    trial_progs = sc.dcp(effective_progs)
                    trial_progs.append(prog, interp_cov(p, prog, [2018, 2024], cov))
                    scen_list = []
                    for c, country in enumerate(country_list):
                        kwargs = {'name': country + prog,
                                  'model_name': country,
                                  'scen_type': 'coverage',
                                  'progvals': trial_progs}
                        scen_list.append(ui.make_scens([kwargs]))
                    p.add_scens(scen_list)
                    p.run_scens_plus(prog_list, trial_progs)
                    for c, country in enumerate(country_list):
                        if not iptp_trigger[country]:
                            if outcome == 'stunting':
                                trial[prog_num] += np.sum(p.results['scens'][c].model.stunted)
                            elif outcome == 'wasting':
                                trial[prog_num] += np.sum(p.results['scens'][c].model.wasted)
                            elif outcome == 'anaemia':
                                trial[prog_num] += np.sum(p.results['scens'][c].model.child_anaemic)
                            elif outcome == 'mortality':
                                trial[prog_num] += np.sum(p.results['scens'][c].model.child_deaths)
                            cost[prog_num] += np.sum(p.results['scens'][c].programs[prog].annual_spend) - \
                                              (len(p.results['scens'][c].programs[prog].annual_spend)) * \
                                              p.results['scens'][c].programs[prog].annual_spend[0]
                        else:
                            if outcome == 'stunting':
                                trial[prog_num] += np.sum(p.run_baseline(country, prog_list).model.stunted)
                            elif outcome == 'wasting':
                                trial[prog_num] += np.sum(p.run_baseline(country, prog_list).model.wasted)
                            elif outcome == 'anaemia':
                                trial[prog_num] += np.sum(p.run_baseline(country, prog_list).model.child_anaemic)
                            elif outcome == 'mortality':
                                trial[prog_num] += np.sum(p.run_baseline(country, prog_list).model.child_deaths)

                else:
                    trial_progs = sc.dcp(effective_progs)
                    trial_progs.append(prog, interp_cov(p, prog, [2018, 2024], cov))
                    scen_list = []
                    for c, country in enumerate(country_list):
                        kwargs = {'name': country + prog,
                                  'model_name': country,
                                  'scen_type': 'coverage',
                                  'progvals': trial_progs}
                        scen_list.append(ui.make_scens([kwargs]))
                    p.add_scens(scen_list)
                    p.run_scens_plus(prog_list, trial_progs)
                    for c, country in enumerate(country_list):
                        if outcome == 'stunting':
                            trial[prog_num] += np.sum(p.results['scens'][c].model.stunted)
                        elif outcome == 'wasting':
                            trial[prog_num] += np.sum(p.results['scens'][c].model.wasted)
                        elif outcome == 'anaemia':
                            trial[prog_num] += np.sum(p.results['scens'][c].model.child_anaemic)
                        elif outcome == 'mortality':
                            trial[prog_num] += np.sum(p.results['scens'][c].model.child_deaths)
                        cost[prog_num] += np.sum(p.results['scens'][c].programs[prog].annual_spend) - \
                                          (len(p.results['scens'][c].programs[prog].annual_spend)) * \
                                          p.results['scens'][c].programs[prog].annual_spend[0]
                try:
                    trial_effectiveness = cost[prog_num] / (baseline - trial[prog_num])
                except RuntimeWarning:
                    trial_effectiveness = np.nan
                if trial_effectiveness >= 0:
                    trials.append(trial_effectiveness)
                    print(baseline, trial[prog_num], cost[prog_num], trial_effectiveness)
                else:
                    trials.append(np.nan)
            try:
                location = np.nanargmin(trials)
            except ValueError:
                break
            effective_progs.append(programs[o].keys()[location], interp_cov(p, programs[o].keys()[location], [2018, 2024], cov))
            effectiveness = trials[location]
            print(effectiveness, programs[o].keys()[location])
            objective_CE.append(effectiveness)
            objective_cost.append(cost[location])
            objective_impact.append(trial[location])
            baseline = trial[location]
            del programs[o][programs[o].keys()[location]]
        objective_progs = effective_progs.keys()
        if outcome == 'stunting':
            stunting_CE = objective_CE
            stunting_cost = objective_cost
            stunting_impact = objective_impact
            best_stunting_progs = objective_progs
        elif outcome == 'wasting':
            wasting_CE = objective_CE
            wasting_cost = objective_cost
            wasting_impact = objective_impact
            best_wasting_progs = objective_progs
        elif outcome == 'anaemia':
            anaemia_CE = objective_CE
            anaemia_cost = objective_cost
            anaemia_impact = objective_impact
            best_anaemia_progs = objective_progs
        elif outcome == 'mortality':
            mortality_CE = objective_CE
            mortality_cost = objective_cost
            mortality_impact = objective_impact
            best_mortality_progs = objective_progs
    CE_data = [[stunting_CE[:-1], stunting_cost[:-1], stunting_impact[:-1], best_stunting_progs[:-1]],
               [wasting_CE[:-1], wasting_cost[:-1], wasting_impact[:-1], best_wasting_progs[:-1]],
               [anaemia_CE[:-1], anaemia_cost[:-1], anaemia_impact[:-1], best_anaemia_progs[:-1]],
               [mortality_CE[:-1], mortality_cost[:-1], mortality_impact[:-1], best_mortality_progs[:-1]]]
    return CE_data


def calc_CE(country, objective, proj, baseline, progs, prog_list, tol):
    new_baseline = sc.dcp(baseline)
    p = proj
    effectiveness = 1.0
    programs = sc.dcp(progs)
    effective_progs = sc.odict()
    objective_cost = []
    objective_impact = []
    objective_CE = []
    while effectiveness < tol and programs:
        trials = []
        for prog in programs.keys():
            if prog == 'IPTp' or prog == 'Long-lasting insecticide-treated bednets':
                if p.datasets[-1].demo_data.demo['Percentage of population at risk of malaria'] <= 0.005:
                    trial_progs = sc.dcp(effective_progs)
                    trial_progs.append(prog, interp_cov(p, prog, [2018, 2024], 0.95))
                    trials.append(np.nan)
                    continue
            trial_progs = sc.dcp(effective_progs)
            trial_progs.append(prog, interp_cov(p, prog, [2018, 2024], 0.95))
            kwargs = {'name': country,
                      'model_name': country,
                      'scen_type': 'coverage',
                      'progvals': trial_progs}
            scen_list = ui.make_scens([kwargs])
            p.add_scens(scen_list)
            p.run_scens_plus(prog_list, trial_progs)
            if objective == 'stunting':
                try:
                    trial_effectiveness = (np.sum(p.results['scens'][-1].programs[prog].annual_spend) - \
                                          (len(p.results['scens'][-1].programs[prog].annual_spend)) * \
                                          p.results['scens'][-1].programs[prog].annual_spend[0]) /\
                                          (np.sum(new_baseline.model.stunted) - np.sum(p.results['scens'][-1].model.stunted))
                except RuntimeWarning:
                    trial_effectiveness = np.nan
            elif objective == 'wasting':
                try:
                    trial_effectiveness = (np.sum(p.results['scens'][-1].programs[prog].annual_spend) - \
                                          (len(p.results['scens'][-1].programs[prog].annual_spend)) * \
                                          p.results['scens'][-1].programs[prog].annual_spend[0]) /\
                                          (np.sum(new_baseline.model.wasted) - np.sum(p.results['scens'][-1].model.wasted))
                except RuntimeWarning:
                    trial_effectiveness = np.nan
            elif objective == 'anaemia':
                try:
                    trial_effectiveness = (np.sum(p.results['scens'][-1].programs[prog].annual_spend) - \
                                          (len(p.results['scens'][-1].programs[prog].annual_spend)) * \
                                          p.results['scens'][-1].programs[prog].annual_spend[0]) /\
                                          (np.sum(new_baseline.model.child_anaemic) - np.sum(p.results['scens'][-1].model.child_anaemic))
                except RuntimeWarning:
                    trial_effectiveness = np.nan
            elif objective == 'mortality':
                try:
                    trial_effectiveness = (np.sum(p.results['scens'][-1].programs[prog].annual_spend) - \
                                          (len(p.results['scens'][-1].programs[prog].annual_spend)) * \
                                          p.results['scens'][-1].programs[prog].annual_spend[0]) /\
                                          (np.sum(new_baseline.model.child_deaths) - np.sum(p.results['scens'][-1].model.child_deaths))
                except RuntimeWarning:
                    trial_effectiveness = np.nan
            if trial_effectiveness >= 0:
                trials.append(trial_effectiveness)
            else:
                trials.append(np.nan)
        try:
            location = np.nanargmin(trials)
        except ValueError:
            break
        effective_progs.append(programs.keys()[location], interp_cov(p, programs.keys()[location], [2018, 2024], 0.95))
        kwargs = {'name': country,
                  'model_name': country,
                  'scen_type': 'coverage',
                  'progvals': effective_progs}
        scen_list = ui.make_scens([kwargs])
        p.add_scens(scen_list)
        p.run_scens_plus(prog_list, effective_progs)
        effectiveness = trials[location]
        print(effectiveness, programs.keys()[location])
        objective_CE.append(effectiveness)
        objective_cost.append((np.sum(p.results['scens'][-1].programs[programs.keys()[location]].annual_spend) -
                              (len(p.results['scens'][-1].programs[programs.keys()[location]].annual_spend)) *
                              p.results['scens'][-1].programs[programs.keys()[location]].annual_spend[0]))
        if objective == 'stunting':
            objective_impact.append(np.sum(baseline.model.stunted) - np.sum(p.results['scens'][-1].model.stunted))
        elif objective == 'wasting':
            objective_impact.append(np.sum(baseline.model.wasted) - np.sum(p.results['scens'][-1].model.wasted))
        elif objective == 'anaemia':
            objective_impact.append(np.sum(baseline.model.child_anaemic) - np.sum(p.results['scens'][-1].model.child_anaemic))
        elif objective == 'mortality':
            objective_impact.append(np.sum(baseline.model.child_deaths) - np.sum(p.results['scens'][-1].model.child_deaths))
        new_baseline = p.results['scens'][-1]
        del programs[programs.keys()[location]]
    objective_progs = effective_progs.keys()
    return objective_CE, objective_cost, objective_impact, objective_progs

def interp_cov(project, program, years, target):
    interp = []
    timeskip = years[1] - years[0]
    baseline_cov = project.models[-1].prog_info.programs[program].base_cov
    if baseline_cov >= target:
        return baseline_cov
    else:
        diff = target - baseline_cov
        for year in list(range(timeskip + 1)):
            interp.append(baseline_cov + year * diff / timeskip)
        return interp