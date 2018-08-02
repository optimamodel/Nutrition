<!--
Define health packages

Last update: 2018-08-02
-->

<template>
  <div class="SitePage">
  
    <div v-if="activeProjectID ==''">
      <div style="font-style:italic">
        <p>No project is loaded.</p>
      </div>
    </div>
    
    <div v-else>
     
      <table class="table table-bordered table-hover table-striped" style="width: 100%">
        <thead>
        <tr>
          <th>Name</th>
          <th>Type</th>
          <th>Active?</th>
          <th>Actions</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="scenSummary in scenSummaries">
          <td>
            <b>{{ scenSummary.name }}</b>
          </td>
          <td>
            {{ scenSummary.scen_type }}
          </td>
          <td>
            <input type="checkbox" v-model="scenSummary.active"/>
          </td>
          <td style="white-space: nowrap">
            <button class="btn" @click="editScen(scenSummary)">Edit</button>
            <button class="btn" @click="copyScen(scenSummary)">Copy</button>
            <button class="btn" @click="deleteScen(scenSummary)">Delete</button>
          </td>
        </tr>
        </tbody>
      </table>

      <div>
        <button class="btn __green" :disabled="!scenariosLoaded" @click="runScenarios()">Run scenarios</button>
        <button class="btn __blue" :disabled="!scenariosLoaded" @click="addScenarioModal('coverage')">Add coverage scenario</button>
        <button class="btn __blue" :disabled="!scenariosLoaded" @click="addScenarioModal('budget')">Add budget scenario</button>        
        <button class="btn" :disabled="!scenariosLoaded" @click="clearGraphs()">Clear graphs</button>
      </div>
      <br>

      <div style="float:left">
      </div>
      <div>
        <div v-for="index in placeholders" :id="'fig'+index" style="width:650px; float:left;">
          <!--mpld3 content goes here-->
        </div>
      </div>


      <modal name="add-scenario"
             height="auto"
             :scrollable="true"
             :width="900"
             :classes="['v--modal', 'vue-dialog']"
             :pivot-y="0.3"
             :adaptive="true"
             :clickToClose="clickToClose"
             :transition="transition">

        <div class="dialog-content">
          <div class="dialog-c-title">
            Add/edit {{ modalScenarioType }} scenario
          </div>
          <div class="dialog-c-text">
            <b>Scenario name:</b><br>
            <input type="text"
                   class="txbox"
                   v-model="defaultScen.name"/><br>
            <table class="table table-bordered table-hover table-striped" style="width: 100%">
              <thead>
              <tr>
                <th colspan=100><div class="dialog-header">
                  <span v-if="modalScenarioType==='coverage'">Program coverages (%)</span>
                  <span v-else>Program spending (US$)</span>
                </div></th>
              </tr>
              <tr>
                <th>Name</th>
                <th>Include?</th>
                <th v-for="year in defaultScenYears">{{ year }}</th>
              </tr>
              </thead>
              <tbody>
              <tr v-for="prog_spec in defaultScen.spec">
                <td style="min-width:200px">
                  {{ prog_spec.name }}
                </td>
                <td style="text-align: center">
                  <input type="checkbox" v-model="prog_spec.included"/>
                </td>
                <td v-for="(val, index) in prog_spec.vals">
                  <input type="text"
                         class="txbox"
                         style="text-align: right"
                         v-model="prog_spec.vals[index]"/>
                </td>
              </tr>
              </tbody>
            </table>
          </div>
          <div style="text-align:center">
            <button @click="addScenario()" class='btn __green' style="display:inline-block">
              Save scenario
            </button>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            <button @click="$modal.hide('add-scenario')" class='btn __red' style="display:inline-block">
              Cancel
            </button>
          </div>
        </div>

      </modal>
    
      <!-- Popup spinner -->
      <popup-spinner></popup-spinner>
    
    </div>
    
  </div>
</template>


<script>
  import axios from 'axios'
  var filesaver = require('file-saver')
  import rpcservice from '@/services/rpc-service'
  import status from '@/services/status-service'
  import router from '@/router'
  import Vue from 'vue';
  import PopupSpinner from './Spinner.vue'

  export default {
    name: 'ScenariosPage',
    
    components: {
      PopupSpinner
    },
  
    data() {
      return {
        serverresponse: 'no response',
        scenSummaries: [],
        defaultScen: [],
        defaultScenYears: [],
        modalScenarioType: 'coverage', 
        graphData: [],
        scenariosLoaded: false        
      }
    },

    computed: {
      activeProjectID() {
        if (this.$store.state.activeProject.project === undefined) {
          return ''
        } else {
          return this.$store.state.activeProject.project.id
        }
      },
      
      placeholders() {
        var indices = []
        for (var i = 0; i <= 100; i++) {
          indices.push(i);
        }
        return indices;
      },

    },

    created() {
      // If we have no user logged in, automatically redirect to the login page.
      if (this.$store.state.currentUser.displayname == undefined) {
        router.push('/login')
      }
      else { // Otherwise...
        // Load the project summaries of the current user.
        this.getScenSummaries()
        this.getDefaultScen()
      }

    },

    methods: {

      dcp(input) {
        let output = JSON.parse(JSON.stringify(input))
        return output
      },
      
      getUniqueName(fileName, otherNames) {
        let tryName = fileName
        let numAdded = 0        
        while (otherNames.indexOf(tryName) > -1) {
          numAdded = numAdded + 1
          tryName = fileName + ' (' + numAdded + ')'
        }
        return tryName
      },

      projectID() {
        let id = this.$store.state.activeProject.project.id // Shorten this
        return id
      },

      getScenSummaries() {
        console.log('getScenSummaries() called')
        
        // Start indicating progress.
        status.start(this)
      
        // Get the current user's scenario summaries from the server.
        rpcservice.rpcCall('get_scenario_info', [this.projectID()])
        .then(response => {
          this.scenSummaries = response.data // Set the scenarios to what we received.
          
          this.scenariosLoaded = true
          
          // Indicate success.
          status.succeed(this, 'Scenarios loaded')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not load scenarios')
        })        
      },

      getDefaultScen() {
        console.log('getDefaultScen() called')
        // Get the current user's scenario summaries from the server.
        rpcservice.rpcCall('get_default_scenario', [this.projectID()])
        .then(response => {
          this.defaultScen = response.data // Set the scenarios to what we received.
          this.defaultScenYears = []
          for (let year = this.defaultScen.t[0]; year <= this.defaultScen.t[1]; year++) {
            this.defaultScenYears.push(year);
          }
        })
        .catch(error => {
          // Failure popup.
          status.failurePopup(this, 'Could not get default scenario')
        })        
      },

      setScenSummaries() {
        console.log('setScenSummaries() called')
        
        // Start indicating progress.
        status.start(this)
          
        rpcservice.rpcCall('set_scenario_info', [this.projectID(), this.scenSummaries])
        .then(response => {
          // Indicate success.
          status.succeed(this, 'Scenarios saved')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not save scenario') 
        })         
      },

      addScenarioModal(scenarioType) {
        // Open a model dialog for creating a new project
        console.log('addScenarioModal() called');
        rpcservice.rpcCall('get_default_scenario', [this.projectID()])
        .then(response => {
          this.defaultScen = response.data // Set the scenarios to what we received.
          this.defaultScen.scen_type = scenarioType
          this.modalScenarioType = scenarioType
          this.$modal.show('add-scenario');
          console.log(this.defaultScen)
        })
        .catch(error => {
           // Failure popup.
          status.failurePopup(this, 'Could not open default scenario')
        })        
      },

      addScenario() {
        console.log('addScenario() called')
        this.$modal.hide('add-scenario')
        
        // Start indicating progress.
        status.start(this)
          
        let newScen = this.dcp(this.defaultScen); // You've got to be kidding me, buster
        let otherNames = []
        this.scenSummaries.forEach(scenSum => {
          otherNames.push(scenSum.name)
        });
        let index = otherNames.indexOf(newScen.name);
        if (index > -1) {
          console.log('Scenario named '+newScen.name+' exists, overwriting...')
          this.scenSummaries[index] = newScen
        }
        else {
          console.log('Scenario named '+newScen.name+' does not exist, creating new...')
          this.scenSummaries.push(newScen)
        }
        console.log(newScen)
        rpcservice.rpcCall('set_scenario_info', [this.projectID(), this.scenSummaries])
        .then(response => {
          // Indicate success.
          status.succeed(this, 'Scenario added')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not add scenario') 
          
          // TODO: Should probably fix the corrupted this.scenSummaries.
        })       
      },

      editScen(scenSummary) {
        // Open a model dialog for creating a new project
        console.log('editScen() called');
        this.defaultScen = scenSummary
        this.modalScenarioType = scenSummary.scen_type
        this.$modal.show('add-scenario');
      },

      copyScen(scenSummary) {
        console.log('copyScen() called')
        
        // Start indicating progress.
        status.start(this)
        
        var newScen = this.dcp(scenSummary); // You've got to be kidding me, buster
        var otherNames = []
        this.scenSummaries.forEach(scenSum => {
          otherNames.push(scenSum.name)
        })
        newScen.name = this.getUniqueName(newScen.name, otherNames)
        this.scenSummaries.push(newScen)
        rpcservice.rpcCall('set_scenario_info', [this.projectID(), this.scenSummaries])
        .then( response => {
          // Indicate success.
          status.succeed(this, 'Scenario copied')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not copy scenario') 
          
          // TODO: Should probably fix the corrupted this.scenSummaries.
        })      
      },

      deleteScen(scenSummary) {
        console.log('deleteScen() called')
        
        // Start indicating progress.
        status.start(this)
        
        for(var i = 0; i< this.scenSummaries.length; i++) {
          if(this.scenSummaries[i].name === scenSummary.name) {
            this.scenSummaries.splice(i, 1);
          }
        }
        rpcservice.rpcCall('set_scenario_info', [this.projectID(), this.scenSummaries])
        .then( response => {
          // Indicate success.
          status.succeed(this, 'Scenario deleted')
        })
        .catch(error => {
          // Indicate failure.
          status.fail(this, 'Could not delete scenario') 
          
          // TODO: Should probably fix the corrupted this.scenSummaries.
        })        
      },
      
      runScenarios() {
        console.log('runScenarios() called')
        status.start(this)        
        // Make sure they're saved first
        rpcservice.rpcCall('set_scenario_info', [this.projectID(), this.scenSummaries])
        .then(response => {
          // Go to the server to get the results from the package set.
          rpcservice.rpcCall('run_scenarios', [this.projectID()])
          .then(response => {
            this.clearGraphs() // Once we receive a response, we can work with a clean slate
            this.serverresponse = response.data // Pull out the response data.
            var n_plots = response.data.graphs.length
            console.log('Rendering ' + n_plots + ' graphs')

            for (var index = 0; index <= n_plots; index++) {
              console.log('Rendering plot ' + index)
              var divlabel = 'fig' + index
              var div = document.getElementById(divlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
              while (div.firstChild) {
                div.removeChild(div.firstChild);
              }
              try {
                mpld3.draw_figure(divlabel, response.data.graphs[index], function(fig, element) {
                  fig.setXTicks(6, function(d) { return d3.format('.0f')(d); });
                  fig.setYTicks(null, function(d) { return d3.format('.2s')(d); });
                })     
              }
              catch (err) {
                console.log('failled:' + err.message);
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
            status.fail(this, 'Could not make graphs')           
          })
        })
        .catch(error => {
          // Pull out the error message.
          this.serverresponse = 'There was an error: ' + error.message

          // Set the server error.
          this.servererror = error.message
          
          // Put up a failure notification.
          status.fail(this, 'Could not make graphs')      
        })         
      },

      clearGraphs() {
        for (var index = 0; index <= 100; index++) {
          console.log('Clearing plot ' + index)
          var divlabel = 'fig' + index
          var div = document.getElementById(divlabel); // CK: Not sure if this is necessary? To ensure the div is clear first
          while (div.firstChild) {
            div.removeChild(div.firstChild);
          }
        }
      }
    }
  }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss" scoped>
</style>
