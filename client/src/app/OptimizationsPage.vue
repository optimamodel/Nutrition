<!--
Optimizations page

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
        <help reflink="optimizations" label="Define optimizations"></help>
        <table class="table table-bordered table-hover table-striped" style="width: 100%">
          <thead>
          <tr>
            <th>Name</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="optimSummary in optimSummaries">
            <td>
              <b>{{ optimSummary.name }}</b>
            </td>
            <td>
              {{ statusFormatStr(optimSummary) }}
              {{ timeFormatStr(optimSummary) }}
            </td>
            <td style="white-space: nowrap">
              <button class="btn __green" @click="runOptim(optimSummary, 9999)">Run</button>
              <button class="btn" @click="runOptim(optimSummary, 15)">Test run</button>
              <button class="btn __red" :disabled="!canCancelTask(optimSummary)" @click="clearTask(optimSummary)">Clear run</button>
              <button class="btn" :disabled="!canPlotResults(optimSummary)" @click="plotOptimization(optimSummary)">Plot results</button>
              <button class="btn btn-icon" @click="editOptimModal(optimSummary)"><i class="ti-pencil"></i></button>
              <button class="btn btn-icon" @click="copyOptim(optimSummary)"><i class="ti-files"></i></button>
              <button class="btn btn-icon" @click="deleteOptim(optimSummary)"><i class="ti-trash"></i></button>
            </td>
          </tr>
          </tbody>
        </table>

        <div>
          <button class="btn" :disabled="!optimsLoaded" @click="addOptimModal()">Add optimization</button>
        </div>
      </div>
    </div>


    <!-- START RESULTS CARD -->
    <div class="card full-width-card" v-if="hasGraphs">
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


    <!-- START ADD-OPTIM MODAL :width="900" -->
    <modal name="add-optim"
           height="auto"
           :scrollable="true"
           :classes="['v--modal', 'vue-dialog']"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="clickToClose"
           :transition="transition">

      <div class="dialog-content">
        <div class="dialog-c-title" v-if="addEditModal.mode=='add'">
          Add optimization
        </div>
        <div class="dialog-c-title" v-else>
          Edit optimization
        </div>
        <div class="dialog-c-text" style="display:inline-block">
          <b>Optimization name</b><br>
          <input type="text"
                 class="txbox"
                 v-model="addEditModal.optimSummary.name"/><br>
          <b>Optimization objective weights</b><br>
          <div style="display: inline-block;">
            <table class="table">
              <tbody>
              <tr v-for="item in addEditModal.optimSummary.weightslist">
                <td>
                  {{ item.label }}&nbsp;&nbsp;&nbsp;
                </td>
                <td>
                  <input type="text"
                         class="txbox"
                         v-model="item.weight"/><br>
                </td>
              </tr>
              </tbody>
            </table>
          </div>
          <br>
          <b>Budget multipliers</b> (1 = current budget)<br>
          <input type="text"
                 class="txbox"
                 v-model="addEditModal.optimSummary.mults"/><br>
          <b>Existing spending</b><br>
          <input type="radio" v-model="addEditModal.optimSummary.fix_curr" value=false>&nbsp;Can be reallocated<br>
          <input type="radio" v-model="addEditModal.optimSummary.fix_curr" value=true>&nbsp;Cannot be reallocated<br><br>
          <b>Additional funds to allocate (US$)</b><br>
          <input type="text"
                 class="txbox"
                 v-model="addEditModal.optimSummary.add_funds"/><br>

          <div class="calib-params" style="max-height: 40vh;">
            <table class="table table-bordered table-hover table-striped" style="width: 100%">
              <thead>
              <tr>
                <th>Program name</th>
                <th style="text-align: center">Include?</th>
              </tr>
              </thead>
              <tbody>
              <tr v-for="spec in addEditModal.optimSummary.spec">
                <td>
                  {{ spec.name }}
                </td>
                <td style="text-align: center">
                  <input type="checkbox" v-model="spec.included"/>
                </td>
              </tr>
              </tbody>
            </table>
          </div>

        </div>
        <div style="text-align:center">
          <button @click="addOptim()" class='btn __green' style="display:inline-block">
            Save
          </button>
          &nbsp;&nbsp;&nbsp;
          <button @click="$modal.hide('add-optim')" class='btn __red' style="display:inline-block">
            Cancel
          </button>
        </div>
      </div>

    </modal>
    <!-- END ADD-OPTIM MODAL -->


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
    name: 'OptimizationsPage',

    components: {
      help
    },

    data() {
      return {
        optimSummaries: [],
        optimsLoaded: false,
        addEditModal: {
          optimSummary: {},
          origName: '',
          mode: 'add',
        },
        figscale: 1.0,
        hasGraphs: false,
      }
    },

    computed: {
      projectID()    { return utils.projectID(this) },
      hasData()      { return utils.hasData(this) },
      placeholders() { return utils.placeholders() },
    },

    created() {
      if (this.$store.state.currentUser.displayname === undefined) { // If we have no user logged in, automatically redirect to the login page.
        router.push('/login')
      }
      else if ((this.$store.state.activeProject.project !== undefined) &&
        (this.$store.state.activeProject.project.hasData) ) {
        console.log('created() called')
        utils.sleep(1)  // used so that spinners will come up by callback func
          .then(response => {
            this.getOptimSummaries()
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

      statusFormatStr(optimSummary) {
        if      (optimSummary.status === 'not started') {return ''}
        else if (optimSummary.status === 'queued')      {return 'Initializing... '} // + this.timeFormatStr(optimSummary.pendingTime)
        else if (optimSummary.status === 'started')     {return 'Running for '} // + this.timeFormatStr(optimSummary.executionTime)
        else if (optimSummary.status === 'completed')   {return 'Completed after '} // + this.timeFormatStr(optimSummary.executionTime)
        else                                            {return ''}
      },

      timeFormatStr(optimSummary) {
        let rawValue = ''
        let is_queued = (optimSummary.status === 'queued')
        let is_executing = ((optimSummary.status === 'started') || (optimSummary.status === 'completed'))
        if      (is_queued)    {rawValue = optimSummary.pendingTime}
        else if (is_executing) {rawValue = optimSummary.executionTime}
        else                   {return ''}

        if (rawValue === '--') {
          return '--'
        } else {
          let numSecs = Number(rawValue).toFixed()
          let numHours = Math.floor(numSecs / 3600)
          numSecs -= numHours * 3600
          let numMins = Math.floor(numSecs / 60)
          numSecs -= numMins * 60
          let output = _.padStart(numHours.toString(), 2, '0') + ':' + _.padStart(numMins.toString(), 2, '0') + ':' + _.padStart(numSecs.toString(), 2, '0')
          return output
        }
      },

      canRunTask(optimSummary) {
        console.log('canRunTask() called for with: ' + optimSummary.status)
        return ((optimSummary.status === 'not started') || (optimSummary.status === 'completed'))
      },

      canCancelTask(optimSummary) {
        console.log('canCancelTask() called for with: ' + optimSummary.status)
        return (optimSummary.status !== 'not started')
      },

      canPlotResults(optimSummary) {
        console.log('canPlotResults() called for with: ' + optimSummary.status)
        return (optimSummary.status === 'completed')
      },

      getOptimTaskState(optimSummary) {
        console.log('getOptimTaskState() called for with: ' + optimSummary.status)
        let statusStr = '';

        // Check the status of the task.
        rpcs.rpc('check_task', [optimSummary.server_datastore_id])
          .then(result => {
            statusStr = result.data.task.status;
            optimSummary.status = statusStr;
            optimSummary.pendingTime = result.data.pendingTime;
            optimSummary.executionTime = result.data.executionTime
          })
          .catch(error => {
            optimSummary.status = 'not started';
            optimSummary.pendingTime = '--';
            optimSummary.executionTime = '--'
          })
      },

      pollAllTaskStates() {
        console.log('Do a task poll...');
        this.optimSummaries.forEach(optimSum => { // For each of the optimization summaries...
          if ((optimSum.status !== 'not started') && (optimSum.status !== 'completed')) { // If there is a valid task launched, check it.
            this.getOptimTaskState(optimSum)
          }
        });

        // Hack to get the Vue display of optimSummaries to update
        this.optimSummaries.push(this.optimSummaries[0]);
        this.optimSummaries.pop();

        // Sleep waitingtime seconds. -- WARNING, should make it so this is only called when something changes
        let waitingtime = 1
        utils.sleep(waitingtime * 1000)
          .then(response => {
            // Only if we are still in the optimizations page, call ourselves.
            if (this.$route.path === '/optimizations') {
              this.pollAllTaskStates()
            }
          })
      },

      clearTask(optimSummary) {
        console.log('cancelRun() called for '+this.currentOptim)
        rpcs.rpc('delete_task', [optimSummary.server_datastore_id])
          .then(response => {
            // Get the task state for the optimization.
            this.getOptimTaskState(optimSummary)

            // TODO: Delete cached result.
          })
      },

      getOptimSummaries() {
        console.log('getOptimSummaries() called')
        status.start(this)
        rpcs.rpc('get_optim_info', [this.projectID]) // Get the current project's optimization summaries from the server.
          .then(response => {
            this.optimSummaries = response.data // Set the optimizations to what we received.
            this.optimSummaries.forEach(optimSum => { // For each of the optimization summaries...
              optimSum.server_datastore_id = this.$store.state.activeProject.project.id + ':opt-' + optimSum.name // Build a task and results cache ID from the project's hex UID and the optimization name.
              optimSum.status = 'not started' // Set the status to 'not started' by default, and the pending and execution times to '--'.
              optimSum.pendingTime = '--'
              optimSum.executionTime = '--'
              this.getOptimTaskState(optimSum) // Get the task state for the optimization.
            })
            this.optimsLoaded = true;
            this.pollAllTaskStates() // Start polling of tasks states.
            status.succeed(this, 'Optimizations loaded')
          })
          .catch(error => {
            status.fail(this, 'Could not load optimizations: ' + error.message)
          })
      },

      setOptimSummaries() {
        console.log('setOptimSummaries() called')
        status.start(this)
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
          .then( response => {
            status.succeed(this, 'Optimizations saved')
          })
          .catch(error => {
            status.fail(this, 'Could not save optimizations: ' + error.message)
          })
      },

      addOptimModal() {
        // Open a model dialog for creating a new project
        console.log('addOptimModal() called');
        rpcs.rpc('get_default_optim', [this.projectID])
          .then(response => {
            this.addEditModal.optimSummary = response.data;
            this.addEditModal.origName = this.addEditModal.optimSummary.name;
            this.addEditModal.mode = 'add';
            this.$modal.show('add-optim');
            console.log('New optimization:');
            console.log(this.addEditModal.optimSummary)
          })
          .catch(error => {
            status.failurePopup(this, 'Could not open add optimization modal: '  + error.message)
          })
      },

      editOptimModal(optimSummary) {
        // Open a model dialog for creating a new project
        console.log('editOptimModal() called');
        this.addEditModal.optimSummary = optimSummary;
        console.log('Editing optimization:');
        console.log(this.addEditModal.optimSummary);
        this.addEditModal.origName = this.addEditModal.optimSummary.name;
        this.addEditModal.mode = 'edit';
        this.$modal.show('add-optim');
      },

      addOptim() {
        console.log('addOptim() called');
        this.$modal.hide('add-optim');
        status.start(this)
        let newOptim = _.cloneDeep(this.addEditModal.optimSummary);
        let optimNames = []; // Get the list of all of the current optimization names.
        this.optimSummaries.forEach(optimSum => {
          optimNames.push(optimSum.name)
        });
        if (this.addEditModal.mode === 'edit') { // If we are editing an existing scenario...
          let index = optimNames.indexOf(this.addEditModal.origName); // Get the index of the original (pre-edited) name
          if (index > -1) {
            this.optimSummaries[index].name = newOptim.name; // hack to make sure Vue table updated
            this.optimSummaries[index] = newOptim
          }
          else {
            console.log('Error: a mismatch in editing keys')
          }
        }
        else { // Else (we are adding a new scenario)...
          newOptim.name = utils.getUniqueName(newOptim.name, optimNames);
          this.optimSummaries.push(newOptim)
        }
        console.log('Saved optimization:');
        console.log(newOptim);
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
          .then( response => {
            status.succeed(this, 'Optimization added')
          })
          .catch(error => {
            status.fail(this, 'Could not add optimization: ' + error.message)
          })
      },

      copyOptim(optimSummary) {
        console.log('copyOptim() called')
        status.start(this)
        var newOptim = _.cloneDeep(optimSummary);
        var otherNames = []
        this.optimSummaries.forEach(optimSum => {
          otherNames.push(optimSum.name)
        })
        newOptim.name = utils.getUniqueName(newOptim.name, otherNames)
        this.optimSummaries.push(newOptim)
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
          .then( response => {
            status.succeed(this, 'Optimization copied')
          })
          .catch(error => {
            status.fail(this, 'Could not copy optimization: ' + error.message)
          })
      },

      deleteOptim(optimSummary) {
        console.log('deleteOptim() called')
        status.start(this)
        for(var i = 0; i< this.optimSummaries.length; i++) {
          if(this.optimSummaries[i].name === optimSummary.name) {
            this.optimSummaries.splice(i, 1);
          }
        }
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
          .then( response => {
            status.succeed(this, 'Optimization deleted')
          })
          .catch(error => {
            status.fail(this, 'Could not delete optimization: ' + error.message)
          })
      },

      runOptim(optimSummary, maxtime) {
        console.log('runOptim() called for ' + optimSummary.name + ' for time: ' + maxtime)
        status.start(this)
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries]) // Make sure they're saved first
          .then(response => {
            rpcs.rpc('launch_task', [optimSummary.server_datastore_id, 'run_optim',
              [this.projectID, optimSummary.server_datastore_id, optimSummary.name]])
              .then(response => {
                this.getOptimTaskState(optimSummary) // Get the task state for the optimization.
                status.succeed(this, 'Started optimization')
              })
              .catch(error => {
                status.fail(this, 'Could not start optimization: ' + error.message)
              })
          })
          .catch(error => {
            status.fail(this, 'Could not save optimizations: ' + error.message)
          })
      },

      cancelRun(optimSummary) {
        console.log('cancelRun() called for '+this.currentOptim)
        rpcs.rpc('delete_task', ['run_optim'])
      },

      plotOptimization(optimSummary) {
        console.log('plotOptimization() called')
        status.start(this)
        rpcs.rpc('plot_optimization', [this.projectID, optimSummary.server_datastore_id])
          .then(response => {
            this.makeGraphs(response.data.graphs)
            this.displayResultName = optimSummary.name
            status.succeed(this, 'Graphs created')
          })
          .catch(error => {
            status.fail(this, 'Could not make graphs:' + error.message) // Indicate failure.
          })
      },
    }
  }
</script>


<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
