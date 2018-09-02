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
            <th>Actions</th>
          </tr>
          </thead>
        <tbody>
        <tr v-for="optimSummary in optimSummaries">
          <td>
            <b>{{ optimSummary.name }}</b>
          </td>
          <td style="white-space: nowrap">
            <button class="btn __green" @click="runOptim(optimSummary, 9999)">Run</button>
<button class="btn" @click="runOptim(optimSummary, 20)">Test run</button>
            <button class="btn" @click="editOptim(optimSummary)">Edit</button>
            <button class="btn" @click="copyOptim(optimSummary)">Copy</button>
            <button class="btn" @click="deleteOptim(optimSummary)">Delete</button>
          </td>
        </tr>
        </tbody>
        </table>
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

    <!-- START ADD-OPTIM MODAL -->
      <modal name="add-optim"
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
          Add optimization
        </div>
        <div class="dialog-c-title" v-else>
          Edit optimization
        </div>
        <div class="dialog-c-text">
            <b>Optimization name:</b><br>
            <input type="text"
                   class="txbox"
                   v-model="addEditModal.optimSummary.name"/><br>
            <b>Optimization objectives:</b><br>
            <select v-model="addEditModal.optimSummary.obj">
              <option v-for='obj in objectiveOptions'>
                {{ obj }}
              </option>
            </select><br><br>
            Budget multipliers (1 = current budget):<br>
            <input type="text"
                   class="txbox"
                   v-model="addEditModal.optimSummary.mults"/><br>
            <input type="checkbox" v-model="defaultOptim.fix_curr"/> Existing spending cannot be reallocated<br><br>
            Additional funds (US$):<br>
            <input type="text"
                   class="txbox"
                   v-model="defaultOptim.add_funds"/><br>
          
          <table class="table table-bordered table-hover table-striped" style="width: 100%">
            <thead>
            <tr>
              <th>Program name</th>
              <th style="text-align: center">Include?</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="progvals in addEditModal.optimSummary.progvals">
              <td>
                {{ progvals.name }}
              </td>
              <td style="text-align: center">
                <input type="checkbox" v-model=progvals.included"/>
              </td>
            </tr>
            </tbody>
          </table>
            
        </div>
        <div style="text-align:justify">
          <button @click="addOptim()" class='btn __green' style="display:inline-block">
            Save scenario
          </button>
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
  import taskservice from '@/services/task-service'
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
        defaultScenYears: [],
        optimsLoaded: false,
        addEditModal: {
          optimSummary: {},
          origName: '',
          mode: 'add',
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

      getOptimSummaries() {
        console.log('getOptimSummaries() called')
        status.start(this)
        rpcs.rpc('get_optim_info', [this.projectID]) // Get the current project's optimization summaries from the server.
        .then(response => {
          this.optimSummaries = response.data // Set the optimizations to what we received.
            console.log('Optimization summaries:')
            console.log(this.optimSummaries)
            this.optimsLoaded = true
          status.succeed(this, 'Optimizations loaded')
        })
        .catch(error => {
          status.fail(this, 'Could not get optimizations: ' + error.message)
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

      runOptim(optimSummary) {
        console.log('runOptim() called for '+this.currentOptim)
        status.start(this)
        this.$Progress.start(5000)  // restart just the progress bar, and make it slower 
//        rpcs.rpc('launch_task', ['my_crazy_id', 'async_add', [23, 57]])
//        rpcs.rpc('check_task', ['my_crazy_id'])
//        rpcs.rpc('get_task_result', ['my_crazy_id'])         
//        rpcs.rpc('delete_task', ['my_crazy_id'])
//        rpcs.rpc('delete_task', ['run_optimization'])

          // Do an async_add() and try for at most 15 sec. to get a result, polling every 5 sec.
          // Should succeed.
/*          taskservice.getTaskResultPolling('run_optimization', 15, 3, 'run_optim', [23, 57])
          .then(response => {
            console.log('The result is: ' + response.data.result)          
          }) */
          
        // Make sure they're saved first
        rpcs.rpc('set_optim_info', [this.projectID, this.optimSummaries])
        .then(response => {
          // Go to the server to get the results from the package set.
//          rpcs.rpc('run_optimization', [this.projectID, optimSummary.name])
          taskservice.getTaskResultPolling('run_optimization', 9999, 1, 'run_optim', [this.projectID, optimSummary.name])
          .then(response => {
            this.clearGraphs() // Once we receive a response, we can work with a clean slate
//            this.graphData = response.data.graphs // Pull out the response data (use with the rpcCall).
            this.graphData = response.data.result.graphs // Pull out the response data (use with task).
            let n_plots = this.graphData.length
            console.log('Rendering ' + n_plots + ' graphs')

            for (var index = 0; index <= n_plots; index++) {
              console.log('Rendering plot ' + index)
              var divlabel = 'fig' + index
              var div = document.getElementById(divlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
              while (div.firstChild) {
                div.removeChild(div.firstChild);
              }
              try {
                mpld3.draw_figure(divlabel, response.data.result.graphs[index], (fig, element) => {
                  var formatters = this.defaultFormatter
                  if (index<this.graphFormatters.length) {
                    formatters = this.graphFormatters[index];
                  }
                  fig.setXTicks(formatters.xTicks, formatters.x);
                  fig.setYTicks(formatters.yTicks, formatters.y);
                });
              }
              catch (err) {
                console.log('Graphs failed:' + err.message);
                status.fail(this, 'Error creating graphs: ' + err.message)
              }
            }
            
            // Indicate success.
            status.succeed(this, 'Graphs created')            
          })
          .catch(error => {
            // Pull out the error message.
            this.serverresponse = 'There was an error: ' + error.message

            // Set the server error.
            this.servererror = error.message
            
            // Indicate failure.
            status.fail(this, 'Could not make graphs: ' + error.message)   
          }) 
        })
        .catch(error => {
          // Pull out the error message.
          this.serverresponse = 'There was an error: ' + error.message

          // Set the server error.
          this.servererror = error.message
          
          // Put up a failure notification.
          status.fail(this, 'Could not make graphs: ' + error.message)            
        })     
      },
    }
  }
</script>


<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
