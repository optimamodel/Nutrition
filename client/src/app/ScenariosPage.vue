<!--
Scenarios page

Last update: 2019feb11
-->

<template>
  <div>

    <div v-if="projectID ==''">
      <div style="font-style:italic">
        <p>{{ $t("common.no_project_loaded") }}.</p>
      </div>
    </div>

    <div v-else-if="!hasData">
      <div style="font-style:italic">
        <p>{{ $t("common.no_data_loaded") }}</p>
      </div>
    </div>

    <div v-else>
      <div class="card">
        <help reflink="scenarios" :label='$t("scenarios.Define scenarios")'></help>
        <table class="table table-bordered table-hover table-striped" style="width: 100%">
          <thead>
          <tr>
            <th style="text-align:center">
              <input type="checkbox" @click="modalDeselectAllScens()" v-model="allActive"/>
            </th>
            <th>{{ $t("Name") }}</th>
            <th>{{ $t("Type") }}</th>
            <th>{{ $t("Databook") }}</th>
            <th>{{ $t("Actions") }}</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="scenSummary in scenSummaries">
            <td style="text-align: center">
              <input type="checkbox" @click="uncheckSelectAll()" v-model="scenSummary.active"/>
            </td>
            <td>
              <b>{{ scenSummary.name }}</b>
            </td>
            <td>
              {{ scenSummary.scen_type === "budget" ? $t("scenarios.budget") : $t("scenarios.coverage") }}
            </td>
            <td>
              {{ scenSummary.model_name }}
            </td>
            <td style="white-space: nowrap">
              <button class="btn btn-icon" @click="editScenModal(scenSummary)" :data-tooltip='$t("scenarios.Edit scenario")'><i class="ti-pencil"></i></button>
              <button class="btn btn-icon" @click="copyScen(scenSummary)"      :data-tooltip='$t("scenarios.Copy scenario")'><i class="ti-files"></i></button>
              <button class="btn btn-icon" @click="convertScen(scenSummary)"   :data-tooltip='$t("scenarios.Convert scenario type")'><i class="ti-control-shuffle"></i></button>
              <button class="btn btn-icon" @click="deleteScen(scenSummary)"    :data-tooltip='$t("scenarios.Delete scenario")'><i class="ti-trash"></i></button>
            </td>
          </tr>
          </tbody>
        </table>

        <div>
            <input type="checkbox" id="costeff_checkbox" v-model="calculateCostEff"/>
            <label for="costeff_checkbox">{{ $t("scenarios.Perform intervention cost-effectiveness analysis") }}</label>
        </div>

        <div>
          <button class="btn __green" :disabled="!scenariosLoaded || !anySelected" @click="runScens(0)">{{ $t("scenarios.Run scenarios") }}</button>
          <button class="btn __green" :disabled="!scenariosLoaded || calculateCostEff || !anySelected" @click="UncertScensModal(10)">{{ $t("scenarios.Run scenarios with uncertainty") }}</button>
          <button class="btn __blue"  :disabled="!scenariosLoaded" @click="addScenModal('coverage')">{{ $t("scenarios.Add coverage scenario") }}</button>
          <button class="btn __blue"  :disabled="!scenariosLoaded" @click="addScenModal('budget')">{{ $t("scenarios.Add budget scenario") }}</button>
        </div>
      </div>
    </div>

    <!-- START RESULTS CARD -->
    <div class="card full-width-card" v-if="hasGraphs">
      <div class="calib-title">
        <help reflink="results-plots" label="Results"></help>
        <div>
          <button class="btn btn-icon" @click="scaleFigs(0.9)" :data-tooltip='$t("Zoom out")'>&ndash;</button>
          <button class="btn btn-icon" @click="scaleFigs(1.0)" :data-tooltip='$t("common.Reset zoom")'><i class="ti-zoom-in"></i></button>
          <button class="btn btn-icon" @click="scaleFigs(1.1)" :data-tooltip='$t("common.Zoom in")'>+</button>
          &nbsp;&nbsp;&nbsp;
          <button class="btn" @click="exportGraphs(projectID, 'scens')">{{ $t("common.Export plots") }}</button>
          <button class="btn" @click="exportResults(projectID, 'scens')">{{ $t("common.Export results") }}</button>
        </div>
      </div>

      <div class="calib-main" :class="{'calib-main--full': true}">
        <div class="calib-graphs">
          <!--<div class="featured-graphs">-->
          <!--<div :id="'fig0'">-->
          <!--&lt;!&ndash;mpld3 content goes here&ndash;&gt;-->
          <!--</div>-->
          <!--</div>-->
          <div class="other-graphs">
            <div v-for="index in placeholders" :id="'fig'+index" class="calib-graph">
              <!--mpld3 content goes here-->
            </div>
          </div>
        </div>
      </div>

      <br>
      <div v-if="hasTable">
        <help reflink="cost-effectiveness" :label='$t("scenarios.Program cost-effectiveness")'></help>
        <div class="calib-graphs" style="display:inline-block; text-align:right; overflow:auto">
          <table class="table table-bordered table-hover table-striped">
            <thead>
            <tr>
              <th>{{ $t("scenarios.Scenario/program") }}</th>
              <th>{{ $t("Outcomes") }}</th>
              <th v-for="i in table[0].length-3"></th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="rowdata in table">
              <td v-for="i in (rowdata.length-1)">
                <span v-if="rowdata[0]==='header'"             style="font-size:15px; font-weight:bold">{{rowdata[i]}}</span>
                <span v-else-if="rowdata[0]==='keys'  && i==1" style="font-size:12px; font-style:italic">{{rowdata[i]}}</span>
                <span v-else-if="rowdata[0]==='keys'  && i!=1" style="font-size:12px; font-weight:bold">{{rowdata[i]}}</span>
                <span v-else-if="rowdata[0]==='entry' && i==1" style="font-size:12px; font-weight:bold">{{rowdata[i]}}</span>
                <span v-else-if="rowdata[0]==='entry' && i!=1" style="font-size:12px;">                 {{rowdata[i]}}</span>
                <span v-else><div style="min-height:30px"></div></span>
              </td>
            </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
    <!-- END RESULTS CARD -->


    <!-- START ADD-SCENARIO MODAL -->
    <modal name="add-scen"
           height="auto"
           :scrollable="true"
           :width="'90%'"
           :classes="['v--modal', 'vue-dialog', 'grrmodal']"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="false">

        <div class="dialog-content">
          <div class="dialog-c-title" v-if="addEditModal.mode=='add'">
            {{ $t("scenarios.Add scenario") }}
          </div>
          <div class="dialog-c-title" v-else>
            {{ $t("scenarios.Edit scenario") }}
          </div>
          <div class="dialog-c-text">
            <b>{{ $t("scenarios.Scenario name") }}:</b><br>
            <input type="text"
                   class="txbox"
                   v-model="addEditModal.scenSummary.name"/><br>
            <b>{{ $t("scenarios.Databook") }}:</b><br>
            <tr>
              <th><select v-model="addEditModal.scenSummary.model_name" @change="modalSwitchDataset">
                <option v-for='dataset in datasetOptions'>
                  {{ dataset }}
                </option>
              </select><br><br></th>
            </tr>
            <div class="scrolltable" style="max-height: 80vh;">
              <table class="table table-bordered table-striped table-hover">
                <thead>
                <tr>
                  <th colspan=100><div class="dialog-header">
                    <span v-if="addEditModal.modalScenarioType==='coverage'">{{ $t("scenarios.Program coverages") }} (%)</span>
                    <span v-else>{{ $t("scenarios.Program spending") }}</span>
                  </div></th>
                </tr>
                <tr>
                  <th>{{ $t("Name") }}</th>
                  <th>{{ $t("Include") }}?</th>
                  <th v-for="year in defaultScenYears.slice(0, 1)">{{ year - 1 }}</th>
                  <th v-for="year in defaultScenYears">{{ year }}</th>
                </tr>
                </thead>
                <tbody>
                <tr v-for="progvals in this.addEditModal.scenSummary.progvals">
                  <td style="min-width:200px">
                    {{ progvals.name }}
                  </td>
                  <td style="text-align: center">
                    <input type="checkbox" v-model="progvals.included"/>
                  </td>
                  <td style="text-align: right">
                    <span v-if="addEditModal.modalScenarioType==='coverage'">{{ progvals.base_cov }}</span>
                    <span v-else>                                            {{ progvals.base_spend }}</span>
                  </td>
                  <td v-for="(val, index) in progvals.vals">
                    <input type="text"
                           class="txbox"
                           style="text-align: right"
                           v-model="progvals.vals[index]"/>
                  </td>
                </tr>
                </tbody>
              </table>
            </div>
            <button class="btn" @click="modalDeselectAllProgs()" data-tooltip="Deselect all interventions">{{ $t("Deselect all") }}</button>
          </div>
          <div style="text-align:center">
            <button @click="modalSave()" class='btn __green' style="display:inline-block">
              {{ $t("Save") }}
            </button>
            &nbsp;&nbsp;&nbsp;
            <button @click="$modal.hide('add-scen')" class='btn __red' style="display:inline-block">
              <!--<editor-fold desc="Description">-->
              {{ $t("Cancel") }}
              <!--</editor-fold>-->
            </button>
          </div>
        </div>

    </modal>

    <!-- END ADD-SCENARIO MODAL -->

    <!-- ### Start: input uncertainty runs modal ### -->
    <modal name="uncert-nruns"
           height="auto"
           :classes="['v--modal', 'vue-dialog']"
           :width="400"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="false"
    >

      <div class="dialog-content">
        <div class="dialog-c-title">
          {{ $t("uncertainty.Input uncertainty runs") }}
        </div>
        <div class="dialog-c-text">
          {{ $t("uncertainty.Number of runs") }}:<br>
          <input type="text"
                 class="txbox"
                 v-model="modalUncertRuns"/><br>
        </div>
        <div style="text-align:justify">
          <button @click="runScens(modalUncertRuns) | $modal.hide('uncert-nruns')" class='btn __green' style="display:inline-block">
            {{ $t("scenarios.Run scenarios") }}
          </button>

          <button @click="$modal.hide('uncert-nruns')" class='btn __red' style="display:inline-block">
            {{ $t("Cancel") }}
          </button>
        </div>
      </div>

    </modal>
    <!-- ### End: input uncertainty runs modal ### -->
  </div>

</template>


<script>

  import utils from '../js/utils.js'
  import router from '../router.js'
  import i18n from "../i18n";

  export default {
    name: 'ScenariosPage',

    data() {
      return {
        allActive: true,
        scenSummaries: [],
        defaultScenYears: [],
        scenariosLoaded: false,
        datasets: [],
        addEditModal: {
          scenSummary: {},
          origName: '',
          mode: 'add',
          modalScenarioType: 'coverage',
        },
        modalUncertRuns: 10,  // Number of runs in the uncertainty nruns modal dialog
        figscale: 1.0,
        hasGraphs: false,
        calculateCostEff: false,
        hasTable: false,
        table: [],
        withUncert: false,
      }
    },

    computed: {
      projectID()    { return this.$store.getters.activeProjectID },
      hasData()      { return utils.hasData(this) },
      placeholders() { return utils.placeholders() },
      anySelected() { return this.scenSummaries.some(x => x.active) },
    },

    created() {
      if (this.$store.state.currentUser.displayname === undefined) { // If we have no user logged in, automatically redirect to the login page.
        router.push('/login')
      }
      else if ((this.$store.state.activeProject.project !== undefined) &&
        (this.$store.state.activeProject.project.hasData) ) {
        console.log('created() called')
        if (this.$store.state.activeProject === this.$store.state.checkProject) {
          this.getScenSummaries(this.$store.state.scenSummaries)
        }
        else {
          this.getScenSummaries(null)
        }
        this.updateDatasets()
      }
    },

    methods: {

      updateDatasets()                    { return utils.updateDatasets(this) },
      makeGraphs(graphdata)               { return utils.makeGraphs(this, graphdata) },
      exportGraphs(project_id, cache_id)  { return utils.exportGraphs(this, project_id, cache_id) },
      exportResults(project_id, cache_id) { return utils.exportResults(this, project_id, cache_id) },
                                
      scaleFigs(frac) {
        this.figscale = this.figscale*frac;
        if (frac === 1.0) {
          frac = 1.0/this.figscale
          this.figscale = 1.0
        }
        return utils.scaleFigs(frac)
      },

      async getScenSummaries(oldSummaries) {
        this.$sciris.start(this)
        try {
          let response = await this.$sciris.rpc('get_scen_info', [this.projectID])
          response.data.forEach((scen, index) => {
            if ((oldSummaries !== null)  &&  (oldSummaries !== undefined)) {
              if (oldSummaries[index] !== undefined) {
                scen.active = oldSummaries[index].active;
              }
              else {
                scen.active = true;
              }
            }
            else if ((oldSummaries === null) ||  (oldSummaries === undefined)) {
              scen.active = true;
            }
          })
          this.scenSummaries = response.data
          this.scenariosLoaded = true
          this.$store.commit('newScenSummaries', this.scenSummaries)
          this.$sciris.succeed(this)
        } catch (error) {
          this.$sciris.fail(this, 'Could not get scenarios', error);
        }
      },

      setScenSummaries() {
        console.log('setScenSummaries() called')
        this.$sciris.start(this)
        this.$sciris.rpc('set_scen_info', [this.projectID, this.scenSummaries])
          .then( response => {
            this.$sciris.succeed(this, 'Scenarios saved')
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not save scenarios', error)
          })
      },

      setScenYears(scen) {
        this.defaultScenYears = [];
        for (let year = scen.t[0]; year <= scen.t[1]; year++) {
          this.defaultScenYears.push(year)
        }
      },

      addScenModal(scen_type) {
        // Open a model dialog for creating a new scenario
        console.log('addScenModal() called for type ' + scen_type)
        this.$sciris.rpc('get_default_scen', [this.projectID, this.datasets[0],scen_type, i18n.locale])
          .then(response => {
            let defaultScen = response.data
            this.setScenYears(defaultScen)
            this.addEditModal.scenSummary = defaultScen
            this.addEditModal.mode = 'add'
            this.addEditModal.modalScenarioType = scen_type
            this.addEditModal.origName = this.addEditModal.scenSummary.name
            this.addEditModal.scenSummary.model_name = this.datasetOptions[0]
            this.addEditModal.scenSummary.active = true
            this.$modal.show('add-scen')
            console.log('Default scenario:')
            console.log(defaultScen)
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not open add scenario modal', error)
          })
      },

      editScenModal(scenSummary) {
        // Open a model dialog for editing a scenario
        console.log('editScenModal() called')
        this.addEditModal.scenSummary = _.cloneDeep(scenSummary)
        this.addEditModal.modalScenarioType = scenSummary.scen_type
        this.setScenYears(scenSummary)
        console.log('Editing scenario:')
        console.log(this.addEditModal.scenSummary)
        this.addEditModal.origName = this.addEditModal.scenSummary.name
        this.addEditModal.mode = 'edit'
        this.addEditModal.scenSummary.active = true
        this.$modal.show('add-scen')
      },

      async modalSwitchDataset() {
        console.log('modalSwitchDataset() called');
        try {
          let response = await this.$sciris.rpc('scen_switch_dataset', [this.projectID, this.addEditModal.scenSummary]);
          this.addEditModal.scenSummary = response.data;  // overwrite the old optimization
        } catch (error) {
          this.$sciris.fail(this, 'Could not switch databooks', error)
        }
      },

      modalDeselectAllProgs() {
        this.addEditModal.scenSummary.progvals.forEach(progval => {
          progval.included = false;
        })
      },

      modalDeselectAllScens() {
        this.scenSummaries.forEach(scenSummary => scenSummary.active = !this.allActive)
      },

      uncheckSelectAll() {
        this.allActive = false
      },

      modalSave() {
        console.log('modalSave() called')
        this.$sciris.start(this)
        let newScen = _.cloneDeep(this.addEditModal.scenSummary) // Get the new scenario summary from the modal.
        let scenNames = [] // Get the list of all of the current scenario names.
        this.scenSummaries.forEach(scenSum => {
          scenNames.push(scenSum.name)
        })
        if (this.addEditModal.mode === 'edit') { // If we are editing an existing scenario...
          let index = scenNames.indexOf(this.addEditModal.origName) // Get the index of the original (pre-edited) name
          if (index > -1) {
            this.scenSummaries[index].name = newScen.name // hack to make sure Vue table updated
            this.scenSummaries[index].model_name = newScen.model_name
            this.scenSummaries[index] = newScen
            this.scenSummaries[index].active = true
          }
          else {
            console.log('Error: a mismatch in editing keys')
          }
        }
        else { // Else (we are adding a new scenario)...
          newScen.name = utils.getUniqueName(newScen.name, scenNames)
          this.scenSummaries.push(newScen)
        }
        console.log('Saved scenario:')
        console.log(newScen)
        this.$sciris.rpc('set_scen_info', [this.projectID, this.scenSummaries])
          .then( response => {
            this.$sciris.succeed(this, 'Scenario added')
            this.$modal.hide('add-scen')
            this.getScenSummaries(this.scenSummaries)  // Reload all scenarios so Vue state is correct (hack).
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not add scenario', error)
            this.getScenSummaries(this.scenSummaries)
          })
      },

      copyScen(scenSummary) {
        console.log('copyScen() called')
        this.$sciris.start(this)
        var newScen = _.cloneDeep(scenSummary);
        var otherNames = []
        this.scenSummaries.forEach(scenSum => {
          otherNames.push(scenSum.name)
        })
        newScen.name = utils.getUniqueName(newScen.name, otherNames)
        this.scenSummaries.push(newScen)
        this.$sciris.rpc('set_scen_info', [this.projectID, this.scenSummaries])
          .then( response => {
            this.$sciris.succeed(this, 'Scenario copied')
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not copy scenario', error)
          })
      },

      convertScen(scenSummary) {
        console.log('convertScen() called')
        this.$sciris.start(this)
        this.$sciris.rpc('convert_scen', [this.projectID, scenSummary.name])
          .then( response => {
            this.$sciris.succeed(this, 'Scenario converted')
            this.getScenSummaries(this.scenSummaries)
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not convert scenario', error)
          })
      },

      deleteScen(scenSummary) {
        console.log('deleteScen() called')
        this.$sciris.start(this)
        for(var i = 0; i< this.scenSummaries.length; i++) {
          if(this.scenSummaries[i].name === scenSummary.name) {
            this.scenSummaries.splice(i, 1);
          }
        }
        this.$sciris.rpc('set_scen_info', [this.projectID, this.scenSummaries])
          .then( response => {
            this.$sciris.succeed(this, 'Scenario deleted')
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not delete scenario', error)
          })
      },

      async runScens(n_uncert_runs) {
        this.$sciris.start(this)
        try {
          let response = await this.$sciris.rpc('run_scens', [this.projectID, this.scenSummaries.filter(x => x.active).map(x => x.name), this.calculateCostEff, n_uncert_runs]) // Go to the server to get the results
          this.hasTable = this.calculateCostEff
          this.table = response.data.table
          this.makeGraphs(response.data.graphs)
          this.withUncert = n_uncert_runs > 0
          this.$sciris.succeed(this, '') // Success message in graphs function
        } catch (error) {
          this.$sciris.fail(this, 'Could not run scenarios', error)
        }
      },

      UncertScensModal(nruns) {
        console.log('UncertScensModal() called');
        this.modalUncertRuns = nruns
        this.$modal.show('uncert-nruns');
      },

    }
  }
</script>


<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>
