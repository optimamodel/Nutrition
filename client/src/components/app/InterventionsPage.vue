<!--
Define interventions

Last update: 2018-03-25
-->

<template>
  <div class="SitePage">

    <div v-if="activeProjectName === ''">
      <div style="font-style:italic">
        <p>Hmm, I can't find any interventions...did you forget to <router-link class="link __blue" to="/projects">load a project</router-link>?</p>
      </div>
    </div>

    <div class="PageSection" v-if="activeProjectName !== ''">

      <button class="btn" @click="createNewSet">Create new intervention set</button>

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
              Intervention set
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
          <tr v-for="intervSet in sortedFilteredIntervSets"
              :class="{ highlighted: intervSetIsSelected(intervSet) }">
            <td v-if="intervSet.renaming !== ''">
			        <input type="text"
                     class="txbox"
                     @keyup.enter="renameSet(intervSet)"
                     v-model="intervSet.renaming"/>
			      </td>
			      <td v-else>
			        {{ intervSet.intervset.name }}
			      </td>
            <td>
              <button class="btn __green" @click="viewSet(intervSet)">Open</button>
            </td>
            <td>{{ intervSet.intervset.creationTime }}</td>
            <td>{{ intervSet.intervset.updateTime ? intervSet.intervset.updateTime:
              'No modification' }}</td>
            <td style="white-space: nowrap">
              <button class="btn" @click="copySet(intervSet)">Copy</button>
              <button class="btn" @click="renameSet(intervSet)">Rename</button>
              <button class="btn __red" @click="deleteSet(intervSet)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>


    <div class="PageSection UIPlaceholder" v-if="activeIntervSet.intervset != undefined">

        <table class="table table-bordered table-hover table-striped" style="width: auto; margin-top: 10px;">
          <thead>
            <tr>
              <th>Active</th>
              <th style="min-width:30%">Intervention&nbsp;name</th>
              <th style="min-width:20%">Delivery&nbsp;platform</th>
              <th>Type</th>
              <th>ICER</th>
              <th>Unit&nbsp;cost</th>
              <th>Equity</th>
              <th>FRP</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="interv in interventionList">
              <td style="text-align: center">
                <input type="checkbox" v-model="interv.active"/>
              </td>
              <td>
                <input type="text"
                       class="txbox"
                       @keyup.enter="notImplemented('Edit name')"
                       v-model="interv.name"/>
              </td>
              <td>
                <input type="text"
                       class="txbox"
                       @keyup.enter="notImplemented('Edit platform')"
                       v-model="interv.platform"/>
              </td>
              <td>
                <input type="text"
                       class="txbox"
                       @keyup.enter="notImplemented('Edit type')"
                       v-model="interv.type"/>
              </td>
              <td>
                <input type="text"
                       class="txbox"
                       @keyup.enter="notImplemented('Edit ICER')"
                       v-model="interv.icer"/>
              </td>
              <td>
                <input type="text"
                       class="txbox"
                       @keyup.enter="notImplemented('Edit unit cost')"
                       v-model="interv.unitcost"/>
              </td>
              <td>
                <input type="text"
                       class="txbox"
                       @keyup.enter="notImplemented('Edit equity')"
                       v-model="interv.equity"/>
              </td>
              <td>
                <input type="text"
                       class="txbox"
                       @keyup.enter="notImplemented('Edit financial risk protection')"
                       v-model="interv.frp"/>
              </td>
              <td style="white-space: nowrap">
                <button class="iconbtn" @click="notImplemented('Rename')"><i class="ti-pencil"></i></button>
                <button class="iconbtn" @click="notImplemented('Copy')"><i class="ti-layers"></i></button>
                <button class="iconbtn" @click="notImplemented('Delete')"><i class="ti-trash"></i></button>
              </td>
            </tr>
          </tbody>
        </table>
      <button class="btn" @click="notImplemented('Add new intervention')">Add new intervention</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
var filesaver = require('file-saver')
import rpcservice from '@/services/rpc-service'
import router from '@/router'

export default {
  name: 'InterventionsPage',

  data() {
    return {
      filterPlaceholder: 'Type here to filter intervention sets', // Placeholder text for table filter box
      filterText: '', // Text in the table filter box
      sortColumn: 'updatedTime',  // Column of table used for sorting the intervention sets -- name, creationTime, updatedTime
      sortReverse: false, // Sort in reverse order?
      interventionSets: [], // List of objects for intervention sets the project has
      activeIntervSet: {}, // Active intervention set
      showAllIntervs: true, // Show all of the intervention categories
      showCancerIntervs: false, // Show cancer interventions
      showInfectiousIntervs: false, // Show infectious diseases interventions
      showChildIntervs: false, // Show child care interventions
      interventionList: [],

      // CK: WARNING TEMP, should come from backend
      country: 'Afghanistan',
      countryList: [
        'Afghanistan',
        'Other',
      ]
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

    sortedFilteredIntervSets() {
      return this.applyNameFilter(this.applySorting(this.interventionSets))
    },

    filteredInterventions() {
      if (this.showAllIntervs) {
        return this.interventionList
      } else {
        return this.interventionList.filter(interv =>
          {
            if (interv.intervCategory === 'cancer')
              return this.showCancerIntervs
            else if (interv.intervCategory === 'infectious')
              return this.showInfectiousIntervs
            else if (interv.intervCategory === 'childcare')
              return this.showChildIntervs
            else
              return false
          }
        )
      }
    }
  },

  created() {
    // If we have no user logged in, automatically redirect to the login page.
    if (this.$store.state.currentUser.displayname == undefined) {
      router.push('/login')
    }

    // Otherwise...
    else {
      // Load the intervention sets from the active project, telling the function
      // to also set the active intervention set to the last item.
      this.updateIntervSets(true)
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

    updateIntervSets(setLastEntryActive=false) {
      console.log('updateIntervSets() called')

      // If there is no active project, clear the interventionSets list.
      if (this.$store.state.activeProject.project === undefined) {
        this.interventionSets = []
      }

      // Otherwise...
      else {
        // Get the active project's intervention sets.
        rpcservice.rpcProjectCall('get_project_interv_sets',
          [this.$store.state.activeProject.project.id])
        .then(response => {
          // Set the intervention set list to what we received.
          this.interventionSets = response.data.intervsets

          // Add numindex elements to the intervention sets to keep track of
		      // which index to pull from the server.
          for (let ind=0; ind < this.interventionSets.length; ind++)
            this.interventionSets[ind].intervset.numindex = ind

          // Set renaming values to blank initially.
          this.interventionSets.forEach(theSet => {
		        theSet.renaming = ''
		      })

          // If we want to set the last entry active and we have any
          // entries, do the setting.
          if ((setLastEntryActive) && (this.interventionSets.length > 0))
            this.viewSet(this.interventionSets[this.interventionSets.length - 1])
        })
      }
    },

    intervSetIsSelected(intervSet) {
      // If the active intervention set is undefined, it is not active.
      if (this.activeIntervSet.intervset === undefined) {
        return false
      }

      // Otherwise, the intervention is selected if the numindexes match.
      else {
        return (this.activeIntervSet.intervset.numindex === intervSet.intervset.numindex)
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
      return sets.filter(theSet => theSet.intervset.name.toLowerCase().indexOf(this.filterText.toLowerCase()) !== -1)
    },

    applySorting(sets) {
      return sets.sort((set1, set2) =>
        {
          let sortDir = this.sortReverse ? -1: 1
          if (this.sortColumn === 'name') {
            return (set1.intervset.name > set2.intervset.name ? sortDir: -sortDir)
          }
          else if (this.sortColumn === 'creationTime') {
            return set1.intervset.creationTime > set2.intervset.creationTime ? sortDir: -sortDir
          }
          else if (this.sortColumn === 'updatedTime') {
            return set1.intervset.updateTime > set2.intervset.updateTime ? sortDir: -sortDir
          }
        }
      )
    },

    viewSet(intervSet) {
      console.log('viewSet() called for ' + intervSet.intervset.name)

      // Set the active intervention set to the matched intervention set.
      this.activeIntervSet = intervSet

      // Go to the server to get the interventions from the intervention set.
      rpcservice.rpcProjectCall('get_project_interv_set_intervs',
        [this.$store.state.activeProject.project.id, this.activeIntervSet.intervset.numindex])
      .then(response => {
        // Set the interventions table list.
        this.interventionList = response.data.interventions

        // Set the active values from the loaded in data.
        this.interventionList.forEach(theInterv => {
		      theInterv.active = theInterv[0];
          theInterv.name = theInterv[1];
          theInterv.platform = theInterv[3];
          theInterv.type = theInterv[4];
          theInterv.icer = Number(theInterv[5]).toLocaleString();
          theInterv.unitcost = Number(theInterv[6]).toLocaleString();
          theInterv.equity = theInterv[7];
          theInterv.frp = theInterv[8];
		    })

      })

      this.$notifications.notify({
        message: 'Intervention set "' + intervSet.intervset.name + '" now active',
        icon: 'ti-check',
        type: 'success',
        verticalAlign: 'top',
        horizontalAlign: 'center',
      });
    },

    copySet(intervSet) {
      console.log('copySet() called for ' + intervSet.intervset.name)

	    // Have the server copy the intervention set, giving it a new name.
      rpcservice.rpcProjectCall('copy_interv_set',
        [this.$store.state.activeProject.project.id, intervSet.intervset.numindex])
      .then(response => {
        // Update the intervention sets so the new set shows up on the list.
        this.updateIntervSets()
      })
    },

    renameSet(intervSet) {
      console.log('renameSet() called for ' + intervSet.intervset.name)

	    // If the intervention set is not in a mode to be renamed, make it so.
	    if (intervSet.renaming === '') {
		    intervSet.renaming = intervSet.intervset.name
      }

	    // Otherwise (it is to be renamed)...
	    else {
        // Have the server change the name of the intervention set.
        rpcservice.rpcProjectCall('rename_interv_set',
          [this.$store.state.activeProject.project.id,
          intervSet.intervset.numindex, intervSet.renaming])
        .then(response => {
          // Update the intervention sets so the renamed one shows up on the list.
          this.updateIntervSets()

	        // Turn off the renaming mode.
	        intervSet.renaming = ''
        })
      }

	    // This silly hack is done to make sure that the Vue component gets updated by this function call.
	    // Something about resetting the intervention set name informs the Vue component it needs to
	    // update, whereas the renaming attribute fails to update it.
	    // We should find a better way to do this.
      let theName = intervSet.intervset.name
      intervSet.intervset.name = 'newname'
      intervSet.intervset.name = theName
    },

    deleteSet(intervSet) {
      console.log('deleteSet() called for ' + intervSet.intervset.name)

      // Go to the server to delete the intervention set.
      rpcservice.rpcProjectCall('delete_interv_set',
        [this.$store.state.activeProject.project.id, intervSet.intervset.numindex])
      .then(response => {
        // Update the intervention sets so the new set shows up on the list.
        this.updateIntervSets()
      })
    },

    createNewSet() {
      console.log('createNewSet() called')

      // Go to the server to create the new intervention set.
      rpcservice.rpcProjectCall('create_interv_set',
        [this.$store.state.activeProject.project.id, 'New intervention set'])
      .then(response => {
        // Update the intervention sets so the new set shows up on the list.
        this.updateIntervSets()
      })
    },

    intervAllCategoryClick() {
      this.showCancerIntervs = false
      this.showInfectiousIntervs = false
      this.showChildIntervs = false
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss" scoped>
  .UIPlaceholder {
//    height: 500px;
    width: 100%;
//    border: 1px solid black;
  }

  .PHText {
    color: green;
    text-align: center;
  }

  #checkboxtable td {
    padding: 0px 5px;
  }
</style>
