<!--
Define equity

Last update: 2018-06-26
-->

<template>
  <div class="SitePage">
  
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
          <button class="btn __green" @click="openOptim(optimSummary)">Open</button>        
          <button class="btn" @click="editOptim(optimSummary)">Edit</button>
          <button class="btn" @click="copyOptim(optimSummary)">Copy</button>
          <button class="btn" @click="deleteOptim(optimSummary)">Delete</button>
        </td>
      </tr>
      </tbody>
    </table>

    <div>
      <button class="btn __blue" @click="addOptim()">Add optimization</button>
      <button class="btn __green" @click="runOptim()">Run</button>
      <button class="btn" @click="clearGraphs()">Clear graphs</button>
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
    name: 'OptimizationPage',
    data() {
      return {
        serverresponse: 'no response',
        optimSummaries: [],
        currentOptim: '',
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
        // Load the optimization summaries of the current project.
        this.getOptimSummaries()
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

      getOptimSummaries() {
        console.log('getOptimSummaries() called')
        // Get the current project's optimization summaries from the server.
        rpcservice.rpcCall('get_optim_info', [this.projectID()])
          .then(response => {
            this.optimSummaries = response.data // Set the optimizations to what we received.

            this.$notifications.notify({
              message: 'Optimizations loaded',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },

      setOptimSummaries() {
        console.log('setOptimSummaries() called')
        rpcservice.rpcCall('set_optim_info', [this.projectID(), this.optimSummaries])
          .then( response => {
            this.$notifications.notify({
              message: 'Optimizations saved',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },

      addOptimModal() {
        // Open a model dialog for creating a new project
        console.log('addOptimModal() called');
        rpcservice.rpcCall('get_default_optim', [this.projectID()])
          .then(response => {
            this.defaultOptim = response.data // Set the optimization to what we received.
            this.$modal.show('add-optim');
            console.log(this.defaultOptim)
          });
      },

      addOptim() {
        console.log('addOptim() called')
        this.$modal.hide('add-optim')
        let newOptim = this.dcp(this.defaultOptim); // You've got to be kidding me, buster
        let otherNames = []
        this.optimSummaries.forEach(optimSum => {
          otherNames.push(optimSum.name)
        });
        let index = otherNames.indexOf(newOptim.name);
        if (index > -1) {
          console.log('Optimization named '+newOptim.name+' exists, overwriting...')
          this.optimSummaries[index] = newOptim
        }
        else {
          console.log('Optimization named '+newOptim.name+' does not exist, creating new...')
          this.optimSummaries.push(newOptim)
        }
        console.log(newOptim)
        rpcservice.rpcCall('set_optim_info', [this.projectID(), this.optimSummaries])
          .then( response => {
            this.$notifications.notify({
              message: 'Optimization added',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },

      copyOptim(optimSummary) {
        console.log('copyOptim() called')
        var newOptim = this.dcp(optimSummary); // You've got to be kidding me, buster
        var otherNames = []
        this.optimSummaries.forEach(optimSum => {
          otherNames.push(optimSum.name)
        })
        newOptim.name = this.getUniqueName(newOptim.name, otherNames)
        this.optimSummaries.push(newOptim)
        rpcservice.rpcCall('set_optim_info', [this.projectID(), this.optimSummaries])
          .then( response => {
            this.$notifications.notify({
              message: 'Opimization copied',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },

      deleteOptim(optimSummary) {
        console.log('deleteOptim() called')
        for(var i = 0; i< this.optimSummaries.length; i++) {
          if(this.optimSummaries[i].name === optimSummary.name) {
            this.optimSummaries.splice(i, 1);
          }
        }
        rpcservice.rpcCall('set_optim_info', [this.projectID(), this.optimSummaries])
          .then( response => {
            this.$notifications.notify({
              message: 'Optimization deleted',
              icon: 'ti-check',
              type: 'success',
              verticalAlign: 'top',
              horizontalAlign: 'center',
            });
          })
      },

      runOptim() {
        console.log('runOptim() called')

        // Make sure they're saved first
        rpcservice.rpcCall('set_optim_info', [this.projectID(), this.optimSummaries])
          .then(response => {

            // Go to the server to get the results from the package set.
            rpcservice.rpcCall('run_optims', [this.projectID()])
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
<style scoped>
</style>
