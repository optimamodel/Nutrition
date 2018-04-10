<!--
Define health packages

Last update: 2018-03-25
-->

<template>
  <div class="SitePage">

    <div style="font-style:italic">
      <p>This module is currently under development.</p>
    </div>

    <div class="PageSection">
      <input type="text"
             class="txbox"
             style="margin-bottom: 20px"
             :placeholder="filterPlaceholder"
             v-model="filterText"/>

      <table class="table table-bordered table-hover table-striped" style="width: auto">
        <thead>
          <tr>
            <th>
              <input type="checkbox" @click="selectAll()" v-model="allSelected"/>
            </th>
            <th @click="updateSorting('name')" class="sortable">
              Benefits package
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
            <th>Country</th>
            <th>Burden project</th>
            <th>Potential intervention set</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="healthPackage in sortedFilteredHealthPackages" :class="{ highlighted: activePackage.uid === healthPackage.uid }">
            <td>
              <input type="checkbox" @click="uncheckSelectAll()" v-model="healthPackage.selected"/>
            </td>
            <td>{{ healthPackage.packageName }}</td>
            <td>{{ healthPackage.country }}</td>
            <td>
              <select v-model="healthPackage.burdenProject">
                <option v-for="choice in burdenProjects">
                  {{ choice }}
                </option>
              </select>
            </td>
            <td>
              <select v-model="healthPackage.intervSet">
                <option v-for="choice in intervSets">
                  {{ choice }}
                </option>
              </select>
            </td>
            <td style="white-space: nowrap">
              <button class="btn __green" @click="viewPackage(healthPackage.uid)">View</button>
              <button class="btn" @click="copyPackage(healthPackage.uid)">Copy</button>
              <button class="btn" @click="renamePackage(healthPackage.uid)">Rename</button>
              <button class="btn __red" @click="deletePackage(healthPackage.uid)">Delete</button>
            </td>
          </tr>
          <tr>
            <td></td>
            <td>
              <button class="btn" @click="createNewPackage">Create new</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="PageSection UIPlaceholder" v-if="activePackage.packageName != undefined">
      <div class="PHText">
        Page interface specific to {{ activePackage.packageName }} health package
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
var filesaver = require('file-saver')
import rpcservice from '@/services/rpc-service'
import router from '@/router'

export default {
  name: 'HealthPackagesPage',

  data() {
    return {
      // Placeholder text for table filter box
      filterPlaceholder: '\u{1f50e} Filter Health Packages',

      // Text in the table filter box
      filterText: '',

      // Are all of the health packages selected?
      allSelected: false,

      // Column of table used for sorting the health packages
      sortColumn: 'name',  // name

      // Sort in reverse order?
      sortReverse: false,

      // List of objects for health packages the active project has
      healthPackages:
        [
          {
            packageName: 'Package 1',
            country: 'Afghanistan',
            burdenProject: 'Default GBD',
            intervSet: 'Default LMIC from DCP',
            uid: 1,
            selected: false
          },
          {
            packageName: 'Final package',
            country: 'Afghanistan',
            burdenProject: 'GBD with updated NCDs',
            intervSet: 'Default LMIC from DCP',
            uid: 2,
            selected: false
          }
        ],

      // Active health package
      activePackage: {},

      burdenProjects: ['Default GBD', 'GBD with updated NCDs'],

      intervSets: ['Default LMIC from DCP', 'Country defined set']
    }
  },

  computed: {
    activeProjectName() {
      if (this.$store.state.activeProject.project === undefined) {
        return '[nothing]'
      } else {
        return this.$store.state.activeProject.project.name
      }
    },

    sortedFilteredHealthPackages() {
      return this.applyNameFilter(this.applySorting(this.healthPackages))
    }
  },

  created() {
    // If we have no user logged in, automatically redirect to the login page.
    if (this.$store.state.currentUser.displayname == undefined) {
      router.push('/login')
    }
  },

  methods: {
    selectAll() {
      console.log('selectAll() called')

      // For each of the packages, set the selection of the package to the
      // _opposite_ of the state of the all-select checkbox's state.
      // NOTE: This function depends on it getting called before the
      // v-model state is updated.  If there are some cases of Vue
      // implementation where these happen in the opposite order, then
      // this will not give the desired result.
      this.healthPackages.forEach(thePackage => thePackage.selected = !this.allSelected)
    },

    uncheckSelectAll() {
      this.allSelected = false
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

    applyNameFilter(packages) {
      console.log('applyNameFilter() called')

      return packages.filter(thePackage => thePackage.packageName.toLowerCase().indexOf(this.filterText.toLowerCase()) !== -1)
    },

    applySorting(packages) {
      console.log('applySorting() called')

      return packages.sort((package1, package2) =>
        {
          let sortDir = this.sortReverse ? -1: 1
          if (this.sortColumn === 'name') {
            return (package1.packageName > package2.packageName ? sortDir: -sortDir)
          }
        }
      )
    },

    viewPackage(uid) {
      // Find the package that matches the UID passed in.
      let matchPackage = this.healthPackages.find(thePackage => thePackage.uid === uid)

      console.log('viewPackage() called for ' + matchPackage.packageName)

      // Set the active package to the matched package.
      this.activePackage = matchPackage
    },

    copyPackage(uid) {
      // Find the package that matches the UID passed in.
      let matchPackage = this.healthPackages.find(thePackage => thePackage.uid === uid)

      console.log('copyPackage() called for ' + matchPackage.packageName)
    },

    renamePackage(uid) {
      // Find the package that matches the UID passed in.
      let matchPackage = this.healthPackages.find(thePackage => thePackage.uid === uid)

      console.log('renamePackage() called for ' + matchPackage.packageName)
    },

    deletePackage(uid) {
      // Find the package that matches the UID passed in.
      let matchPackage = this.healthPackages.find(thePackage => thePackage.uid === uid)

      console.log('deletePackage() called for ' + matchPackage.packageName)
    },

    createNewPackage() {
      console.log('createNewPackage() called')
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss" scoped>
  .UIPlaceholder {
    height: 500px;
    width: 100%;
    border: 1px solid black;
  }

  .PHText {
    color: green;
    text-align: center;
  }
</style>
