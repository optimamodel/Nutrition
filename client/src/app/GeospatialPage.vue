<!--
Geospatial page

Last update: 2019jan10
-->

<template>
  <div>

    <div v-if="projectID ==''">
      <div style="font-style:italic">
        <p>{{ $t("common.no_project_loaded") }}.</p>
      </div>
    </div>

    <div v-else-if="!hasData">
      <div style="font-style:italic">
        <p>{{ $t("common.no_data_loaded") }}</p>
      </div>
    </div>

    <div v-else>
      <div class="card">
        <help reflink="geospatial" :label='$t("geospatial.Define geospatial optimizations")'></help>
        <table class="table table-bordered table-hover table-striped" style="width: 100%">
          <thead>
          <tr>
            <th>{{ $t("Name") }}</th>
            <th>{{ $t("Status") }}</th>
            <th>{{ $t("Actions") }}</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="geoSummary in geoSummaries">
            <td>
              <b>{{ geoSummary.name }}</b>
            </td>
            <td>
              {{ statusFormatStr(geoSummary) }}
              {{ timeFormatStr(geoSummary) }}
            </td>
            <td style="white-space: nowrap">
              <button class="btn __green" :disabled="!canRunTask(geoSummary)"     @click="runGeo(geoSummary, 'full')">{{ $t("common.Run") }}</button>
              <button class="btn" :disabled="!canRunTask(geoSummary)"             @click="runGeo(geoSummary, 'test')">{{ $t("common.Test run") }}</button>
              <button class="btn __green" :disabled="!canPlotResults(geoSummary)" @click="plotGeospatial(geoSummary)">{{ $t("common.Plot results") }}</button>
              <button class="btn" :disabled="!canCancelTask(geoSummary)"          @click="clearTask(geoSummary)">{{ $t("common.Clear run") }}</button>
              <button class="btn btn-icon" @click="editGeoModal(geoSummary)" :data-tooltip='$t("geospatial.Edit geospatial optimization")'><i class="ti-pencil"></i></button>
              <button class="btn btn-icon" @click="copyGeo(geoSummary)" :data-tooltip='$t("geospatial.Copy geospatial optimization")'><i class="ti-files"></i></button>
              <button class="btn btn-icon" @click="deleteGeo(geoSummary)" :data-tooltip='$t("geospatial.Delete geospatial optimization")'><i class="ti-trash"></i></button>
            </td>
          </tr>
          </tbody>
        </table>

        <div>
          <button class="btn" :disabled="!geosLoaded" @click="addGeoModal()">{{ $t("geospatial.Add geospatial optimization") }}</button>
        </div>
      </div>
    </div>


    <!-- START RESULTS CARD -->
    <div class="card full-width-card" v-if="hasGraphs">
      <div class="calib-title">
        <help reflink="results-plots" label="Results"></help>
        <div>
          <button class="btn btn-icon" @click="scaleFigs(0.9)" :data-tooltip='$t("common.Zoom out")'>&ndash;</button>
          <button class="btn btn-icon" @click="scaleFigs(1.0)" :data-tooltip='$t("common.Reset zoom")'><i class="ti-zoom-in"></i></button>
          <button class="btn btn-icon" @click="scaleFigs(1.1)" :data-tooltip='$t("common.Zoom in")'>+</button>
          &nbsp;&nbsp;&nbsp;
          <button class="btn" @click="exportGraphs(projectID, displayResultDatastoreId)">{{ $t("common.Export plots") }}</button>
          <button class="btn" @click="exportResults(projectID, displayResultDatastoreId)">{{ $t("common.Export data") }}</button>
        </div>
      </div>

      <div class="calib-main" :class="{'calib-main--full': true}">
        <div class="calib-graphs">
          <div class="other-graphs">
            <div v-for="index in placeholders" :id="'fig'+index" class="calib-graph">
              <!--mpld3 content goes here-->
            </div>
          </div>
        </div>
      </div>

      <br>
      <div v-if="table">
        <help reflink="cost-effectiveness" label="Program cost-effectiveness"></help>
        <div class="calib-graphs" style="display:inline-block; text-align:right; overflow:auto">
          <table class="table table-bordered table-hover table-striped">
            <thead>
            <tr>
              <th>{{ $t("geospatial.Optimization/program") }}</th>
              <th>{{ $t("Outcomes") }}</th>
              <th v-for="i in table[0].length-3"></th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="rowdata in table">
              <td v-for="i in (rowdata.length-1)">
                <span v-if="rowdata[0]==='header'"             style="font-size:15px; font-weight:bold">{{rowdata[i]}}</span>
                <span v-else-if="rowdata[0]==='keys'  && i==1" style="font-size:12px; font-style:italic">{{rowdata[i]}}</span>
                <span v-else-if="rowdata[0]==='keys'  && i!=1" style="font-size:12px; font-weight:bold">{{rowdata[i]}}</span>
                <span v-else-if="rowdata[0]==='entry' && i==1" style="font-size:12px; font-weight:bold">{{rowdata[i]}}</span>
                <span v-else-if="rowdata[0]==='entry' && i!=1" style="font-size:12px;">                 {{rowdata[i]}}</span>
                <span v-else><div style="min-height:30px"></div></span>
              </td>
            </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
    <!-- END RESULTS CARD -->


    <!-- START ADD-GEO MODAL :width="900" -->
    <modal name="add-geo"
           height="auto"
           :scrollable="true"
           :classes="['v--modal', 'vue-dialog']"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="clickToClose"
           :transition="transition">

      <div class="dialog-content">
        <div class="dialog-c-title" v-if="addEditModal.mode=='add'">
          {{ $t("geospatial.Add geospatial optimization") }}
        </div>
        <div class="dialog-c-title" v-else>
          {{ $t("geospatial.Edit geospatial optimization") }}
        </div>
        <div class="dialog-c-text" style="display:inline-block">
          <b>{{ $t("geospatial.Geospatial optimization name") }}</b><br>
          <input type="text"
                 class="txbox"
                 v-model="addEditModal.geoSummary.name"/><br>
          <b>{{ $t("geospatial.Select regions") }}</b><br>
          <div v-for="selection in addEditModal.geoSummary.dataset_selections">
            <input type="checkbox" :value="selection.active" v-model="selection.active">
            {{selection.name}}</input>
          </div><br>
          <div class="scrolltable" style="max-height: 30vh;">
            <table class="table table-bordered table-striped table-hover">
              <thead>
              <tr>
                <th>{{ $t("geospatial.Optimization objective") }}</th>
                <th>{{ $t("geospatial.Weight") }}</th>
              </tr>
              </thead>
              <tbody>
              <tr v-for="item in addEditModal.geoSummary.weightslist">
                <td>
                  {{ item.label }}&nbsp;&nbsp;&nbsp;
                </td>
                <td>
                  <input type="text"
                         class="txbox"
                         v-model="item.weight"/><br>
                </td>
              </tr>
              </tbody>
            </table>
          </div>

          <br>
          <b>{{ $t("geospatial.Existing spending") }}</b><br>
          <input type="radio" v-model="addEditModal.geoSummary.fix_curr" :value="false">&nbsp;{{ $t("common.Can be reallocated") }}<br>
          <input type="radio" v-model="addEditModal.geoSummary.fix_curr" :value="true">&nbsp;{{ $t("common.Cannot be reallocated") }}<br><br>
          <b>{{ $t("geoaptial.Regional spending") }}</b><br>
          <input type="radio" v-model="addEditModal.geoSummary.fix_regionalspend" :value="false">&nbsp;{{ $t("geospatial.Can be reallocated between regions") }}<br>
          <input type="radio" v-model="addEditModal.geoSummary.fix_regionalspend" :value="true">&nbsp;{{ $t("geospatial.Cannot be reallocated between regions") }}<br><br>
          <b>{{ $t("geospatial.Additional funds to allocate") }}</b><br>
          <input type="text"
                 class="txbox"
                 v-model="addEditModal.geoSummary.add_funds"/><br>

          <div class="scrolltable" style="max-height: 30vh;">
            <table class="table table-bordered table-striped table-hover">
              <thead>
              <tr>
                <th>{{ $t("common.Program name") }}</th>
                <th style="text-align: center">{{ $t("Include") }}?</th>
              </tr>
              </thead>
              <tbody>
              <tr v-for="spec in addEditModal.geoSummary.spec">
                <td>
                  {{ spec.name }}
                </td>
                <td style="text-align: center">
                  <input type="checkbox" v-model="spec.included"/>
                </td>
              </tr>
              </tbody>
            </table>
          </div>

        </div>
        <div style="text-align:center">
          <button @click="modalSave()" class='btn __green' style="display:inline-block">
            {{ $t("Save") }}
          </button>
          &nbsp;&nbsp;&nbsp;
          <button @click="$modal.hide('add-geo')" class='btn __red' style="display:inline-block">
            {{ $t("Cancel") }}
          </button>
        </div>
      </div>

    </modal>
    <!-- END ADD-GEO MODAL -->


  </div>
</template>


<script>

  import utils from '../js/utils.js'
  import router from '../router.js'

  export default {
    name: 'GeospatialPage',

    data() {
      return {
        serverDatastoreId: '',
        displayResultName: '',
        displayResultDatastoreId: '',        
        geoSummaries: [],
        geosLoaded: false,
        pollingTasks: false,
        addEditModal: {
          geoSummary: {},
          origName: '',
          mode: 'add',
        },
        figscale: 1.0,
        hasGraphs: false,
        table: [],
        datasetOptions: [],
      }
    },

    computed: {
      projectID()    { return this.$store.getters.activeProjectID },
      hasData()      { return utils.hasData(this) },
      placeholders() { return utils.placeholders() },
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
            this.updateDatasets()
            this.getGeoSummaries()
          })
      }
    },

    methods: {

      clearGraphs()                       { return utils.clearGraphs() },
      makeGraphs(graphdata)               { return utils.makeGraphs(this, graphdata) },
      exportGraphs(project_id, cache_id)  { return utils.exportGraphs(this, project_id, cache_id) },
      exportResults(project_id, cache_id) { return utils.exportResults(this, project_id, cache_id) },
      updateDatasets()                    { return utils.updateDatasets(this) },

      scaleFigs(frac) {
        this.figscale = this.figscale*frac;
        if (frac === 1.0) {
          frac = 1.0/this.figscale
          this.figscale = 1.0
        }
        return utils.scaleFigs(frac)
      },

      statusFormatStr(geoSummary) {
        if      (geoSummary.status === 'not started') {return ''}
        else if (geoSummary.status === 'queued')      {return 'Initializing... '} // + this.timeFormatStr(geoSummary.pendingTime)
        else if (geoSummary.status === 'started')     {return 'Running for '} // + this.timeFormatStr(geoSummary.executionTime)
        else if (geoSummary.status === 'completed')   {return 'Completed after '} // + this.timeFormatStr(geoSummary.executionTime)
        else if (geoSummary.status === 'error')       {return 'Error after '} // + this.timeFormatStr(geoSummary.executionTime)          
        else                                            {return ''}
      },

      timeFormatStr(geoSummary) {
        let rawValue = ''
        let is_queued = (geoSummary.status === 'queued')
        let is_executing = ((geoSummary.status === 'started') || 
          (geoSummary.status === 'completed') || (geoSummary.status === 'error'))
        if      (is_queued)    {rawValue = geoSummary.pendingTime}
        else if (is_executing) {rawValue = geoSummary.executionTime}
        else                   {return ''}

        if (rawValue === '--') {
          return '--'
        } else {
          let numSecs = Number(rawValue).toFixed()
          let numHours = Math.floor(numSecs / 3600)
          numSecs -= numHours * 3600
          let numMins = Math.floor(numSecs / 60)
          numSecs -= numMins * 60
          let output = _.padStart(numHours.toString(), 2, '0') + ':' + _.padStart(numMins.toString(), 2, '0') + ':' + _.padStart(numSecs.toString(), 2, '0')
          return output
        }
      },

      canRunTask(geoSummary)     { return (geoSummary.status === 'not started') },
      canCancelTask(geoSummary)  { return (geoSummary.status !== 'not started') },
      canPlotResults(geoSummary) { return (geoSummary.status === 'completed') },

      getGeoTaskState(geoSummary) {
        return new Promise((resolve, reject) => {
          console.log('getGeoTaskState() called for with: ' + geoSummary.status)
          let statusStr = '';
          this.$sciris.rpc('check_task', [geoSummary.serverDatastoreId]) // Check the status of the task.
            .then(result => {
              statusStr = result.data.task.status
              geoSummary.status = statusStr
              geoSummary.pendingTime = result.data.pendingTime
              geoSummary.executionTime = result.data.executionTime
              if (geoSummary.status == 'error') {
                console.log('Error in task: ', geoSummary.serverDatastoreId)
                console.log(result.data.task.errorText)
                let failMessage = 'Error in task: ' + geoSummary.serverDatastoreId
                let usermsg = result.data.task.errorText
                this.$notifications.notify({
                  message: '<b>' + failMessage + '</b>' + '<br><br>' + usermsg,
                  icon: 'ti-face-sad',
                  type: 'warning',
                  verticalAlign: 'top',
                  horizontalAlign: 'right',
                  timeout: 0
                })
                // TODO: The above works, but we want a solution that uses the line
                // below (which currently does not work).
//                this.$sciris.fail(this, failMessage, result.data.task.errorText)
              }
              resolve(result)
            })
            .catch(error => {
              geoSummary.status = 'not started'
              geoSummary.pendingTime = '--'
              geoSummary.executionTime = '--'
              resolve(error)  // yes, resolve, not reject, because this means non-started task
            })
        })
      },

      needToPoll() {
        // Check if we're still on the Geospatial page.
        let routePath = (this.$route.path === '/geospatial')
        
        // Check if we have a queued or started task.
        let runningState = false
        this.geoSummaries.forEach(geoSum => {
          if ((geoSum.status === 'queued') || (geoSum.status === 'started')) {
            runningState = true
          }
        })
        
        // We need to poll if we are in the page and a task is going.
        return (routePath && runningState)
      },
      
      pollAllTaskStates(checkAllTasks) {
        return new Promise((resolve, reject) => {
          console.log('Polling all tasks...')
          
          // Clear the poll states.
          this.geoSummaries.forEach(geoSum => {
            geoSum.polled = false
          })
          
          // For each of the optimization summaries...
          this.geoSummaries.forEach(geoSum => { 
            console.log(geoSum.serverDatastoreId, geoSum.status)
            
            // If we are to check all tasks OR there is a valid task running, check it.
            if ((checkAllTasks) ||            
              ((geoSum.status !== 'not started') && (geoSum.status !== 'completed') && 
                (geoSum.status !== 'error'))) {
              this.getGeoTaskState(geoSum)
              .then(response => {
                // Flag as polled.
                geoSum.polled = true
                
                // Resolve the main promise when all of the geoSummaries are polled.
                let done = true
                this.geoSummaries.forEach(geoSum2 => {
                  if (!geoSum2.polled) {
                    done = false
                  }
                })
                if (done) {
                  resolve()
                }
              })
            }
            
            // Otherwise (no task to check), we are done polling for it.
            else {
              // Flag as polled.
              geoSum.polled = true
              
              // Resolve the main promise when all of the geoSummaries are polled.
              let done = true
              this.geoSummaries.forEach(geoSum2 => {
                if (!geoSum2.polled) {
                  done = false
                }
              })
              if (done) {
                resolve()
              }
            }           
          })   
        })     
      },
      
      doTaskPolling(checkAllTasks) {
        // Flag that we're polling.
        this.pollingTasks = true

        // If we there are some optimization summaries...
        if (this.geoSummaries.length > 0) {         
          // Do the polling of the task states.
          this.pollAllTaskStates(checkAllTasks)
          .then(() => {
            // Hack to get the Vue display of geoSummaries to update
            this.geoSummaries.push(this.geoSummaries[0])
            this.geoSummaries.pop()
            
            // Only if we need to continue polling...
            if (this.needToPoll()) {
              // Sleep waitingtime seconds.
              let waitingtime = 1
              utils.sleep(waitingtime * 1000)
                .then(response => {
                  // Call the next polling, in a way that doesn't check_task()
                  // for _every_ task.
                  this.doTaskPolling(false)
                })         
            }
          
            // Otherwise, flag that we're no longer polling.
            else {
              this.pollingTasks = false
            }
          })

        // If the list is empty, we aren't polling.
        } else {
          this.pollingTasks = false
        }
      },
      
      clearTask(geoSummary) {
        return new Promise((resolve, reject) => {
          let datastoreId = geoSummary.serverDatastoreId  // hack because this gets overwritten soon by caller
          console.log('clearTask() called for '+this.currentGeo)
          this.$sciris.rpc('del_result', [datastoreId, this.projectID]) // Delete cached result.
            .then(response => {
              this.$sciris.rpc('delete_task', [datastoreId])
                .then(response => {
                  this.getGeoTaskState(geoSummary) // Get the task state for the optimization.
                  if (!this.pollingTasks) {
                    this.doTaskPolling(true)
                  }
                  resolve(response)
                })
                .catch(error => {
                  resolve(error)  // yes, resolve because at least cache entry deletion succeeded
                })
            })
            .catch(error => {
              reject(error)
            })
        })
      },
    
      getGeoSummaries() {
        console.log('getGeoSummaries() called')
        this.$sciris.start(this)
        this.$sciris.rpc('get_geo_info', [this.projectID]) // Get the current project's optimization summaries from the server.
          .then(response => {
            this.geoSummaries = response.data // Set the optimizations to what we received.
            this.geoSummaries.forEach(geoSum => { // For each of the optimization summaries...
              geoSum.serverDatastoreId = this.$store.state.activeProject.project.id + ':geo-' + geoSum.name // Build a task and results cache ID from the project's hex UID and the optimization name.
              geoSum.status = 'not started' // Set the status to 'not started' by default, and the pending and execution times to '--'.
              geoSum.pendingTime = '--'
              geoSum.executionTime = '--'             
            })
            this.doTaskPolling(true)  // start task polling, kicking off with running check_task() for all optimizations
            this.geosLoaded = true
            this.$sciris.succeed(this)
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not load geospatial optimizations', error)
          })
      },

      setGeoSummaries() {
        console.log('setGeoSummaries() called')
        this.$sciris.start(this)
        this.$sciris.rpc('set_geo_info', [this.projectID, this.geoSummaries])
          .then( response => {
            this.$sciris.succeed(this, 'Geospatial optimizations saved')
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not save geospatial optimizations', error)
          })
      },

      addGeoModal() {
        // Open a model dialog for creating a new geospatial optimization
        console.log('addGeoModal() called')
        this.$sciris.rpc('get_default_geo', [this.projectID])
          .then(response => {
            this.addEditModal.geoSummary = response.data
            this.addEditModal.origName = this.addEditModal.geoSummary.name
            this.addEditModal.mode = 'add'
            this.$modal.show('add-geo')
            console.log('New geospatial optimization:')
            console.log(this.addEditModal.geoSummary)
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not open add geospatial modal', error)
          })
      },

      editGeoModal(geoSummary) {
        // Open a model dialog for editing a geospatial optimization
        console.log('editGeoModal() called')
        this.addEditModal.geoSummary = _.cloneDeep(geoSummary)
        console.log('Editing geospatial optimization:')
        console.log(this.addEditModal.geoSummary)
        this.addEditModal.origName = this.addEditModal.geoSummary.name
        this.addEditModal.mode = 'edit'
        this.$modal.show('add-geo')
      },

      modalSave() {
        console.log('modalSave() called')
        this.$modal.hide('add-geo')
        this.$sciris.start(this)
        let newGeo = _.cloneDeep(this.addEditModal.geoSummary)
        let geoNames = [] // Get the list of all of the current optimization names.
        this.geoSummaries.forEach(geoSum => {
          geoNames.push(geoSum.name)
        })
        if (this.addEditModal.mode === 'edit') { // If we are editing an existing scenario...
          let index = geoNames.indexOf(this.addEditModal.origName) // Get the index of the original (pre-edited) name
          if (index > -1) {
            this.geoSummaries[index].name = newGeo.name // hack to make sure Vue table updated
            this.geoSummaries[index] = newGeo
          }
          else {
            console.log('Error: a mismatch in editing keys')
          }
        }
        else { // Else (we are adding a new optimization)...
          newGeo.name = utils.getUniqueName(newGeo.name, geoNames)
          newGeo.serverDatastoreId = this.$store.state.activeProject.project.id + ':geo-' + newGeo.name
          this.geoSummaries.push(newGeo)
          this.getGeoTaskState(newGeo)
          .then(result => {
            // Hack to get the Vue display of geoSummaries to update
            this.geoSummaries.push(this.geoSummaries[0])
            this.geoSummaries.pop()
          })
        }
        console.log('Saved geospatial optimization:')
        console.log(newGeo)
        this.$sciris.rpc('set_geo_info', [this.projectID, this.geoSummaries])
          .then( response => {
            this.$sciris.succeed(this, 'Geospatial optimization added')
			this.getGeoSummaries()  // Reload all geo optimizations so Vue state is correct (hack).
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not add geospatial optimization', error)
          })
      },

      copyGeo(geoSummary) {
        console.log('copyGeo() called')
        this.$sciris.start(this)
        var newGeo = _.cloneDeep(geoSummary);
        var otherNames = []
        this.geoSummaries.forEach(geoSum => {
          otherNames.push(geoSum.name)
        })
        newGeo.name = utils.getUniqueName(newGeo.name, otherNames)
        newGeo.serverDatastoreId = this.$store.state.activeProject.project.id + ':geo-' + newGeo.name
        this.geoSummaries.push(newGeo)
        this.getGeoTaskState(newGeo)
        this.$sciris.rpc('set_geo_info', [this.projectID, this.geoSummaries])
          .then( response => {
            this.$sciris.succeed(this, 'Geospatial optimization copied')
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not copy geospatial optimization', error)
          })
      },

      deleteGeo(geoSummary) {
        console.log('deleteGeo() called')
        this.$sciris.start(this)
        if (geoSummary.status !== 'not started') {
          this.clearTask(geoSummary)  // Clear the task from the server.
        }
        for(var i = 0; i< this.geoSummaries.length; i++) {
          if(this.geoSummaries[i].name === geoSummary.name) {
            this.geoSummaries.splice(i, 1);
          }
        }
        this.$sciris.rpc('set_geo_info', [this.projectID, this.geoSummaries])
          .then(response => {
            this.$sciris.succeed(this, 'Geospatial optimization deleted')
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not delete geospatial optimization', error)
          })
      },

      runGeo(geoSummary, runtype) {
        console.log('runGeo() called for ' + geoSummary.name + ' for time: ' + runtype)
        this.$sciris.start(this)
        this.$sciris.rpc('set_geo_info', [this.projectID, this.geoSummaries]) // Make sure they're saved first
          .then(response => {
            this.$sciris.rpc('launch_task', [geoSummary.serverDatastoreId, 'run_geo',
              [this.projectID, geoSummary.serverDatastoreId, geoSummary.name, runtype]])
              .then(response => {
                this.getGeoTaskState(geoSummary) // Get the task state for the optimization.
                if (!this.pollingTasks) {
                  this.doTaskPolling(true)
                }
                this.$sciris.succeed(this, 'Started geospatial optimization')
              })
              .catch(error => {
                this.$sciris.fail(this, 'Could not start geospatial optimization', error)
              })
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not save geospatial optimizations', error)
          })
      },

      cancelRun(geoSummary) {
        console.log('cancelRun() called for '+this.currentGeo)
        this.$sciris.rpc('delete_task', ['run_optim'])
      },

      plotGeospatial(geoSummary) {
        console.log('plotGeospatial() called')
        this.$sciris.start(this)
        this.$sciris.rpc('plot_geospatial', [this.projectID, geoSummary.serverDatastoreId])
          .then(response => {
            this.table = response.data.table
            this.makeGraphs(response.data.graphs)
            this.displayResultName = geoSummary.name
            this.displayResultDatastoreId = geoSummary.serverDatastoreId
            this.$sciris.succeed(this, 'Graphs created')
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not make graphs', error) // Indicate failure.
          })
      },
    }
  }
</script>