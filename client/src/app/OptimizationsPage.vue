<!--
Optimizations page

Last update: 2019feb11
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
        <help reflink="optimizations" :label='$t("optimization.Define optimizations")'></help>
        <table class="table table-bordered table-hover table-striped" style="width: 100%">
          <thead>
          <tr>
            <th style="text-align:center">
              <input type="checkbox" @click="modalDeselectAllOptims()" v-model="allActive"/>
            </th>
            <th>{{ $t("Name") }}</th>
            <th>{{ $t("Databook") }}</th>
            <th>{{ $t("Status") }}</th>
            <th>{{ $t("Actions") }}</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="optimSummary in optimSummaries">
            <td style="text-align: center">
              <input type="checkbox" @click="uncheckSelectAll()" v-model="optimSummary.active"/>
            </td>
            <td>
              <b>{{ optimSummary.name }}</b>
            </td>
            <td>
              <b>{{ optimSummary.model_name }}</b>
            </td>
            <td>
              {{ statusFormatStr(optimSummary) }}
              {{ timeFormatStr(optimSummary) }}
            </td>
            <td style="white-space: nowrap">
              <button class="btn __green" :disabled="!canRunTask(optimSummary)" @click="runOptim(optimSummary, 'full')">{{ $t("common.Run") }}</button>
              <button class="btn" :disabled="!canRunTask(optimSummary)" @click="runOptim(optimSummary, 'test')">{{ $t("common.Test run") }}</button>
              <button class="btn __red" :disabled="!canCancelTask(optimSummary)" @click="clearTask(optimSummary)">{{ $t("common.Clear results") }}</button>
              <button class="btn btn-icon" @click="editOptimModal(optimSummary)" :data-tooltip='$t("optimization.Edit optimization")'><i class="ti-pencil"></i></button>
              <button class="btn btn-icon" @click="copyOptim(optimSummary)" :data-tooltip='$t("optimization.Copy optimization")'><i class="ti-files"></i></button>
              <button class="btn btn-icon" @click="deleteOptim(optimSummary)" :data-tooltip='$t("optimization.Delete optimization")'><i class="ti-trash"></i></button>
            </td>
          </tr>
          </tbody>
        </table>

        <div>
          <input type="checkbox" id="costeff_checkbox" v-model="calculateCostEff"/>
          <label for="costeff_checkbox">{{ $t("optimization.perform_costeff") }}</label>
        </div>

        <div>
          <button class="btn __green" :disabled="!optimsLoaded || !anySelected" @click="plotOptims(0)">{{ $t("optimization.Plot optimizations") }}</button>
          <button class="btn __green" :disabled="!optimsLoaded || calculateCostEff || !anySelected" @click="UncertScensModal(10)">{{ $t("optimization.Plot optimizations with uncertainty") }}</button>
          <button class="btn" :disabled="!optimsLoaded" @click="addOptimModal()">{{ $t("optimization.Add optimization") }}</button>
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
          <button class="btn" @click="exportGraphs(projectID, 'opts')">{{ $t("common.Export plots") }}</button>
          <button class="btn" @click="exportResults(projectID, 'opts')">{{ $t("common.Export data") }}</button>
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
      <div v-if="hasTable">
        <help reflink="cost-effectiveness" label="Program cost-effectiveness"></help>
        <div class="calib-graphs" style="display:inline-block; text-align:right; overflow:auto">
          <table class="table table-bordered table-hover table-striped">
            <thead>
            <tr>
              <th>{{ $t("optimization.Optimization/program") }}</th>
              <th>{{ $t("Outcomes") }}</th>
              <th v-for="i in table[0].length-3"></th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="rowdata in table">
              <td v-for="i in (rowdata.length-1)">
                <span v-if="rowdata[0]==='header'" style="font-size:15px; font-weight:bold">{{rowdata[i]}}</span>
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


    <!-- START ADD-OPTIM MODAL :width="900" -->
    <modal name="add-optim"
           height="auto"
           :scrollable="true"
           :classes="['v--modal', 'vue-dialog']"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="false">

      <div class="dialog-content">
        <div class="dialog-c-title" v-if="addEditModal.mode=='add'">
          {{ $t("optimization.Add optimization") }}
        </div>
        <div class="dialog-c-title" v-else>
          {{ $t("optimization.Edit optimization") }}
        </div>
        <div class="dialog-c-text" style="display:inline-block">
          <b>{{ $t("optimization.Optimization name") }}</b><br>
          <input type="text"
                 class="txbox"
                 v-model="addEditModal.optimSummary.name"/><br>
          <b>{{ $t("Databook") }}</b><br>
          <tr>
            <th><select v-model="addEditModal.optimSummary.model_name" @change="modalSwitchDataset">
              <option v-for='dataset in datasetOptions'>
                {{ dataset }}
              </option>
            </select><br><br></th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            <td style="text-align: center">
              <input type="checkbox" v-model="addEditModal.optimSummary.balanced_optimization"/>&nbsp;{{ $t("optimization.Run balanced optimization?") }}
            </td>
          </tr>
          <div class="scrolltable" style="max-height: 30vh;">
            <table class="table table-bordered table-striped table-hover">
              <thead>
              <tr>
                <th>{{ $t("optimization.Optimization objective") }}</th>
                <th>{{ $t("optimization.Weight") }}</th>
              </tr>
              </thead>
              <tbody>
              <tr v-for="item in addEditModal.optimSummary.weightslist">
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
          <b>{{ $t("optimization.Budget multipliers") }}</b> (1 = {{ $t("optimization.current budget") }})<br>
          <input type="text"
                 class="txbox"
                 v-model="addEditModal.optimSummary.mults"/><br>
          <b>{{ $t("optimization.Existing spending") }}</b><br>
          <input type="radio" v-model="addEditModal.optimSummary.fix_curr" :value="false">&nbsp;{{ $t("common.Can be reallocated") }}<br>
          <input type="radio" v-model="addEditModal.optimSummary.fix_curr" :value="true">&nbsp;{{ $t("common.Cannot be reallocated") }}<br><br>
          <b>{{ $t("optimization.Growth type") }}</b><br>
          <input type="radio" v-model="addEditModal.optimSummary.growth" value="fixed budget">&nbsp;{{ $t("optimization.Fixed budget") }}<br>
          <input type="radio" v-model="addEditModal.optimSummary.growth" value="fixed coverage">&nbsp;{{ $t("optimization.Fixed coverage") }}<br><br>
          <b>{{ $t("optimization.Additional funds to allocate") }}</b><br>
          <input type="text"
                 class="txbox"
                 v-model="addEditModal.optimSummary.add_funds"/><br>

          <div class="scrolltable" style="max-height: 30vh;">
            <table class="table table-bordered table-striped table-hover">
              <thead>
              <tr>
                <th>{{ $t("common.Program name") }}</th>
                <th style="text-align: center">{{ $t("Include") }}?</th>
              </tr>
              </thead>
              <tbody>
              <tr v-for="program in addEditModal.optimSummary.programs">
                <td>
                  {{ program.name }}
                </td>
                <td style="text-align: center">
                  <input type="checkbox" v-model="program.included"/>
                </td>
              </tr>
              </tbody>
            </table>
          </div>
          <button class="btn" @click="modalDeselectAllProgs()" :data-tooltip='$t("optimization.Deselect all interventions")'>{{ $t("Deselect all") }}</button>
        </div>
        <div style="text-align:center">
          <button @click="modalSave()" class='btn __green' style="display:inline-block">
            {{ $t("Save") }}
          </button>
          &nbsp;&nbsp;&nbsp;
          <button @click="$modal.hide('add-optim')" class='btn __red' style="display:inline-block">
            {{ $t("Cancel") }}
          </button>
        </div>
      </div>

    </modal>
    <!-- END ADD-OPTIM MODAL -->

    <!-- ### Start: input uncertainty runs modal ### -->
    <modal name="uncert-nruns"
           height="auto"
           :classes="['v--modal', 'vue-dialog']"
           :width="400"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="false"
    >

      <div class="dialog-content">
        <div class="dialog-c-title">
          Input uncertainty runs
        </div>
        <div class="dialog-c-text">
          Number of runs:<br>
          <input type="text"
                 class="txbox"
                 v-model="modalUncertRuns"/><br>
        </div>
        <div style="text-align:justify">
          <button @click="plotOptims(modalUncertRuns)  | $modal.hide('uncert-nruns')" class='btn __green' style="display:inline-block">
            {{ $t("optimization.Plot optimizations") }}
          </button>

          <button @click="$modal.hide('uncert-nruns')" class='btn __red' style="display:inline-block">
            {{ $t("Cancel") }}
          </button>
        </div>
      </div>

    </modal>
    <!-- ### End: input uncertainty runs modal ### -->
  </div>


  </div>
</template>


<script>

  import utils from '../js/utils.js'
  import router from '../router.js'
  import i18n from '../i18n'

  export default {
    name: 'OptimizationsPage',

    data() {
      return {
        allActive: true,
        serverDatastoreId: '',
        displayResultName: '',
        displayResultDatastoreId: '',
        optimSummaries: [],
        scenSummaries: [],
        scenariosLoaded: false,
        optimsLoaded: false,
        pollingTasks: false,
        datasetOptions: [],
        growthOptions: [],
        addEditModal: {
          optimSummary: {},
          mode: 'add',
        },
        modalUncertRuns: 10,  // Number of runs in the uncertainty nruns modal dialog
        figscale: 1.0,
        hasGraphs: false,
        calculateCostEff: false,
        hasTable: false,
        table: [],
        withUncert: false,
      }
    },

    computed: {
      projectID() {
        return this.$store.getters.activeProjectID
      },
      hasData() {
        return utils.hasData(this)
      },
      placeholders() {
        return utils.placeholders()
      },
      anySelected() { return this.optimSummaries.some(x => x.active) },
    },

    created() {
      if (this.$store.state.currentUser.displayname === undefined) { // If we have no user logged in, automatically redirect to the login page.
        router.push('/login')
      } else if ((this.$store.state.activeProject.project !== undefined) &&
          (this.$store.state.activeProject.project.hasData)) {
        console.log('created() called')
        if (this.$store.state.activeProject === this.$store.state.checkProject) {
          this.getOptimSummaries(this.$store.state.optimSummaries)
        }
        else {
          this.getOptimSummaries(null)
        }
        this.updateDatasets()
      }
    },

    methods: {

      updateDatasets() {
        return utils.updateDatasets(this)
      },
      clearGraphs() {
        return utils.clearGraphs()
      },
      makeGraphs(graphdata) {
        return utils.makeGraphs(this, graphdata)
      },
      exportGraphs(project_id, cache_id) {
        return utils.exportGraphs(this, project_id, cache_id)
      },
      exportResults(project_id, cache_id) {
        return utils.exportResults(this, project_id, cache_id)
      },

      scaleFigs(frac) {
        this.figscale = this.figscale * frac;
        if (frac === 1.0) {
          frac = 1.0 / this.figscale
          this.figscale = 1.0
        }
        return utils.scaleFigs(frac)
      },

      statusFormatStr(optimSummary) {
        if (optimSummary.status === 'not started') {
          return ''
        } else if (optimSummary.status === 'queued') {
          return this.$t('Initializing') + '... '
        } // + this.timeFormatStr(optimSummary.pendingTime)
        else if (optimSummary.status === 'started') {
          return this.$t('Running for') + ' '
        } // + this.timeFormatStr(optimSummary.executionTime)
        else if (optimSummary.status === 'completed') {
          return this.$t('Completed after') + ' '
        } // + this.timeFormatStr(optimSummary.executionTime)
        else if (optimSummary.status === 'error') {
          return this.$t('Error after') + ' '
        } // + this.timeFormatStr(optimSummary.executionTime)
        else {
          return ''
        }
      },

      timeFormatStr(optimSummary) {
        let rawValue = ''
        let is_queued = (optimSummary.status === 'queued')
        let is_executing = ((optimSummary.status === 'started') ||
            (optimSummary.status === 'completed') || (optimSummary.status === 'error'))
        if (is_queued) {
          rawValue = optimSummary.pendingTime
        } else if (is_executing) {
          rawValue = optimSummary.executionTime
        } else {
          return ''
        }

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

      canRunTask(optimSummary) {
        return (optimSummary.status === 'not started')
      },
      canCancelTask(optimSummary) {
        return (optimSummary.status !== 'not started')
      },
      canPlotResults(optimSummary) {
        return (optimSummary.status === 'completed')
      },

      getOptimTaskState(optimSummary) {
        return new Promise((resolve, reject) => {
          console.log('getOptimTaskState() called for with: ' + optimSummary.status)
          let statusStr = '';
          this.$sciris.rpc('check_task', [optimSummary.serverDatastoreId]) // Check the status of the task.
              .then(result => {
                statusStr = result.data.task.status
                optimSummary.status = statusStr
                optimSummary.pendingTime = result.data.pendingTime
                optimSummary.executionTime = result.data.executionTime
                if (optimSummary.status === 'error') {
                  console.log('Error in task: ', optimSummary.serverDatastoreId)
                  console.log(result.data.task.errorText)
                  let failMessage = 'Error in task: ' + optimSummary.serverDatastoreId
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
                optimSummary.status = 'not started'
                optimSummary.pendingTime = '--'
                optimSummary.executionTime = '--'
                resolve(error)  // yes, resolve, not reject, because this means non-started task
              })
        })
      },

      needToPoll() {
        // Check if we're still on the Optimizations page.
        let routePath = (this.$route.path === '/optimizations')

        // Check if we have a queued or started task.
        let runningState = false
        this.optimSummaries.forEach(optimSum => {
          if ((optimSum.status === 'queued') || (optimSum.status === 'started')) {
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
          this.optimSummaries.forEach(optimSum => {
            optimSum.polled = false
          })

          // For each of the optimization summaries...
          this.optimSummaries.forEach(optimSum => {
            console.log(optimSum.serverDatastoreId, optimSum.status)

            // If we are to check all tasks OR there is a valid task running, check it.
            if ((checkAllTasks) ||
                ((optimSum.status !== 'not started') && (optimSum.status !== 'completed') &&
                    (optimSum.status !== 'error'))) {
              this.getOptimTaskState(optimSum)
                  .then(response => {
                    // Flag as polled.
                    optimSum.polled = true

                    // Resolve the main promise when all of the optimSummaries are polled.
                    let done = true
                    this.optimSummaries.forEach(optimSum2 => {
                      if (!optimSum2.polled) {
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
              optimSum.polled = true

              // Resolve the main promise when all of the optimSummaries are polled.
              let done = true
              this.optimSummaries.forEach(optimSum2 => {
                if (!optimSum2.polled) {
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
        if (this.optimSummaries.length > 0) {
          // Do the polling of the task states.
          this.pollAllTaskStates(checkAllTasks)
              .then(() => {
                // Hack to get the Vue display of optimSummaries to update
                this.optimSummaries.push(this.optimSummaries[0])
                this.optimSummaries.pop()

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

      clearTask(optimSummary) {
        return new Promise((resolve, reject) => {
          let datastoreId = optimSummary.serverDatastoreId  // hack because this gets overwritten soon by caller
          console.log('clearTask() called for ' + this.currentOptim)
          this.$sciris.rpc('clear_optim_scens', [this.projectID, optimSummary.uid]) // Delete cached result.
              .then(response => {
                this.$sciris.rpc('delete_task', [datastoreId])
                    .then(response => {
                      this.getOptimTaskState(optimSummary) // Get the task state for the optimization.
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

      async getOptimSummaries(oldSummaries) {
        console.log('getOptimSummaries() called');
        this.$sciris.start(this);
        try {
          let response = await this.$sciris.rpc('get_optim_info', [this.projectID]);
          response.data.forEach((optimSum, index) => { // For each of the optimization summaries...
            optimSum.serverDatastoreId = this.$store.state.activeProject.project.id + ':opt-' + optimSum.name; // Build a task and results cache ID from the project's hex UID and the optimization name.
            optimSum.status = 'not started'; // Set the status to 'not started' by default, and the pending and execution times to '--'.
            optimSum.pendingTime = '--';
            optimSum.executionTime = '--';
            if ((oldSummaries !== null)  &&  (oldSummaries !== undefined)) {
              if (oldSummaries[index] !== undefined) {
                optimSum.active = oldSummaries[index].active;
              }
              else {
                optimSum.active = true;
              }
            }
            else if ((oldSummaries === null) ||  (oldSummaries === undefined)) {
              optimSum.active = true;
            }
          })
          this.optimSummaries = response.data; // Set the optimizations to what we received.
          this.doTaskPolling(true);  // start task polling, kicking off with running check_task() for all optimizations
          this.optimsLoaded = true;
          this.$store.commit('newOptimSummaries', this.optimSummaries)
          this.$sciris.succeed(this)
        } catch (error) {
          this.$sciris.fail(this, 'Could not load optimizations', error);
        }
      },

      addOptimModal() {
        // Open a model dialog for creating a new optimization
        console.log('addOptimModal() called');
        this.$sciris.rpc('opt_new_optim', [this.projectID, this.datasetOptions[0], i18n.locale])
            .then(response => {
              this.addEditModal.optimSummary = response.data
              this.addEditModal.mode = 'add'
              this.addEditModal.optimSummary.model_name = this.datasetOptions[0]
              this.addEditModal.optimSummary.active = true
              this.$modal.show('add-optim')
              console.log('New optimization:')
              console.log(this.addEditModal.optimSummary)
            })
            .catch(error => {
              this.$sciris.fail(this, 'Could not open add optimization modal', error)
            })
      },

      editOptimModal(optimSummary) {
        // Open a model dialog for editing an optimization
        console.log('editOptimModal() called');
        this.addEditModal.optimSummary = _.cloneDeep(optimSummary);
        console.log('Editing optimization:');
        console.log(this.addEditModal.optimSummary);
        this.addEditModal.mode = 'edit';
        this.addEditModal.optimSummary.active = true
        this.$modal.show('add-optim')
      },

      async modalSwitchDataset() {
        console.log('modalSwitchDataset() called');
        try {
          let response = await this.$sciris.rpc('opt_switch_dataset', [this.projectID, this.addEditModal.optimSummary]);
          this.addEditModal.optimSummary = response.data;  // overwrite the old optimization
        } catch (error) {
          this.$sciris.fail(this, 'Could not switch databooks', error)
        }
      },

      modalDeselectAllProgs() {
        this.addEditModal.optimSummary.programs.forEach(progval => {
          progval.included = false;
        })
      },

      modalDeselectAllOptims() {
        this.optimSummaries.forEach(optimSummary => optimSummary.active = !this.allActive)
      },

      uncheckSelectAll() {
        this.allActive = false
      },

      async modalSave() {
        console.log('modalSave() called')
        this.$modal.hide('add-optim')
        this.$sciris.start(this)

        let newOptim = _.cloneDeep(this.addEditModal.optimSummary)
        newOptim.name = utils.getUniqueName(newOptim.name, this.optimSummaries.filter(x => x.uid !== newOptim.uid).map(x => x.name)) // Force it to have a unique name

        if (this.addEditModal.mode === 'edit') { // If we are editing an existing scenario...
          let index = this.optimSummaries.map(x => x.uid).indexOf(newOptim.uid) // Get the index of the original (pre-edited) name
          this.optimSummaries[index] = newOptim
          this.optimSummaries[index].active = true
          await this.$sciris.rpc('set_optim_info', [this.projectID, this.optimSummaries])
        } else { // Else (we are adding a new optimization)...
          newOptim.serverDatastoreId = this.$store.state.activeProject.project.id + ':opt-' + newOptim.name
          let response = await this.$sciris.rpc('create_optim', [this.projectID, newOptim])
          newOptim.uid = response.data;
          this.optimSummaries.push(newOptim)
        }
        this.$sciris.succeed(this, 'Optimization added')
        this.getOptimSummaries(this.optimSummaries)  // Reload all optimizations so Vue state is correct
      },

      async copyOptim(optimSummary) {
        console.log('copyOptim() called')
        this.$sciris.start(this)
        var newOptim = _.cloneDeep(optimSummary);
        var otherNames = []
        this.optimSummaries.forEach(optimSum => {
          otherNames.push(optimSum.name)
        })
        newOptim.name = utils.getUniqueName(newOptim.name, otherNames)
        newOptim.serverDatastoreId = this.$store.state.activeProject.project.id + ':opt-' + newOptim.name
        let response = await this.$sciris.rpc('create_optim', [this.projectID, newOptim])
        newOptim.uid = response.data;
        this.optimSummaries.push(newOptim)
        this.getOptimTaskState(newOptim)
        this.$sciris.succeed(this, 'Optimization copied')
      },

      deleteOptim(optimSummary) {
        console.log('deleteOptim() called')
        this.$sciris.start(this)
        if (optimSummary.status !== 'not started') {
          this.clearTask(optimSummary)  // Clear the task from the server.
        }
        for (var i = 0; i < this.optimSummaries.length; i++) {
          if (this.optimSummaries[i].name === optimSummary.name) {
            this.optimSummaries.splice(i, 1);
          }
        }
        this.$sciris.rpc('set_optim_info', [this.projectID, this.optimSummaries])
            .then(response => {
              this.$sciris.succeed(this, 'Optimization deleted')
            })
            .catch(error => {
              this.$sciris.fail(this, 'Could not delete optimization', error)
            })
      },

      runOptim(optimSummary, runtype) {
        console.log('runOptim() called for ' + optimSummary.name + ' for time: ' + runtype)
        this.$sciris.start(this)
        this.$sciris.rpc('set_optim_info', [this.projectID, this.optimSummaries]) // Make sure they're saved first
            .then(response => {
              this.$sciris.rpc('launch_task', [optimSummary.serverDatastoreId, 'run_optim',
                [this.projectID, optimSummary.serverDatastoreId, optimSummary.name, runtype, optimSummary.balanced_optimization]])
                  .then(response => {
                    this.getOptimTaskState(optimSummary) // Get the task state for the optimization.
                    if (!this.pollingTasks) {
                      this.doTaskPolling(true)
                    }
                    this.$sciris.succeed(this, 'Started optimization')
                  })
                  .catch(error => {
                    this.$sciris.fail(this, 'Could not start optimization', error)
                  })
            })
            .catch(error => {
              this.$sciris.fail(this, 'Could not save optimizations', error)
            })
      },

      cancelRun(optimSummary) {
        console.log('cancelRun() called for ' + this.currentOptim)
        this.$sciris.rpc('delete_task', ['run_optim'])
      },


      async plotOptims(n_uncert_runs) {
        this.$sciris.start(this)
        try{
          let response = await this.$sciris.rpc('run_opt_scens', [this.projectID, this.optimSummaries.filter(x => x.active).map(x => x.uid), this.calculateCostEff, n_uncert_runs]) // Go to the server to get the results
          this.hasTable = this.calculateCostEff
          this.table = response.data.table
          this.makeGraphs(response.data.graphs)
          this.withUncert = n_uncert_runs > 0
          this.$sciris.succeed(this, '')
        } catch (error) {
          this.$sciris.fail(this, 'Could not plot optimization scenarios', error)
        }
      },


      UncertScensModal(nruns) {
        console.log('UncertScensModal() called');
        this.modalUncertRuns = nruns
        this.$modal.show('uncert-nruns');
      },
    }
  }
</script>