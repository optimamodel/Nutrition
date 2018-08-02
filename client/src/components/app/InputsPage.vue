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
      <button class="btn" @click="setActive('breastfeeding')">Breastfeeding distribution</button>
      <button class="btn" @click="setActive('nutritional')">Nutritional status distribution</button>
      <button class="btn" @click="setActive('IYCF')">IYCF packages</button>
      <button class="btn" @click="setActive('sam')">Treatment of SAM</button>
      <button class="btn" @click="setActive('programs')">Program cost and coverage</button>
      <br><br>

      Placeholder for {{ this.activeScreen }} input table<br><br>

      <!--<table class="table table-bordered table-hover table-striped" style="width: 100%">-->
        <!--<thead>-->
        <!--<tr>-->
          <!--<th>Name</th>-->
          <!--<th>Type</th>-->
          <!--<th>Active?</th>-->
          <!--<th>Actions</th>-->
        <!--</tr>-->
        <!--</thead>-->
        <!--<tbody>-->
        <!--<tr v-for="scenSummary in scenSummaries">-->
          <!--<td>-->
            <!--<b>{{ scenSummary.name }}</b>-->
          <!--</td>-->
          <!--<td>-->
            <!--{{ scenSummary.scen_type }}-->
          <!--</td>-->
          <!--<td>-->
            <!--<input type="checkbox" v-model="scenSummary.active"/>-->
          <!--</td>-->
          <!--<td style="white-space: nowrap">-->
            <!--<button class="btn" @click="editScen(scenSummary)">Edit</button>-->
            <!--<button class="btn" @click="copyScen(scenSummary)">Copy</button>-->
            <!--<button class="btn" @click="deleteScen(scenSummary)">Delete</button>-->
          <!--</td>-->
        <!--</tr>-->
        <!--</tbody>-->
      <!--</table>-->

      <div>
        <button class="btn __green" @click="saveChanges()">Save changes</button>
        <button class="btn"         @click="download()">Download</button>
        <button class="btn"         @click="upload()">Upload</button>
        <button class="btn __red"   @click="revert()">Revert</button>
      </div>
      <br>


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
    name: 'InputsPage',

    components: {
      PopupSpinner
    },

    data() {
      return {
        activeScreen: 'breastfeeding',
        screenData: [],
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
    },

    created() {
      // If we have no user logged in, automatically redirect to the login page.
      if (this.$store.state.currentUser.displayname == undefined) {
        router.push('/login')
      }
      else { // Otherwise...
        // Load the project summaries of the current user.
        this.getSheetData()
      }

    },

    methods: {

      setActive(active) {
        console.log('Setting active to ' + active)
        this.activeScreen = active
      },

      getSheetData() {
        console.log('getSheetData() called')
      },

      projectID() {
        let id = this.$store.state.activeProject.project.id // Shorten this
        return id
      },

      saveChanges() {
        status.failurePopup(this, 'Not implemented')
      },

      upload() {
        status.failurePopup(this, 'Not implemented')
      },

      download() {
        status.failurePopup(this, 'Not implemented')
      },

      revert() {
        status.failurePopup(this, 'Not implemented')
      },

      exportResults() {
        console.log('exportResults() called')
        rpcservice.rpcDownloadCall('export_results', [this.projectID()]) // Make the server call to download the framework to a .prj file.
          .catch(error => {
            // Failure popup.
            status.failurePopup(this, 'Could not export results: ' + error.message)
          })
      },
    }
  }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss" scoped>
</style>
