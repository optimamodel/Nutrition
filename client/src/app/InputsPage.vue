<!--
Define health packages

Last update: 2018-08-02
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
      <div v-if="sheetNames">
        <!--<div>-->
          <help reflink="inputs" label="Edit input data"></help>
          <div v-for="name in sheetNames" style="display:inline-block; padding-right:10px">
            <div v-if="name===activeSheet">
              <button class="btn sheetbtn" @click="setActive(name)">{{ name }}</button>
            </div>
            <div v-else>
              <button class="btn sheetbtn deselected" @click="setActive(name)">{{ name }}</button>
            </div>

          </div>
          <br><br>

          <!--Placeholder for {{ this.activeScreen }} input table<br><br>-->

          <!--<div style="flex-grow: 1; max-width: 90vh; overflow-x: scroll;">-->
        <div style="display: inline-block">
            <table class="table table-bordered table-hover table-striped" style="width: 100%">
              <tr v-for="rowData in sheetTables[activeSheet]">
                <td v-for="cellDict in rowData">
                  <div v-if="cellDict.format==='edit'">
                    <input type="text"
                           class="txbox"
                           style="text-align: right"
                           v-model="cellDict.value"/>
                  </div>
                  <div v-else>
                    {{ cellDict.value }}
                  </div>
                </td>
              </tr>
            </table>
          </div>

          <div>
            <button class="btn __green" @click="saveChanges()">Save changes</button>
            <button class="btn"         @click="revert()">Revert</button>
            <button class="btn"         @click="download()"><i class="ti-download"></i></button>
            <button class="btn"         @click="upload()"><i class="ti-upload"></i></button>
          </div>
          <br>
        </div>
      <!--</div>-->
    </div>

  </div>
</template>


<script>
  import axios from 'axios'
  let filesaver = require('file-saver')
  import utils from '@/services/utils'
  import rpcs from '@/services/rpc-service'
  import status from '@/services/status-service'
  import router from '@/router'
  import help from '@/app/HelpLink.vue'


  export default {
    name: 'InputsPage',

    components: {
      help
    },

    data() {
      return {
        sheetNames: [],
        sheetTables: {},
        activeSheet: '',
      }
    },

    computed: {
      projectID()    { return utils.projectID(this) },
      hasData()      { return utils.hasData(this) },
    },

    created() {
      if (this.$store.state.currentUser.displayname === undefined) { // If we have no user logged in, automatically redirect to the login page.
        router.push('/login')
      } else { // Otherwise...
        this.getSheetData() // Load the sheet data
      }

    },

    methods: {

      setActive(active) {
        console.log('Setting active to ' + active)
        this.activeSheet = active
      },

      getSheetData() {
        console.log('getSheetData() called')
        rpcs.rpc('get_sheet_data', [this.projectID]) // Make the server call to download the framework to a .prj file.
          .then(response => {
            this.sheetNames = response.data.names
            this.sheetTables = response.data.tables
            this.activeSheet = this.sheetNames[0]
            status.succeed(this, 'Data loaded')
          })
          .catch(error => {
            // Failure popup.
            status.failurePopup(this, 'Could not get sheet data: ' + error.message)
          })
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
        rpcs.rpcDownloadCall('export_results', [this.projectID]) // Make the server call to download the framework to a .prj file.
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
