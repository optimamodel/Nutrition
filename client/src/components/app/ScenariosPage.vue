<!--
Define health packages

Last update: 2018-05-29
-->

<template>
  <div class="SitePage">

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
      <button class="btn __blue" @click="addScenario()">Add scenario</button>
      <button class="btn __green" @click="runScenarios()">Run scenarios</button>
      <button class="btn" @click="clearGraphs()">Clear graphs</button>
    </div>
    <br>

    <div style="float:left">
    </div>
    <div>
      <div v-for="index in placeholders" :id="'fig'+index" style="width:650px; float:left;">
        <!--mpld3 content goes here-->
      </div>
    </div>

  </div>
</template>


<script>
  import axios from 'axios'
  var filesaver = require('file-saver')
  import rpcservice from '@/services/rpc-service'
  import router from '@/router'
  import Vue from 'vue';

  export default {
    name: 'ScenariosPage',
    data() {
      return {
        serverresponse: 'no response',
        scenSummaries: [],
      }
    },

    computed: {
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
      }

    },

    methods: {

      dcp(input) {
        var output = JSON.parse(JSON.stringify(input))
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
        var id = this.$store.state.activeProject.project.id // Shorten this
        return id
      },

      getScenSummaries() {
        console.log('getScenSummaries() called')
        // Get the current user's scenaro summaries from the server.
        rpcservice.rpcCall('get_scenario_info', [this.projectID()])
          .then(response => {
            this.scenSummaries = response.data // Set the scenarios to what we received.

            this.$notifications.notify({
              message: 'Scenarios loaded',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },

      setScenSummaries() {
        console.log('setScenSummaries() called')
        rpcservice.rpcCall('set_scenario_info', [this.projectID(), this.scenSummaries])
          .then( response => {
            this.$notifications.notify({
              message: 'Scenarios saved',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },

      copyScen(scenSummary) {
        console.log('copyScen() called')
        var newScen = this.dcp(scenSummary); // You've got to be kidding me, buster
        var otherNames = []
        this.scenSummaries.forEach(scenSum => {
          otherNames.push(scenSum.name)
        })
        newScen.name = this.getUniqueName(newScen.name, otherNames)
        this.scenSummaries.push(newScen)
        rpcservice.rpcCall('set_scenario_info', [this.projectID(), this.scenSummaries])
          .then( response => {
            this.$notifications.notify({
              message: 'Scenario copied',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },
      
      deleteScen(scenSummary) {
        console.log('deleteScen() called')
      },
      
      runScenarios() {
        console.log('runScenarios() called')

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
                    mpld3.draw_figure(divlabel, response.data.graphs[index]); // Draw the figure.
                  }
                  catch (err) {
                    console.log('failled:' + err.message);
                  }
                }
              })
              .catch(error => {
                // Pull out the error message.
                this.serverresponse = 'There was an error: ' + error.message

                // Set the server error.
                this.servererror = error.message
              }).then(response => {
              this.$notifications.notify({
                message: 'Graphs created',
                icon: 'ti-check',
                type: 'success',
                verticalAlign: 'top',
                horizontalAlign: 'center',
              });
            })
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
<style>
</style>
