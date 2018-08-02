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

      <!--<div style="float:left">-->
      <!--</div>-->
      <!--<div>-->
        <!--<div v-for="index in placeholders" :id="'fig'+index" style="width:650px; float:left;">-->
          <!--&lt;!&ndash;mpld3 content goes here&ndash;&gt;-->
        <!--</div>-->
      <!--</div>-->


      <!--<modal name="add-scenario"-->
             <!--height="auto"-->
             <!--:scrollable="true"-->
             <!--:width="900"-->
             <!--:classes="['v&#45;&#45;modal', 'vue-dialog']"-->
             <!--:pivot-y="0.3"-->
             <!--:adaptive="true"-->
             <!--:clickToClose="clickToClose"-->
             <!--:transition="transition">-->

        <!--<div class="dialog-content">-->
          <!--<div class="dialog-c-title">-->
            <!--Add/edit {{ modalScenarioType }} scenario-->
          <!--</div>-->
          <!--<div class="dialog-c-text">-->
            <!--<b>Scenario name:</b><br>-->
            <!--<input type="text"-->
                   <!--class="txbox"-->
                   <!--v-model="defaultScen.name"/><br>-->
            <!--<table class="table table-bordered table-hover table-striped" style="width: 100%">-->
              <!--<thead>-->
              <!--<tr>-->
                <!--<th colspan=100><div class="dialog-header">-->
                  <!--<span v-if="modalScenarioType==='coverage'">Program coverages (%)</span>-->
                  <!--<span v-else>Program spending (US$)</span>-->
                <!--</div></th>-->
              <!--</tr>-->
              <!--<tr>-->
                <!--<th>Name</th>-->
                <!--<th>Include?</th>-->
                <!--<th>Baseline</th>-->
                <!--<th v-for="year in defaultScenYears">{{ year }}</th>-->
              <!--</tr>-->
              <!--</thead>-->
              <!--<tbody>-->
              <!--<tr v-for="prog_spec in defaultScen.spec">-->
                <!--<td style="min-width:200px">-->
                  <!--{{ prog_spec.name }}-->
                <!--</td>-->
                <!--<td style="text-align: center">-->
                  <!--<input type="checkbox" v-model="prog_spec.included"/>-->
                <!--</td>-->
                <!--<td style="text-align: right">-->
                  <!--<span v-if="modalScenarioType==='coverage'">{{ prog_spec.base_cov }}</span>-->
                  <!--<span v-else>{{ prog_spec.base_spend }}</span>-->
                <!--</td>-->
                <!--<td v-for="(val, index) in prog_spec.vals">-->
                  <!--<input type="text"-->
                         <!--class="txbox"-->
                         <!--style="text-align: right"-->
                         <!--v-model="prog_spec.vals[index]"/>-->
                <!--</td>-->
              <!--</tr>-->
              <!--</tbody>-->
            <!--</table>-->
          <!--</div>-->
          <!--<div style="text-align:center">-->
            <!--<button @click="addScenario()" class='btn __green' style="display:inline-block">-->
              <!--Save scenario-->
            <!--</button>-->
            <!--&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-->
            <!--<button @click="$modal.hide('add-scenario')" class='btn __red' style="display:inline-block">-->
              <!--Cancel-->
            <!--</button>-->
          <!--</div>-->
        <!--</div>-->

      <!--</modal>-->

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
