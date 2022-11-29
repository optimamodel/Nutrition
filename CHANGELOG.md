
### Changelog

#### [2.0.6]
Lock databooks in all languages


#### [2.0.5]
Add dependencies to scenarios
Fix translation for management of MAM

#### [2.0.4]

Add additional outputs for 
- alive and non-anaemic children turning age 5
- alive and non-wasted children turning age 5
- alive and non-stunted, non-wasted and non-anaemic children turnign age 5

Fix handling of multiple constraints for interventions. Exclusion dependencies can now be entered as a list.

Fix budget multipliest so that "1.5" multiplier is 1.5 times total budget, not 1.5 times free budget.


#### [2.0.0]

**Breaking change** - projects from Optima Nutrition 1.* must be recreated by reloading the databooks into Optima Nutrition 2.*

- Added localization functionality to allow translation of the tool into different languages
- Removed `nu.ONException`, now a standard `Exception` is raised
- `nu.ONpath` is now a `Path` object rather than a function. Instead of `nu.ONpath('foo')`, use `nu.ONpath/'foo'`
- Input files are now stored within locales by default e.g. `inputs/en/demo_region1_input.xlsx`. Files are read by locale by default
- Times are captured in UTC and displayed in local time to users. Legacy projects may have times that show up offset by the timezone because they were previously captured in local time

#### [1.7.4] - 2022-03-09

- Corrected Zn + ORS treatemnt for only severe diarrhoea

#### [1.7.2] - 2021-19-10

- Fixed incorrect initialization of non-pregnant women population sizes

#### [1.7.1] - 2021-02-09

- Particle swarm optimization step removed from default optimizations in order to reduce variability in allocation when similar budget sizes are optimized.
- Default maximum run time for adaptive stochastic descent algorithm increased to accommodate the removal of the PSO step
- Optima Nutrition version number and date added to standard results output in 'Version' sheet

#### [1.7.0] - 2020-06-18

- Treatment of SAM, ORS, ORS + Zinc intervention unit costs are now per treatment, rather than average per child per year
- Coverage entered for treatment of SAM, ORS, ORS + Zinc, pre-eclampsia, eclampsia as percentage of episodes covered
- Geospatial outputs include baseline estimates for each region
- Databooks include inputs for the prevalence of pre-eclampsia and eclampsia, with global averages applied for legacy projects
- Scenarios and optimisations now plot "Excess budget not allocated" when available funds are greater than all interventions
- Output exports include the type of cost-coverage curve for each intervention
- Bugfix: when changing databooks in scenario and optimisation definitions, inputs are no longer reset
- Bugfix: changing budget reallocation restrictions, in sequential optimisations, updates properly

#### [1.6.6] - 2020-04-29

- Added Web interface changelog
