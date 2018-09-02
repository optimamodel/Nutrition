<!--
Scenarios page

Last update: 2018-09-02
-->

<template>
  <div>

    <div v-if="projectID ==''">
      <div style="font-style:italic">
        <p>No project is loaded.</p>
      </div>
    </div>

    <div v-else-if="!hasData">
      <div style="font-style:italic">
        <p>Data not yet uploaded for the project.  Please upload a databook in the Projects page.</p>
      </div>
    </div>

    <div v-else>
      <div class="card">
        <help reflink="scenarios" label="Define scenarios"></help>
        <table class="table table-bordered table-hover table-striped" style="width: 100%">
          <thead>
          <tr>
            <th>Name</th>
            <th>Active?</th>
            <th>Actions</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="scenSummary in scenSummaries">
            <td>
              <b>{{ scenSummary.name }}</b>
            </td>
            <td style="text-align: center">
              <input type="checkbox" v-model="scenSummary.active"/>
            </td>
            <td style="white-space: nowrap">
              <button class="btn btn-icon" @click="editScenModal(scenSummary)"><i class="ti-pencil"></i></button>
              <button class="btn btn-icon" @click="copyScen(scenSummary)"><i class="ti-files"></i></button>
              <button class="btn btn-icon" @click="deleteScen(scenSummary)"><i class="ti-trash"></i></button>
            </td>
          </tr>
          </tbody>
        </table>

        <div>
          <button class="btn __green" :disabled="!scenariosLoaded" @click="runScens()">Run scenarios</button>
          <button class="btn __blue" :disabled="!scenariosLoaded" @click="addScenModal('coverage')">Add coverage scenario</button>
          <button class="btn __blue" :disabled="!scenariosLoaded" @click="addScenModal('budget')">Add budget scenario</button>
        </div>
      </div>
    </div>

    <!-- START RESULTS CARD -->
    <div class="card full-width-card">
      <div class="calib-title">
        <help reflink="results-plots" label="Results"></help>
        <div>
            <button class="btn btn-icon" @click="scaleFigs(0.9)" data-tooltip="Zoom out">&ndash;</button>
            <button class="btn btn-icon" @click="scaleFigs(1.0)" data-tooltip="Reset zoom"><i class="ti-zoom-in"></i></button>
            <button class="btn btn-icon" @click="scaleFigs(1.1)" data-tooltip="Zoom in">+</button>
            &nbsp;&nbsp;&nbsp;
          <button class="btn" @click="exportGraphs()">Export plots</button>
          <button class="btn" @click="exportResults(projectID)">Export data</button>
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

    </div>
    <!-- END RESULTS CARD -->


    <!-- START ADD-SCENARIO MODAL -->
    <modal name="add-scen"
           height="auto"
           :scrollable="true"
           :width="900"
           :classes="['v--modal', 'vue-dialog']"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="clickToClose"
           :transition="transition">

      <div class="dialog-content">
        <div class="dialog-c-title" v-if="addEditModal.mode=='add'">
          Add scenario
        </div>
        <div class="dialog-c-title" v-else>
          Edit scenario
        </div>
        <div class="dialog-c-text">
          <b>Scenario name:</b><br>
          <input type="text"
                 class="txbox"
                 v-model="addEditModal.scenSummary.name"/><br>
          <div class="calib-params">
            <table class="table table-bordered table-hover table-striped" style="width: 100%">
              <thead>
              <tr>
                <th colspan=100><div class="dialog-header">
                  <span v-if="addEditModal.modalScenarioType==='coverage'">Program coverages (%)</span>
                  <span v-else>Program spending (US$)</span>
                </div></th>
              </tr>
              <tr>
                <th>Name</th>
                <th>Include?</th>
                <th>Baseline</th>
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
        </div>
        <div style="text-align:center">
          <button @click="addScen()" class='btn __green' style="display:inline-block">
            Save
          </button>
          &nbsp;&nbsp;&nbsp;
          <button @click="$modal.hide('add-scen')" class='btn __red' style="display:inline-block">
            Cancel
          </button>
        </div>
      </div>

    </modal>
    <!-- END ADD-SCENARIO MODAL -->


  </div>
</template>


<script>
  import axios from 'axios'
  var filesaver = require('file-saver')
  import utils from '@/services/utils'
  import rpcs from '@/services/rpc-service'
  import status from '@/services/status-service'
  import router from '@/router'
  import help from '@/app/HelpLink.vue'

  export default {
    name: 'ScenariosPage',

    components: {
      help
    },

    data() {
      return {
        scenSummaries: [],
        defaultScenYears: [],
        scenariosLoaded: false,
        addEditModal: {
          scenSummary: {},
          origName: '',
          mode: 'add',
          modalScenarioType: 'coverage',
        },
        figscale: 1.0,
      }
    },

    computed: {
      projectID()    { return utils.projectID(this) },
      hasData()      { return utils.hasData(this) },
      placeholders() { return utils.placeholders() },
    },

    created() {
      if (this.$store.state.currentUser.displayname == undefined) { // If we have no user logged in, automatically redirect to the login page.
        router.push('/login')
      }
      else if ((this.$store.state.activeProject.project != undefined) &&
        (this.$store.state.activeProject.project.hasData) ) {
        console.log('created() called')
        utils.sleep(1)  // used so that spinners will come up by callback func
          .then(response => {
            this.getScenSummaries()
          })
      }
    },

    methods: {

      clearGraphs()             { return utils.clearGraphs() },
      makeGraphs(graphdata)     { return utils.makeGraphs(this, graphdata) },
      exportGraphs()            { return utils.exportGraphs(this) },
      exportResults(project_id) { return utils.exportResults(this, project_id) },

      scaleFigs(frac) {
        this.figscale = this.figscale*frac;
        if (frac === 1.0) {
          frac = 1.0/this.figscale
          this.figscale = 1.0
        }
        return utils.scaleFigs(frac)
      },

      getScenSummaries() {
        console.log('getScenSummaries() called')
        status.start(this)
        rpcs.rpc('get_scen_info', [this.projectID])
          .then(response => {
            this.scenSummaries = response.data // Set the scenarios to what we received.
            console.log('Scenario summaries:')
            console.log(this.scenSummaries)
            this.scenariosLoaded = true
            status.succeed(this, 'Scenarios loaded')
          })
          .catch(error => {
            status.fail(this, 'Could not get scenarios: ' + error.message)
          })
      },

      setScenSummaries() {
        console.log('setScenSummaries() called')
        status.start(this)
        rpcs.rpc('set_scen_info', [this.projectID, this.scenSummaries])
          .then( response => {
            status.succeed(this, 'Scenarios saved')
          })
          .catch(error => {
            status.fail(this, 'Could not save scenarios: ' + error.message)
          })
      },

      setScenYears(scen) {
        this.defaultScenYears = [];
        for (let year = scen.t[0]; year <= scen.t[1]; year++) {
          this.defaultScenYears.push(year);
        }
      },

      addScenModal(scen_type) {
        // Open a model dialog for creating a new project
        console.log('addScenModal() called for type ' + scen_type);
        rpcs.rpc('get_default_scen', [this.projectID, scen_type])
          .then(response => {
            let defaultScen = response.data;
            this.setScenYears(defaultScen);
            this.addEditModal.scenSummary = defaultScen;
            this.addEditModal.mode = 'add';
            this.addEditModal.modalScenarioType = scen_type;
            this.addEditModal.origName = this.addEditModal.scenSummary.name;
            this.$modal.show('add-scen');
            console.log('Default scenario:');
            console.log(defaultScen)
          })
          .catch(error => {
            status.failurePopup(this, 'Could not open add scenario modal: '  + error.message)
          })
      },

      editScenModal(scenSummary) {
        // Open a model dialog for creating a new project
        console.log('editScenModal() called');
        this.addEditModal.scenSummary = scenSummary;
        this.setScenYears(scenSummary);
        console.log('Editing scenario:');
        console.log(this.addEditModal.scenSummary);
        this.addEditModal.origName = this.addEditModal.scenSummary.name;
        this.addEditModal.mode = 'edit';
        this.$modal.show('add-scen');
      },

      addScen() {
        console.log('addScen() called');
        this.$modal.hide('add-scen');
        status.start(this);
        let newScen = _.cloneDeep(this.addEditModal.scenSummary); // Get the new scenario summary from the modal.
        let scenNames = []; // Get the list of all of the current scenario names.
        this.scenSummaries.forEach(scenSum => {
          scenNames.push(scenSum.name)
        });
        if (this.addEditModal.mode === 'edit') { // If we are editing an existing scenario...
          let index = scenNames.indexOf(this.addEditModal.origName); // Get the index of the original (pre-edited) name
          if (index > -1) {
            this.scenSummaries[index].name = newScen.name; // hack to make sure Vue table updated
            this.scenSummaries[index] = newScen
          }
          else {
            console.log('Error: a mismatch in editing keys')
          }
        }
        else { // Else (we are adding a new scenario)...
          newScen.name = utils.getUniqueName(newScen.name, scenNames);
          this.scenSummaries.push(newScen)
        }
        console.log('Saved scenario:');
        console.log(newScen);
        rpcs.rpc('set_scen_info', [this.projectID, this.scenSummaries])
          .then( response => {
            status.succeed(this, 'Scenario added')
          })
          .catch(error => {
            status.fail(this, 'Could not add scenario: ' + error.message)
          })
      },

      copyScen(scenSummary) {
        console.log('copyScen() called')
        status.start(this)
        var newScen = _.cloneDeep(scenSummary);
        var otherNames = []
        this.scenSummaries.forEach(scenSum => {
          otherNames.push(scenSum.name)
        })
        newScen.name = utils.getUniqueName(newScen.name, otherNames)
        this.scenSummaries.push(newScen)
        rpcs.rpc('set_scen_info', [this.projectID, this.scenSummaries])
          .then( response => {
            status.succeed(this, 'Scenario copied')
          })
          .catch(error => {
            status.fail(this, 'Could not copy scenario: ' + error.message)
          })
      },

      deleteScen(scenSummary) {
        console.log('deleteScen() called')
        status.start(this)
        for(var i = 0; i< this.scenSummaries.length; i++) {
          if(this.scenSummaries[i].name === scenSummary.name) {
            this.scenSummaries.splice(i, 1);
          }
        }
        rpcs.rpc('set_scen_info', [this.projectID, this.scenSummaries])
          .then( response => {
            status.succeed(this, 'Scenario deleted')
          })
          .catch(error => {
            status.fail(this, 'Could not delete scenario: ' + error.message)
          })
      },

      runScens() {
        console.log('runScens() called')
        status.start(this)
        rpcs.rpc('set_scen_info', [this.projectID, this.scenSummaries]) // Make sure they're saved first
          .then(response => {
            rpcs.rpc('run_scens', [this.projectID]) // Go to the server to get the results
              .then(response => {
                this.makeGraphs(response.data.graphs)
                status.succeed(this, '') // Success message in graphs function
              })
              .catch(error => {
                console.log('There was an error: ' + error.message) // Pull out the error message.
                status.fail(this, 'Could not run scenarios: ' + error.message) // Indicate failure.
              })
          })
          .catch(error => {
            this.response = 'There was an error: ' + error.message
            status.fail(this, 'Could not set scenarios: ' + error.message)
          })
      },
    }
  }
</script>


<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
