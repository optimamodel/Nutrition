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
        <div class="card">
          <help reflink="inputs" label="Edit input data"></help>
          <div v-for="name in sheetNames" style="display:inline-block; padding-right:10px">
            <div v-if="name===activeSheet">
              <button class="btn sheetbtn" @click="setActive(name)" data-tooltip="Current sheet">{{ name }}</button>
            </div>
            <div v-else>
              <button class="btn sheetbtn deselected" @click="setActive(name)" data-tooltip="Switch to this sheet">{{ name }}</button>
            </div>

          </div>
          <br><br>

          <div class="icantbelieveitsnotexcel">
            <table class="table table-bordered table-hover table-striped" style="width: 100%;">
              <tr v-for="rowData in sheetTables[activeSheet]" style="height:30px">
                <td v-for="cellDict in rowData" style="border: 1px solid #ccc;">
                  <div v-if="cellDict.format==='head'" class="cell c_head"><div class="cellpad">{{ cellDict.value }}</div></div>
                  <div v-if="cellDict.format==='name'" class="cell c_name"><div class="cellpad">{{ cellDict.value }}</div></div>
                  <div v-if="cellDict.format==='blnk'" class="cell c_blnk"><div class="cellpad"></div></div> <!-- Force empty, even if value -->
                  <div v-if="cellDict.format==='tick'" class="cell c_tick">
                    <div class="cellpad">
                      <input type="checkbox" v-model="cellDict.value"/>
                    </div>
                  </div>
                  <div v-if="cellDict.format==='edit'" class="cell c_edit">
                    <div class="cellpad">
                      <input type="text"
                             class="txbox"
                             style="text-align: right"
                             v-model="cellDict.value"/>
                    </div>
                  </div>
                  <div v-if="cellDict.format==='calc'" class="cell c_calc">
                    <div class="cellpad">
                      <input type="text"
                             class="txbox"
                             style="text-align: right"
                             v-model="cellDict.value" disabled/>
                    </div>
                  </div>
                </td>
              </tr>
            </table>
          </div>

          <div>
            <button class="btn __green" @click="saveSheetData()"    data-tooltip="Save data to project">Save changes</button>
            <button class="btn"         @click="getSheetData()"     data-tooltip="Revert to last saved data">Revert</button>
            <button class="btn"         @click="downloadDatabook()" data-tooltip="Download databook"><i class="ti-download"></i></button>
            <button class="btn"         @click="uploadDatabook()"   data-tooltip="Upload databook"><i class="ti-upload"></i></button>
          </div>
          <br>
        </div>
      </div>
    </div>

  </div>
</template>


<script>

  import axios from 'axios'
  let filesaver = require('file-saver')
  import utils from '@/js/utils' // Imported globally
  import rpcs from '@/js/rpc-service'
  import status from '@/js/status-service'
  import router from '@/router'

  export default {
    name: 'InputsPage',



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
      }
      else if ((this.$store.state.activeProject.project !== undefined) &&
        (this.$store.state.activeProject.project.hasData) ) {
        console.log('created() called')
        utils.sleep(1)  // used so that spinners will come up by callback func
          .then(response => {
            this.getSheetData() // Load the sheet data
          })
      }
    },

    methods: {

      setActive(active) {
        console.log('Setting active to ' + active)
        this.activeSheet = active
      },

      getSheetData() {
        console.log('getSheetData() called')
        status.start(this, 'Getting data...')
        rpcs.rpc('get_sheet_data', [this.projectID]) // Make the server call to download the framework to a .prj file.
          .then(response => {
            this.sheetNames = response.data.names
            this.sheetTables = response.data.tables
            if (this.activeSheet === '') {
              this.activeSheet = this.sheetNames[0]
            }
            status.succeed(this, 'Data loaded')
          })
          .catch(error => {
            status.fail(this, 'Could not get sheet data', error)
          })
      },

      saveSheetData() {
        console.log('saveSheetData() called')
        status.start(this, 'Saving changes...')
        rpcs.rpc('save_sheet_data', [this.projectID, this.sheetTables]) // Make the server call to download the framework to a .prj file.
          .then(response => {
            status.succeed(this, 'Data saved')
          })
          .catch(error => {
            status.fail(this, 'Could not save sheet data', error)
          })
      },

      downloadDatabook() {
        console.log('downloadDatabook() called')
        status.start(this, 'Downloading data book...')
        rpcs.download('download_databook', [this.projectID])
          .then(response => {
            status.succeed(this, '')  // No green popup message.
          })
          .catch(error => {
            status.fail(this, 'Could not download databook', error)
          })
      },

      uploadDatabook() {
        console.log('uploadDatabook() called')
        status.start(this, 'Uploading databook...')
        rpcs.upload('upload_databook', [this.projectID], {}, '.xlsx')
          .then(response => {
            this.getSheetData() // Refresh the table
            status.succeed(this, 'Data uploaded')
          })
          .catch(error => {
            status.fail(this, 'Could not upload data', error)
          })
      },

    }
  }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss" scoped>
  .icantbelieveitsnotexcel {
    display:inline-block;
    max-width: 90vw;
    max-height: 90vh;
    overflow: auto;
  }

  .cell {
    display:inline-flex;
    align-items:center;
    height:100%;
    width:100%;
    justify-content:flex-end;
    text-align:right;
  }

  .cellpad {
    padding:5px
  }

  .c_head {
    background-color: #fafafa;
    font-weight:bold
  }

  .c_name {
    background-color:#fafafa;
  }

  .c_tick {
    background-color: rgb(168, 237, 154);
    justify-content:center;
  }

  .c_edit {
    background-color: rgb(168, 237, 154);
    justify-content:flex-end;
  }

  .c_calc {
    color:#888;
    background-color:#ccc;
    justify-content:flex-end;
  }

  .c_blnk {
    background-color:#fafafa;
  }
</style>
