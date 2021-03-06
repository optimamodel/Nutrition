<!--
Define health packages

Last update: 2019-02-11
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
          <br>
          <br>
          <div class="controls-box">
            <b>Databook: &nbsp;</b>
            <select v-model="activeDataset" @change="getSheetData()">
              <option v-for='dataset in datasetOptions'>
                {{ dataset }}
              </option>
            </select>&nbsp;
            <button class="btn btn-icon" @click="renameDatasetModal()" data-tooltip="Rename"><i class="ti-pencil"></i></button>
            <button class="btn btn-icon" @click="copyDataset()" data-tooltip="Copy"><i class="ti-files"></i></button>
            <button class="btn btn-icon" @click="deleteDataset()" data-tooltip="Delete"><i class="ti-trash"></i></button>
            <button class="btn btn-icon" @click="downloadDatabook()" data-tooltip="Download"><i class="ti-download"></i></button>
            <button class="btn btn-icon" @click="uploadDatabook()" data-tooltip="Upload"><i class="ti-upload"></i></button>
<!--            <button class="btn btn-icon" @click="loadDatasets()" data-tooltip="Refresh"><i class="ti-reload"></i></button> --> &nbsp;
            <!--<help reflink="parameter-sets"></help>-->
          </div>
          <br>
          <br>
          <div v-for="name in sheetNames" style="display:inline-block; padding-right:10px">
            <div v-if="name===activeSheet">
              <button class="btn sheetbtn" @click="setActive(name)" data-tooltip="Current sheet">{{ name }}</button>
            </div>
            <div v-else>
              <button class="btn sheetbtn deselected" @click="setActive(name)" data-tooltip="Switch to this sheet">{{ name }}</button>
            </div>

          </div>

          <br><br>

          <div>
            <button class="btn __green" @click="saveSheetData()"    data-tooltip="Save data to project">Save changes</button>
            <button class="btn __red"         @click="getSheetData()"     data-tooltip="Revert to last saved data">Revert</button>
          </div>

          <br>

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
                  <div v-if="cellDict.format==='bdgt'" class="cell c_edit">
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
                             v-model="cellDict.value" :disabled="true"/>
                    </div>
                  </div>
                  <div v-if="cellDict.format==='drop'" class="cell c_drop">
                    <div class="cellpad">
                      <select v-model="cellDict.value">
                        <option v-for='costFunc in costFuncOptions'>{{ costFunc }}</option>
                      </select>
                    </div>
                  </div>
                </td>
              </tr>
            </table>
          </div>

          <br>
        </div>
      </div>
    </div>

    <!-- ### Start: rename dataset modal ### -->
    <modal name="rename-dataset"
           height="auto"
           :classes="['v--modal', 'vue-dialog']"
           :width="width"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="clickToClose"
           :transition="transition">

      <div class="dialog-content">
        <div class="dialog-c-title">
          Rename databook
        </div>
        <div class="dialog-c-text">
          New name:<br>
          <input type="text"
                 class="txbox"
                 v-model="activeDataset"/><br>
        </div>
        <div style="text-align:justify">
          <button @click="renameDataset()" class='btn __green' style="display:inline-block">
            Rename
          </button>

          <button @click="$modal.hide('rename-dataset')" class='btn __red' style="display:inline-block">
            Cancel
          </button>
        </div>
      </div>

    </modal>
    <!-- ### End: rename dataset modal ### -->

  </div>
</template>


<script>

  import utils from '../js/utils.js' // Imported globally
  import router from '../router.js'

  export default {
    name: 'InputsPage',



    data() {
      return {
        activeDataset: '',
        datasetOptions: [],
        sheetNames: [],
        sheetTables: {},
        activeSheet: '',
        costFuncOptions: ['Linear (constant marginal cost) [default]',
                          'Curved with increasing marginal cost',
                          'Curved with decreasing marginal cost',
                          'S-shaped (decreasing then increasing marginal cost)']
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
        this.updateDatasets()
          .then(response => {
            this.getSheetData() // Load the sheet data
          })
      }
    },

    methods: {

      updateDatasets() { return utils.updateDatasets(this) },

      setActive(active) {
        console.log('Setting active to ' + active)
        this.activeSheet = active
      },

      getSheetData() {
        console.log('getSheetData() called')
        this.$sciris.start(this, 'Getting data...')
        this.$sciris.rpc('get_sheet_data', [this.projectID], {'key': this.activeDataset}) // Make the server call to download the framework to a .prj file.
          .then(response => {
            this.sheetNames = response.data.names
            this.sheetTables = response.data.tables
            if (this.activeSheet === '') {
              this.activeSheet = this.sheetNames[0]
            }
            this.$sciris.succeed(this, 'Data loaded')
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not get sheet data', error)
          })
      },

      saveSheetData() {
        console.log('saveSheetData() called')
        this.$sciris.start(this, 'Saving changes...')
        this.$sciris.rpc('save_sheet_data', [this.projectID, this.sheetTables], {'key': this.activeDataset}) // Make the server call to download the framework to a .prj file.
          .then(response => {
            // Call getSheetData() because the save_sheet_data() RPC will trigger new
            // values for the calculated cells.
            this.getSheetData() // Load the sheet data.
            this.$sciris.succeed(this, 'Data saved')
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not save sheet data', error)
          })
      },

      downloadDatabook() {
        console.log('downloadDatabook() called')
        this.$sciris.start(this, 'Downloading databook...')
        this.$sciris.download('download_databook', [this.projectID], {'key': this.activeDataset})
          .then(response => {
            this.$sciris.succeed(this, '')  // No green popup message.
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not download databook', error)
          })
      },

      uploadDatabook() {
        console.log('uploadDatabook() called')
        this.$sciris.upload('upload_databook', [this.projectID], {}, '.xlsx')
          .then(response => {
            this.$sciris.start(this, 'Uploading databook...')
            this.updateDatasets() // Update the dataset list so the new dataset shows up on the list.
              .then(response2 => {
                this.getSheetData() // Load the sheet data.
                  this.$sciris.succeed(this, 'Data uploaded')
                })
		  })
          .catch(error => {
            this.$sciris.fail(this, 'Could not upload data', error)
          })
      },

      renameDatasetModal() {
        console.log('renameDatasetModal() called');
        this.origDatasetName = this.activeDataset // Store this before it gets overwritten
        this.$modal.show('rename-dataset');
      },

      renameDataset() {
        console.log('renameDataset() called for ' + this.activeDataset)
        this.$modal.hide('rename-dataset');
        this.$sciris.start(this)
        this.$sciris.rpc('rename_dataset', [this.projectID, this.origDatasetName, this.activeDataset]) // Have the server rename the dataset, giving it a new name.
          .then(response => {
            this.updateDatasets() // Update the dataset so the renamed set shows up on the list.
            this.$sciris.succeed(this, 'Databook "'+this.activeDataset+'" renamed') // Indicate success.
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not rename databook', error)
          })
      },

      copyDataset() {
        console.log('copyDataset() called for ' + this.activeDataset)
        this.$sciris.start(this)
        this.$sciris.rpc('copy_dataset', [this.projectID, this.activeDataset]) // Have the server copy the dataset, giving it a new name.
          .then(response => {
            this.updateDatasets() // Update the datasets so the copied program shows up on the list.
            this.activeDataset = response.data
            this.$sciris.succeed(this, 'Databook "'+this.activeDataset+'" copied') // Indicate success.
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not copy databook', error)
          })
      },

      deleteDataset() {
        console.log('deleteDataset() called for ' + this.activeDataset)
        this.$sciris.start(this)
        this.$sciris.rpc('delete_dataset', [this.projectID, this.activeDataset]) // Have the server delete the dataset.
          .then(response => {
            this.updateDatasets() // Update the project summaries so the dataset deletion shows up on the list.
              .then(response2 => {
                this.getSheetData() // Load the sheet data (since we've switched to a new one).
				this.$sciris.succeed(this, 'Databook "'+this.activeDataset+'" deleted') // Indicate success.
              })        
          })
          .catch(error => {
            this.$sciris.fail(this, 'Cannot delete last databook: ensure there are at least 2 databooks before deleting one', error)
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

  .c_drop {
    background-color: rgb(168, 237, 154);
    justify-content:flex-end;
  }

  .c_blnk {
    background-color:#fafafa;
  }
</style>
