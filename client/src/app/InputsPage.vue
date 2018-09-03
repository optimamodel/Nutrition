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

      <!--Placeholder for {{ this.activeScreen }} input table<br><br>-->

      <table class="table table-bordered table-hover table-striped" style="width: 100%">
        <thead>
        <tr>
          <th colspan="6" style="text-align: left">Percentage of children in each breastfeeding category in baseline year (2017)</th>
        </tr>
        <tr>
          <th>Status</th>
          <th><1 month</th>
          <th>1-5 months</th>
          <th>6-11 months</th>
          <th>12-23 months</th>
          <th>24-59 months</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="tmpr in tmpRows">
          <td v-for="tmpc in tmpCols">
            <input type="text"
                   class="txbox"
                   style="text-align: right"
                   v-model="tmpData[tmpr][tmpc]"/>
            <!--{{ r }}-->
          </td>
        </tr>
        </tbody>
      </table>

      <div>
        <button class="btn __green" @click="saveChanges()">Save changes</button>
        <button class="btn"         @click="download()">Download</button>
        <button class="btn"         @click="upload()">Upload</button>
        <button class="btn __red"   @click="revert()">Revert</button>
      </div>
      <br>

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

  export default {
    name: 'InputsPage',

    components: {
    },

    data() {
      return {
        activeScreen: 'breastfeeding',
        screenData: [],
        tmpData: [['Exclusive', '84.0%', '44.3%', '1.4%', '0.0%', '0.0%'],
          ['Predominant', '9.2%', '21.7%', '3.3%', '0.1%', '0.0%'],
          ['Partial', '5.8%', '31.6%', '93.5%', '72.1%', '0.0%'],
          ['None', '1.0%', '2.4%', '1.9%', '27.8%', '100.0%']],
        tmpRows: [0,1,2,3],
        tmpCols: [0,1,2,3,4,5],
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
