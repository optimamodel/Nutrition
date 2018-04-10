<!--
Define disease burden

Last update: 2018-03-25
-->

<template>
  <div class="SitePage">

    <div v-if="activeProjectName === ''">
      <div style="font-style:italic">
        <p>Hmm, I can't find any disease burdens...did you forget to <router-link class="link __blue" to="/projects">load a project</router-link>?</p>
      </div>
    </div>

    <div class="PageSection" v-if="activeProjectName !== ''">

      <button class="btn" @click="createNewBurdenSet">Create new burden set</button>

      <span>&nbsp;based on&nbsp;</span>

      <select
        title="countrySelect"
        id="country"
        :required="true"
        v-model="country">
        <option
          v-for = "country in countryList"
          :value="country"
        >
          {{country}}
        </option>
      </select>

      <br/><br/>

      <input type="text"
             class="txbox"
             style="margin-left:0px; margin-bottom:10px; display:inline-block; width:100%"
             :placeholder="filterPlaceholder"
             v-model="filterText"/>

      <table class="table table-bordered table-hover table-striped" style="width: 100%">
        <thead>
          <tr>
            <th @click="updateSorting('name')" class="sortable">
              Burden set
              <span v-show="sortColumn == 'name' && !sortReverse">
                <i class="fas fa-caret-down"></i>
              </span>
              <span v-show="sortColumn == 'name' && sortReverse">
                <i class="fas fa-caret-up"></i>
              </span>
              <span v-show="sortColumn != 'name'">
                <i class="fas fa-caret-up" style="visibility: hidden"></i>
              </span>
            </th>
            <th>
              Select
            </th>
            <th @click="updateSorting('creationTime')" class="sortable">
              Created on
              <span v-show="sortColumn == 'creationTime' && !sortReverse">
                <i class="fas fa-caret-down"></i>
              </span>
              <span v-show="sortColumn == 'creationTime' && sortReverse">
                <i class="fas fa-caret-up"></i>
              </span>
              <span v-show="sortColumn != 'creationTime'">
                <i class="fas fa-caret-up" style="visibility: hidden"></i>
              </span>
            </th>
            <th @click="updateSorting('updatedTime')" class="sortable">
              Last modified
              <span v-show="sortColumn == 'updatedTime' && !sortReverse">
                <i class="fas fa-caret-down"></i>
              </span>
              <span v-show="sortColumn == 'updatedTime' && sortReverse">
                <i class="fas fa-caret-up"></i>
              </span>
              <span v-show="sortColumn != 'updatedTime'">
                <i class="fas fa-caret-up" style="visibility: hidden"></i>
              </span>
            </th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="burdenSet in sortedFilteredBurdenSets"
              :class="{ highlighted: burdenSetIsSelected(burdenSet) }">
            <td v-if="burdenSet.renaming !== ''">
			        <input type="text"
                     class="txbox"
                     @keyup.enter="renameBurdenSet(burdenSet)"
                     v-model="burdenSet.renaming"/>
			      </td>
			      <td v-else>
			        {{ burdenSet.burdenset.name }}
			      </td>
            <td><button class="btn __green" @click="viewBurdenSet(burdenSet)">Open</button></td>
            <td>{{ burdenSet.burdenset.creationTime }}</td>
            <td>{{ burdenSet.burdenset.updateTime ? burdenSet.burdenset.updateTime:
              'No modification' }}</td>
            <td style="white-space: nowrap">
              <button class="btn" @click="renameBurdenSet(burdenSet)">Rename</button>
              <button class="btn" @click="copyBurdenSet(burdenSet)">Copy</button>
              <button class="btn __red" @click="deleteBurdenSet(burdenSet)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="PageSection UIPlaceholder" v-if="activeBurdenSet.burdenset != undefined">
      <button class="btn" @click="makeGraph(activeBurdenSet)">Visualize</button>

      <div>
        <div id="fig01" style="float:left" ></div>
        <div id="fig02" style="float:left" ></div>
        <!--<div id="fig03" style="float:left" ></div>-->
      </div>




      <table class="table table-bordered table-hover table-striped" style="width: 100%; margin-top: 10px;">
        <thead>
          <tr>
            <th style="text-align:center">
              Active
            </th>
            <th @click="updateSorting2('name')" class="sortable">
              Cause name
              <span v-show="sortColumn2 == 'name' && !sortReverse2">
                <i class="fas fa-caret-down"></i>
              </span>
              <span v-show="sortColumn2 == 'name' && sortReverse2">
                <i class="fas fa-caret-up"></i>
              </span>
              <span v-show="sortColumn2 != 'name'">
                <i class="fas fa-caret-up" style="visibility: hidden"></i>
              </span>
            </th>
            <th @click="updateSorting2('DALYs')" class="sortable">
              DALYs
              <span v-show="sortColumn2 == 'DALYs' && !sortReverse2">
                <i class="fas fa-caret-down"></i>
              </span>
              <span v-show="sortColumn2 == 'DALYs' && sortReverse2">
                <i class="fas fa-caret-up"></i>
              </span>
              <span v-show="sortColumn2 != 'DALYs'">
                <i class="fas fa-caret-up" style="visibility: hidden"></i>
              </span>
            </th>
            <th @click="updateSorting2('deaths')" class="sortable">
              Deaths
              <span v-show="sortColumn2 == 'deaths' && !sortReverse2">
                <i class="fas fa-caret-down"></i>
              </span>
              <span v-show="sortColumn2 == 'deaths' && sortReverse2">
                <i class="fas fa-caret-up"></i>
              </span>
              <span v-show="sortColumn2 != 'deaths'">
                <i class="fas fa-caret-up" style="visibility: hidden"></i>
              </span>
            </th>
            <th @click="updateSorting2('prevalence')" class="sortable">
              Prevalence
              <span v-show="sortColumn2 == 'prevalence' && !sortReverse2">
                <i class="fas fa-caret-down"></i>
              </span>
              <span v-show="sortColumn2 == 'prevalence' && sortReverse2">
                <i class="fas fa-caret-up"></i>
              </span>
              <span v-show="sortColumn2 != 'prevalence'">
                <i class="fas fa-caret-up" style="visibility: hidden"></i>
              </span>
            </th>
            <th style="text-align:center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="disease in sortedDiseases">
            <td style="text-align: center">
              <input type="checkbox" v-model="disease.active"/>
            </td>
            <td>
              <input type="text"
                     class="txbox"
                     @keyup.enter="notImplemented('Rename cause')"
                     v-model="disease.cause"/>
            </td>
            <td>
              <input type="text"
                     class="txbox"
                     @keyup.enter="notImplemented('Edit DALYs')"
                     v-model="disease.dalys"/>
            </td>
            <td>
              <input type="text"
                     class="txbox"
                     @keyup.enter="notImplemented('Edit deaths')"
                     v-model="disease.deaths"/>
            </td>
            <td>
              <input type="text"
                     class="txbox"
                     @keyup.enter="notImplemented('Edit prevalence')"
                     v-model="disease.prevalence"/>
            </td>
            <td style="white-space: nowrap; text-align:center">
              <button class="iconbtn" @click="notImplemented('Copy')"><i class="ti-layers"></i></button>
              <button class="iconbtn" @click="notImplemented('Delete')"><i class="ti-trash"></i></button>
            </td>
          </tr>
        </tbody>
      </table>
      <button class="btn" @click="notImplemented('Add new burden type')">Add new burden type</button>

      <!--<template>-->
        <!--Testing handsontable-->
        <!--<div id="hot-preview">-->
          <!--<HotTable :root="root" :settings="hotSettings"></HotTable>-->
        <!--</div>-->
      <!--</template>-->

    </div>
  </div>
</template>

<script>
  import axios from 'axios'
  var filesaver = require('file-saver')
  import rpcservice from '@/services/rpc-service'
  import router from '@/router'
//  import HotTable from 'vue-handsontable-official';
  import Vue from 'vue';

  export default {
    name: 'DiseaseBurdenPage',
//    components: {
//        HotTable
//    },
    data() {
      return {
        // Placeholder text for table filter box
        filterPlaceholder: 'Type here to filter burden sets',

        // Text in the table filter box
        filterText: '',

        // Column of table used for sorting the burden sets
        sortColumn: 'updatedTime',  // name, creationTime, updatedTime

        // Sort in reverse order?
        sortReverse: false,

        root: 'test-hot',
        hotSettings: {
          data: [['sample', 'data']],
          colHeaders: true
        },

        // List of burden sets in the active project
        burdenSets: [],

        // Active burden set
        activeBurdenSet: {},

        // List of diseases.  Each list element is a list of the ailment name
        // and numbers associated with it.
        diseaseList: [],

        // Column of table used for sorting the diseases
        sortColumn2: 'name',  // name, country, creationTime, updatedTime

        // Sort diseases in reverse order?
        sortReverse2: false,

        // CK: WARNING TEMP, should come from backend
        country: 'Afghanistan',
        countryList: [
          'Afghanistan',
          'Other',
        ],

        serverresponse: 'no response',
      }
    },

    computed: {
      activeProjectName() {
        if (this.$store.state.activeProject.project === undefined) {
          return ''
        } else {
          return this.$store.state.activeProject.project.name
        }
      },

      sortedFilteredBurdenSets() {
        return this.applyNameFilter(this.applySorting(this.burdenSets))
      },

      sortedDiseases() {
        var sortedDiseaseList =  this.applySorting2(this.diseaseList);
        Vue.set(this.hotSettings, 'data', [[1,2,3]]);
        console.log(sortedDiseaseList);
        return sortedDiseaseList;
      },

    },

    created() {
      // If we have no user logged in, automatically redirect to the login page.
      if (this.$store.state.currentUser.displayname == undefined) {
        router.push('/login')
      }

      // Otherwise...
      else {
        // Load the burden sets from the active project, telling the function
        // to also set the active burden set to the last item.
        this.updateBurdenSets(true)
      }
    },

    methods: {

      notImplemented(message) {
        this.$notifications.notify({
          message: 'Function "' + message + '" not yet implemented',
          icon: 'ti-face-sad',
          type: 'warning',
          verticalAlign: 'top',
          horizontalAlign: 'center',
        });
      },

      updateBurdenSets(setLastEntryActive=false) {
        console.log('updateBurdenSets() called')

        // If there is no active project, clear the burdenSets list.
        if (this.$store.state.activeProject.project === undefined) {
          this.burdenSets = []
        }

        // Otherwise...
        else {
          // Get the active project's burden sets.
          rpcservice.rpcProjectCall('get_project_burden_sets',
            [this.$store.state.activeProject.project.id])
          .then(response => {
            // Set the burden set list to what we received.
            this.burdenSets = response.data.burdensets

            // Add numindex elements to the burden sets to keep track of
		        // which index to pull from the server.
            for (let ind=0; ind < this.burdenSets.length; ind++)
              this.burdenSets[ind].burdenset.numindex = ind

            // Set renaming values to blank initially.
            this.burdenSets.forEach(theSet => {
		          theSet.renaming = ''
		        })

            // If we want to set the last entry active and we have any
            // entries, do the setting.
            if ((setLastEntryActive) && (this.burdenSets.length > 0))
              this.viewBurdenSet(this.burdenSets[this.burdenSets.length - 1])
          })
        }
      },

      burdenSetIsSelected(burdenSet) {
        // If the active burden set is undefined, it is not active.
        if (this.activeBurdenSet.burdenset === undefined) {
          return false
        }

        // Otherwise, the burden set is selected if the numindexes match.
        else {
          return (this.activeBurdenSet.burdenset.numindex === burdenSet.burdenset.numindex)
        }
      },

      updateSorting(sortColumn) {
        console.log('updateSorting() called')

        // If the active sorting column is clicked...
        if (this.sortColumn === sortColumn) {
            // Reverse the sort.
            this.sortReverse = !this.sortReverse
        }
        // Otherwise.
        else {
          // Select the new column for sorting.
          this.sortColumn = sortColumn

          // Set the sorting for non-reverse.
          this.sortReverse = false
        }
      },

      applyNameFilter(sets) {
        return sets.filter(theSet => theSet.burdenset.name.toLowerCase().indexOf(this.filterText.toLowerCase()) !== -1)
      },

      applySorting(sets) {
        return sets.sort((set1, set2) =>
          {
            let sortDir = this.sortReverse ? -1: 1
            if (this.sortColumn === 'name') {
              return (set1.burdenset.name > set2.burdenset.name ? sortDir: -sortDir)
            }
            else if (this.sortColumn === 'creationTime') {
              return set1.burdenset.creationTime > set2.burdenset.creationTime ? sortDir: -sortDir
            }
            else if (this.sortColumn === 'updatedTime') {
              return set1.burdenset.updateTime > set2.burdenset.updateTime ? sortDir: -sortDir
            }
          }
        )
      },

      viewBurdenSet(burdenSet) {
        console.log('viewBurdenSet() called for ' + burdenSet.burdenset.name)

        // Set the active project to the burdenSet passed in.
        this.activeBurdenSet = burdenSet

        // Go to the server to get the diseases from the burden set.
        rpcservice.rpcProjectCall('get_project_burden_set_diseases',
          [this.$store.state.activeProject.project.id, this.activeBurdenSet.burdenset.numindex])
        .then(response => {
          // Set the disease list.
          this.diseaseList = response.data.diseases

          // Set the active values from the loaded in data.
          this.diseaseList.forEach(theDisease => {
		        theDisease.active = theDisease[0];
            theDisease.cause = theDisease[1];
            theDisease.dalys = Number(theDisease[2]).toLocaleString();
            theDisease.deaths = Number(theDisease[3]).toLocaleString();
            theDisease.prevalence = Number(theDisease[4]).toLocaleString();
		      })

          // Reset the bottom table sorting state.
          this.sortColumn2 = 'name'
          this.sortReverse2 = false
        })

        this.$notifications.notify({
          message: 'Burden set "' + burdenSet.burdenset.name + '" now active',
          icon: 'ti-check',
          type: 'success',
          verticalAlign: 'top',
          horizontalAlign: 'center',
        });
      },

      copyBurdenSet(burdenSet) {
        console.log('copyBurdenSet() called for ' + burdenSet.burdenset.name)

	      // Have the server copy the burden set, giving it a new name.
        rpcservice.rpcProjectCall('copy_burden_set',
          [this.$store.state.activeProject.project.id, burdenSet.burdenset.numindex])
        .then(response => {
          // Update the burden sets so the new set shows up on the list.
          this.updateBurdenSets()
        })
      },

      renameBurdenSet(burdenSet) {
        console.log('renameBurdenSet() called for ' + burdenSet.burdenset.name)

	      // If the burden set is not in a mode to be renamed, make it so.
	      if (burdenSet.renaming === '') {
		      burdenSet.renaming = burdenSet.burdenset.name
        }

	      // Otherwise (it is to be renamed)...
	      else {
          // Have the server change the name of the burden set.
          rpcservice.rpcProjectCall('rename_burden_set',
            [this.$store.state.activeProject.project.id,
            burdenSet.burdenset.numindex, burdenSet.renaming])
          .then(response => {
            // Update the burden sets so the renamed one shows up on the list.
            this.updateBurdenSets()

		        // Turn off the renaming mode.
		        burdenSet.renaming = ''
          })
        }

	      // This silly hack is done to make sure that the Vue component gets updated by this function call.
	      // Something about resetting the burden set name informs the Vue component it needs to
	      // update, whereas the renaming attribute fails to update it.
	      // We should find a better way to do this.
        let theName = burdenSet.burdenset.name
        burdenSet.burdenset.name = 'newname'
        burdenSet.burdenset.name = theName
      },

      deleteBurdenSet(burdenSet) {
        console.log('deleteBurdenSet() called for ' + burdenSet.burdenset.name)

        // Go to the server to delete the burden set.
        rpcservice.rpcProjectCall('delete_burden_set',
          [this.$store.state.activeProject.project.id, burdenSet.burdenset.numindex])
        .then(response => {
          // Update the burden sets so the new set shows up on the list.
          this.updateBurdenSets()
        })
      },

      createNewBurdenSet() {
        console.log('createNewBurdenSet() called')

        // Go to the server to create the new burden set.
        rpcservice.rpcProjectCall('create_burden_set',
          [this.$store.state.activeProject.project.id, 'New burden set'])
        .then(response => {
          // Update the burden sets so the new set shows up on the list.
          this.updateBurdenSets()
        })
      },

      makeGraph(burdenSet) {
        console.log('makeGraph() called for ' + burdenSet.burdenset.name)

        // Set the active project to the matched project.
        this.activeBurdenSet = burdenSet

        // Go to the server to get the diseases from the burden set.
        rpcservice.rpcProjectCall('get_project_burden_plots',
          [this.$store.state.activeProject.project.id, this.activeBurdenSet.burdenset.numindex])
        .then(response => {
          // Pull out the response data.
          this.serverresponse = response.data

          // Draw the figure in the 'fig01' div tag.
          console.log('About to replace');
          document.getElementById("fig01").innerHTML = response.data.graph1.div;
          console.log('About to eval');
          console.log(response.data.graph1.script);
          eval(response.data.graph1.script);

//          mpld3.draw_figure('fig01', response.data.graph1)
//          mpld3.draw_figure('fig02', response.data.graph2)
//          mpld3.draw_figure('fig03', response.data.graph3)

          console.log('TEMP complete')
          document.getElementById("fig02").innerHTML = response.data.graph2.div;
          eval(response.data.graph2.script);
        })
        .catch(error => {
          // Pull out the error message.
          this.serverresponse = 'There was an error: ' + error.message

          // Set the server error.
          this.servererror = error.message
        })
      },

      updateSorting2(sortColumn) {
        console.log('updateSorting2() called')

        // If the active sorting column is clicked...
        if (this.sortColumn2 === sortColumn) {
            // Reverse the sort.
            this.sortReverse2 = !this.sortReverse2
        }
        // Otherwise.
        else {
          // Select the new column for sorting.
          this.sortColumn2 = sortColumn

          // Set the sorting for non-reverse.
          this.sortReverse2 = false
        }
      },

      applySorting2(diseases) {
        return diseases.sort((disease1, disease2) =>
          {
            let sortDir = this.sortReverse2 ? -1: 1
            if (this.sortColumn2 === 'name') {
              return (disease1[1] > disease2[1] ? sortDir: -sortDir)
            }
            else if (this.sortColumn2 === 'DALYs') {
              return disease1[2] > disease2[2] ? sortDir: -sortDir
            }
            else if (this.sortColumn2 === 'deaths') {
              return disease1[3] > disease2[3] ? sortDir: -sortDir
            }
            else if (this.sortColumn2 === 'prevalence') {
              return disease1[4] > disease2[4] ? sortDir: -sortDir
            }
          }
        )
      }

    }
  }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss" scoped>
  .UIPlaceholder {
    width: 100%;
  }

  .PHText {
    color: green;
    text-align: center;
  }

  .ThreePanels {
    display: flex;
    width: 100%;
  }

  .LeftPanel {
    height: 100%;
    width: 33%;
    text-align: center;
  }

  .MidPanel {
    height: 100%;
    width: 34%;
    text-align: center;
  }

  .RightPanel {
    height: 100%;
    width: 33%;
    text-align: center;
  }

  #test-hot {
    width: 600px;
    height: 400px;
    overflow: hidden;
  }
</style>
