
### Changelog

#### [1.6.6] - 2020-04-29

- Added Web interface changelog

#### [1.7.0] - 2020-06-18

- Treatment of SAM, ORS, ORS + Zinc intervention unit costs are now per treatment, rather than average per child per year
- Coverage entered for treatment of SAM, ORS, ORS + Zinc, pre-eclampsia, eclampsia as percentage of episodes covered
- Geospatial outputs include baseline estimates for each region
- Databooks include inputs for the prevalence of pre-eclampsia and eclampsia, with global averages applied for legacy projects
- Scenarios and optimisations now plot "Excess budget not allocated" when available funds are greater than all interventions
- Output exports include the type of cost-coverage curve for each intervention
- Bugfix: when changing databooks in scenario and optimisation definitions, inputs are no longer reset
- Bugfix: changing budget reallocation restrictions, in sequential optimisations, updates properly

#### [1.7.1] - 2021-02-09

- Particle swarm optimization step removed from default optimizations in order to reduce variability in allocation when similar budget sizes are optimized.
- Default maximum run time for adaptive stochastic descent algorithm increased to accommodate the removal of the PSO step
- Optima Nutrition version number and date added to standard results output in 'Version' sheet

#### [1.7.2] - 2021-19-10

- Fixed incorrect initialization of non-pregnant women population sizes