<!--
Manage projects page

Last update: 2019feb18
-->

<template>
  <div class="SitePage">
    <div class="card">
      <help reflink="create-projects" :label='$t("projects.Create project")'></help>

      <div class="ControlsRow">
        <button class="btn __blue" @click="addDemoProject">{{ $t("projects.Add demo project") }}</button>
        &nbsp; &nbsp;
        <button class="btn __blue" @click="createNewProjectModal">{{ $t("projects.Create new project") }}</button>
        &nbsp; &nbsp;
        <button class="btn __blue" @click="uploadProjectFromFile">{{ $t("projects.Upload project from file") }}</button>
        &nbsp; &nbsp;
        <button class="btn __blue" @click="addCountryProject" :data-tooltip="$t('Last extracted 1 Feb 2022')">{{ $t("Add country project from LiST database") }}</button>
        &nbsp; &nbsp;
      </div>
    </div>

    <div class="PageSection" v-if="projectSummaries.length > 0">
      <div class="card">
        <help reflink="manage-projects" :label='$t("projects.Manage projects")'></help>

        <input type="text"
               class="txbox"
               style="margin-bottom: 20px"
               :placeholder="filterPlaceholder"
               v-model="filterText"/>

        <table class="table table-bordered table-hover table-striped" style="width: 100%">
          <thead>
          <tr>
            <th style="text-align:center">
              <input type="checkbox" @click="selectAll()" v-model="allSelected"/>
            </th>
            <th @click="updateSorting('name')" class="sortable">
              {{ $t("Name") }}
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
            <th style="text-align:left">{{ $t("projects.Project actions") }}</th>
            <th @click="updateSorting('updatedTime')" class="sortable" style="text-align:left">
              {{ $t("projects.Last modified") }}
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
            <th>{{ $t("projects.Language") }}</th>
            <th>{{ $t("Databook") }}</th> <!-- ATOMICA-NUTRITION DIFFERENCE -->
          </tr>
          </thead>
          <tbody>
          <tr v-for="projectSummary in sortedFilteredProjectSummaries"
              :class="{ highlighted: projectSummary.project.id === projectID }">
            <td>
              <input type="checkbox" @click="uncheckSelectAll()" v-model="projectSummary.selected"/>
            </td>
            <td v-if="projectSummary.renaming !== ''">
              <input type="text"
                     class="txbox renamebox"
                     @keyup.enter="renameProject(projectSummary)"
                     v-model="projectSummary.renaming"/>
            </td>
            <td v-else>
              <div v-if="projectSummary.project.id === projectID">
                <b>{{ projectSummary.project.name }}</b>
              </div>
              <div v-else>
                {{ projectSummary.project.name }}
              </div>
            </td>
            <td style="text-align:left">
              <span v-if="sortedFilteredProjectSummaries.length>1">
                <button class="btn __green"  @click="openProject(projectSummary.project.id)" :disabled="projectSummary.project.id === projectID" ><span>{{ $t("Open") }}</span></button>
              </span>
              <button class="btn btn-icon" @click="renameProject(projectSummary)"                  :data-tooltip="$t('Rename')">  <i class="ti-pencil"></i></button>
              <button class="btn btn-icon" @click="copyProject(projectSummary.project.id)"         :data-tooltip="$t('Copy')">    <i class="ti-files"></i></button>
              <button class="btn btn-icon" @click="downloadProjectFile(projectSummary.project.id)" :data-tooltip="$t('Download')"><i class="ti-download"></i></button>
            </td>
            <td style="text-align:left">
              {{ projectSummary.project.updatedTimeString ? projectSummary.project.updatedTimeString : 'No modification' }}
            </td>
            <td style="text-align:left">{{ projectSummary.project.localeName }}</td>
            <td style="white-space: nowrap; text-align:left"> <!-- ATOMICA-NUTRITION DIFFERENCE -->
              <button class="btn __blue" @click="renameDatasetModal(projectSummary.project.id, projectSummary.selectedDataSet)" :data-tooltip='$t("projects.Rename databook")'><i class="ti-pencil"></i></button>
              <button class="btn __blue" @click="copyDataset(projectSummary.project.id, projectSummary.selectedDataSet)" :data-tooltip='$t("projects.Copy databook")'><i class="ti-files"></i></button>
              <button class="btn __blue" @click="deleteDataset(projectSummary.project.id, projectSummary.selectedDataSet)" :data-tooltip='$t("projects.Delete databook")'><i class="ti-trash"></i></button>
              <button class="btn __blue" @click="downloadDatabook(projectSummary.project.id, projectSummary.selectedDataSet)" :data-tooltip='$t("projects.Download databook")'><i class="ti-download"></i></button>
              <button class="btn __blue" @click="uploadDatabook(projectSummary.project.id)" :data-tooltip='$t("projects.Upload databook")'><i class="ti-upload"></i></button>
              <select v-if="projectSummary.project.dataSets.length>0" v-model="projectSummary.selectedDataSet">
                <option v-for='dataset in projectSummary.project.dataSets'>
                  {{ dataset }}
                </option>
              </select>&nbsp;
            </td>
          </tr>
          </tbody>
        </table>

        <div class="ControlsRow">
          <button :disabled="!anySelected" class="btn __red" @click="deleteModal()">{{ $t("Delete selected") }}</button>
          &nbsp; &nbsp;
          <button :disabled="!anySelected" class="btn" @click="downloadSelectedProjects">{{ $t("Download selected") }}</button>
        </div>
      </div>
    </div>

    <modal name="create-project"
           height="auto"
           :classes="['v--modal', 'vue-dialog']"
           :width="400"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="false"
    >

      <div class="dialog-content">
        <div class="dialog-c-title">
          {{ $t("projects.Create blank project") }}
        </div>
        <div class="dialog-c-text">
          {{ $t("projects.Project name") }}:<br>
          <input type="text"
                 class="txbox"
                 v-model="proj_name"/><br>
        </div>  <!-- ATOMICA-NUTRITION DIFFERENCE -->
        <div style="text-align:justify">
          <button @click="createNewProject()" class='btn __green' style="display:inline-block">
            {{ $t("Create") }}
          </button>

          <button @click="$modal.hide('create-project')" class='btn __red' style="display:inline-block">
            {{ $t("Cancel") }}
          </button>
        </div>
      </div>
    </modal>  <!-- ATOMICA-NUTRITION DIFFERENCE -->
    
    <!-- ### Start: rename dataset modal ### -->
    <modal name="rename-dataset"
           height="auto"
           :classes="['v--modal', 'vue-dialog']"
           :width="400"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="false"
    >

      <div class="dialog-content">
        <div class="dialog-c-title">
          {{ $t("projects.Rename databook") }}
        </div>
        <div class="dialog-c-text">
          {{ $t("projects.New name") }}:<br>
          <input type="text"
                 class="txbox"
                 v-model="modalRenameDataset"/><br>
        </div>
        <div style="text-align:justify">
          <button @click="renameDataset()" class='btn __green' style="display:inline-block">
            {{ $t("Rename") }}
          </button>

          <button @click="$modal.hide('rename-dataset')" class='btn __red' style="display:inline-block">
            {{ $t("Cancel") }}
          </button>
        </div>
      </div>

    </modal>
    <!-- ### End: rename dataset modal ### -->

    <!-- ### Start: create country project modal ### -->
    <modal name="country-proj"
           height="auto"
           :classes="['v--modal', 'vue-dialog']"
           :width="400"
           :pivot-y="0.3"
           :adaptive="true"
           :clickToClose="false"
    >

      <div class="dialog-content">
        <div class="dialog-c-title">
          {{ $t("Select country") }}
        </div>
        <div class="dialog-c-text">
          {{ $t("Warning: databooks contain unvalidated fields and require review before results are used.") }}
        </div>
        <br />
        <span style="white-space: pre;"></span>
        <tr>
          <th><select v-model="country_name">
            <option v-for='country_name in countryList'>
              {{ country_name }}
            </option>
          </select><br><br></th>
        </tr>
        <div style="text-align:justify">
          <button @click="loadCountryProj(country_name) | $modal.hide('country-proj')" class='btn __green' style="display:inline-block">
            {{ $t("Load") }}
          </button>

          <button @click="$modal.hide('country-proj')" class='btn __red' style="display:inline-block">
            {{ $t("Cancel") }}
          </button>
        </div>
      </div>

    </modal>
    <!-- ### End: input uncertainty runs modal ### -->
  </div>

</template>

<script>
  import utils from '../js/utils'
  import router from '../router'
  import i18n from '../i18n'

  export default {
    name: 'ProjectsPage',

    data() {
      return {
        filterText: '',  // Text in the table filter box
        allSelected: false, // Are all of the projects selected?
        projectToRename: null, // What project is being renamed?
        sortColumn: 'updatedTime',  // Column of table used for sorting the projects: name, country, creationTime, updatedTime, dataUploadTime
        sortReverse: true, // Sort in reverse order?
        projectSummaries: [], // List of summary objects for projects the user has
        modalRenameProjUID: null,  // Project ID with data being renamed in the modal dialog
        modalRenameDataset: null,  // Dataset being renamed in the rename modal dialog
        countryList: [], // List of country databooks from LiST database
        country_name: '',
      }
    },

    computed: {
      filterPlaceholder() { return i18n.t('projects.Type here to filter projects') },
      proj_name() { return i18n.t('projects.New project') },
      projectID()    { return this.$store.getters.activeProjectID },
      anySelected() { return this.projectSummaries.some(x => x.selected) },
      sortedFilteredProjectSummaries() {
        return this.applyNameFilter(this.applySorting(this.projectSummaries))
      },
    },

    created() {
      if (this.$store.state.activeProject) { // Get the active project ID if there is an active project.
        this.updateProjectSummaries(this.$store.state.activeProject.project.id) // Load the project summaries of the current user.
      } else {
        this.updateProjectSummaries()
      }
      this.pullCountryList()
    },

    methods: {

      getLocaleName(locale) {
        for (var i = 0; i < utils.locales.length; i++) {
          if (utils.locales[i].locale === locale) {
            return utils.locales[i].name;
          }
        }
        return locale;
      },

      beforeOpen (event) {
        console.log(event)
        this.TEMPtime = Date.now() // Set the opening time of the modal
      },

      beforeClose (event) {
        console.log(event)
        // If modal was open less then 5000 ms - prevent closing it
        if (this.TEMPtime + this.TEMPduration < Date.now()) {
          event.stop()
        }
      },

      async updateProjectSummaries(setActiveID) {
        console.log('updateProjectSummaries() called')
        this.$sciris.start(this)
        try {
          let response = await this.$sciris.rpc('jsonify_projects', [this.$store.state.currentUser.username]) // Get the current user's project summaries from the server.

          this.projectToRename = null  // Unset the link to a project being renamed.
          let options = { year: 'numeric', month: 'short', day: 'numeric' , hour:'numeric',minute:'numeric',second:'numeric', timeZoneName:'short'};
          response.data.projects.forEach(theProj => {
            theProj.selected = false // Set to not selected.
            theProj.renaming = '' // Set to not being renamed.
            theProj.selectedDataSet = theProj.project.dataSets[0] // Set the first dataset.
            theProj.project.localeName = this.getLocaleName(theProj.project.locale);

            // Convert times to JS objects
            theProj.project.creationTime = new Date(theProj.project.creationTime);
            theProj.project.updatedTime = new Date(theProj.project.updatedTime);

            // Localize the last modified time string
            theProj.project.updatedTimeString = theProj.project.updatedTime.toLocaleString(undefined, options);
          })

          this.projectSummaries = response.data.projects
          this.$sciris.succeed(this, '')  // No green popup.
        } catch (error) {
          this.$sciris.fail(this, 'Could not load projects', error);
        }

        if (this.projectSummaries.length === 0) {
          this.$store.commit('newActiveProject', undefined);
          return;
        }

        // Try to open the requested project (noting that it may not exist if the project has been deleted in the meantime)
        if (setActiveID !== null) {
          let matchProject = this.projectSummaries.find(theProj => theProj.project.id === setActiveID);
          if (matchProject !== undefined) {
            this.openProject(matchProject.project.id);
            return;
          }
        }

        // Otherwise, open the most recent project (by modification time)
        let latest = Math.max(...Array.from(this.projectSummaries, x => x.project.updatedTime.getTime()));
        let matchProject = this.projectSummaries.find(x => x.project.updatedTime.getTime() === latest);
        this.openProject(matchProject.project.id);

      },

      addDemoProject() {
        console.log('addDemoProject() called');
        this.$sciris.start(this);
        this.$sciris.rpc('add_demo_project', [this.$store.state.currentUser.username, i18n.locale]) // Have the server create a new project.
          .then(response => {
            this.updateProjectSummaries(response.data.projectID); // Update the project summaries so the new project shows up on the list.
            this.$sciris.succeed(this, '')
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not add demo project', error)
          })
      },

      // Open a model dialog for creating a new project
      createNewProjectModal() {
        console.log('createNewProjectModal() called');
        this.$modal.show('create-project');
      },


      createNewProject() {
        console.log('createNewProject() called');
        this.$modal.hide('create-project');
        this.$sciris.start(this) // Start indicating progress.
        var username = this.$store.state.currentUser.username
        this.$sciris.download('create_new_project', [username, this.proj_name, i18n.locale]) // Have the server create a new project.
          .then(response => {
            this.updateProjectSummaries(null); // Update the project summaries so the new project shows up on the list.
            this.$sciris.succeed(this, 'New project "' + this.proj_name + '" created') // Indicate success.
          })
          .catch(error => {
            this.$sciris.fail(this, i18n.t('projects.Could not add new project'), error)    // Indicate failure.
          })
      },

      uploadProjectFromFile() {
        console.log('uploadProjectFromFile() called')
        this.$sciris.upload('upload_project', [this.$store.state.currentUser.username], {}, '.prj') // Have the server upload the project.
          .then(response => {
            this.$sciris.start(this)  // This line needs to be here to avoid the spinner being up during the user modal.
            this.updateProjectSummaries(response.data.projectID) // Update the project summaries so the new project shows up on the list.
            this.$sciris.succeed(this, i18n.t('projects.New project uploaded'))
          })
          .catch(error => {
            this.$sciris.fail(this, i18n.t('Could not upload file'), error)
          })
      },

      selectAll() {
        console.log('selectAll() called')

        // For each of the projects, set the selection of the project to the
        // _opposite_ of the state of the all-select checkbox's state.
        // NOTE: This function depends on it getting called before the
        // v-model state is updated.  If there are some cases of Vue
        // implementation where these happen in the opposite order, then
        // this will not give the desired result.
        this.projectSummaries.forEach(theProject => theProject.selected = !this.allSelected)
      },

      uncheckSelectAll() {
        this.allSelected = false
      },

      updateSorting(sortColumn) {
        console.log('updateSorting() called')
        if (this.sortColumn === sortColumn) { // If the active sorting column is clicked...
          // Reverse the sort.
          this.sortReverse = !this.sortReverse
        } else { // Otherwise.
          this.sortColumn = sortColumn // Select the new column for sorting.
          this.sortReverse = false // Set the sorting for non-reverse.
        }
      },

      applyNameFilter(projects) {
        return projects.filter(theProject => theProject.project.name.toLowerCase().indexOf(this.filterText.toLowerCase()) !== -1)
      },

      applySorting(projects) {
        return projects.slice(0).sort((proj1, proj2) =>
          {
            let sortDir = this.sortReverse ? -1: 1
            if (this.sortColumn === 'name') {
              return (proj1.project.name.toLowerCase() > proj2.project.name.toLowerCase() ? sortDir: -sortDir)
            } else if (this.sortColumn === 'creationTime') {
              return proj1.project.creationTime > proj2.project.creationTime ? sortDir: -sortDir
            } else if (this.sortColumn === 'updatedTime') {
              return proj1.project.updatedTime > proj2.project.updatedTime ? sortDir: -sortDir
            }
          }
        )
      },

      openProject(uid) {
        // Find the project that matches the UID passed in.
        let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid)
        console.log('openProject() called for ' + matchProject.project.name)
        this.$store.commit('newActiveProject', matchProject) // Set the active project to the matched project.
        // this.$sciris.succeed(this, i18n.t('projects.loaded_popup', {name:matchProject.project.name})) // Success popup.
      },

      copyProject(uid) {
        let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid) // Find the project that matches the UID passed in.
        console.log('copyProject() called for ' + matchProject.project.name)
        this.$sciris.start(this) // Start indicating progress.
        this.$sciris.rpc('copy_project', [uid]) // Have the server copy the project, giving it a new name.
          .then(response => {
            this.updateProjectSummaries(response.data.projectID) // Update the project summaries so the copied program shows up on the list.
            this.$sciris.succeed(this, 'Project "'+matchProject.project.name+'" copied')    // Indicate success.
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not copy project', error) // Indicate failure.
          })
      },

      finishRename(event) {
        // Grab the element of the open textbox for the project name to be renamed.
        let renameboxElem = document.querySelector('.renamebox')
        
        // If the click is outside the textbox, renamed the remembered project.
        if (!renameboxElem.contains(event.target)) {
          this.renameProject(this.projectToRename)
        }
      },
      
      renameProject(projectSummary) {
        console.log('renameProject() called for ' + projectSummary.project.name)
        if (projectSummary.renaming === '') { // If the project is not in a mode to be renamed, make it so.
          projectSummary.renaming = projectSummary.project.name
          // Add a click listener to run the rename when outside the input box is click, and remember
          // which project needs to be renamed.
//          window.addEventListener('click', this.finishRename)
          this.projectToRename = projectSummary
        } else { // Otherwise (it is to be renamed)...
          // Remove the listener for reading the clicks outside the input box, and null out the project 
          // to be renamed.
//          window.removeEventListener('click', this.finishRename)
          this.projectToRename = null          
          let newProjectSummary = _.cloneDeep(projectSummary) // Make a deep copy of the projectSummary object.
          newProjectSummary.project.name = projectSummary.renaming // Rename the project name in the client list from what's in the textbox.
          this.$sciris.start(this)
          this.$sciris.rpc('rename_project', [newProjectSummary]) // Have the server change the name of the project by passing in the new copy of the summary.
            .then(response => {
              this.updateProjectSummaries(newProjectSummary.project.id) // Update the project summaries so the rename shows up on the list.
              projectSummary.renaming = '' // Turn off the renaming mode.
              this.$sciris.succeed(this, '')  // No green popup message.
            })
            .catch(error => {
              this.$sciris.fail(this, 'Could not rename project', error) // Indicate failure.
            })
        }

        // This silly hack is done to make sure that the Vue component gets updated by this function call.
        // Something about resetting the project name informs the Vue component it needs to
        // update, whereas the renaming attribute fails to update it.
        // We should find a better way to do this.
        let theName = projectSummary.project.name
        projectSummary.project.name = 'newname'
        projectSummary.project.name = theName
      },

      downloadProjectFile(uid) {
        let matchProject = this.projectSummaries.find(theProj => theProj.project.id === uid) // Find the project that matches the UID passed in.
        console.log('downloadProjectFile() called for ' + matchProject.project.name)
        this.$sciris.start(this) // Start indicating progress.
        this.$sciris.download('download_project', [uid]) // Make the server call to download the project to a .prj file.
          .then(response => { // Indicate success.
            this.$sciris.succeed(this, '')  // No green popup message.
          })
          .catch(error => { // Indicate failure.
            this.$sciris.fail(this, i18n.t('projects.Could not download project'), error)
          })
      },
      
      renameDatasetModal(uid, selectedDataset) {
        console.log('renameDatasetModal() called');
        this.origDatasetName = selectedDataset // Store this before it gets overwritten
        this.modalRenameProjUID = uid
        this.modalRenameDataset = selectedDataset
        this.$modal.show('rename-dataset');
      },

      renameDataset() {
        console.log('renameDataset() called for ' + this.modalRenameDataset)
        this.$modal.hide('rename-dataset');
        this.$sciris.start(this)
        this.$sciris.rpc('rename_dataset', [this.modalRenameProjUID, this.origDatasetName, this.modalRenameDataset]) // Have the server rename the dataset, giving it a new name.
          .then(response => {
            this.updateProjectSummaries(this.modalRenameProjUID) // Update the project summaries
            this.$sciris.succeed(this, 'Databook "'+this.origDatasetName+'" renamed') // Indicate success.
          })
          .catch(error => {
            this.$sciris.fail(this, i18n.t('projects.Could not rename databook'), error)
          })
      },

      copyDataset(uid, selectedDataset) {
        console.log('copyDataset() called for ' + selectedDataset)
        this.$sciris.start(this)
        this.$sciris.rpc('copy_dataset', [uid, selectedDataset]) // Have the server copy the dataset, giving it a new name.
          .then(response => {
            this.updateProjectSummaries(uid) // Update the project summaries
            this.$sciris.succeed(this, 'Databook "'+selectedDataset+'" copied') // Indicate success.
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not copy databook', error)
          })
      },

      deleteDataset(uid, selectedDataset) {
        console.log('deleteDataset() called for ' + selectedDataset)
        this.$sciris.start(this)
        this.$sciris.rpc('delete_dataset', [uid, selectedDataset]) // Have the server delete the dataset.
          .then(response => {
            this.updateProjectSummaries(uid) // Update the project summaries
            this.$sciris.succeed(this, 'Databook "'+selectedDataset+'" deleted') // Indicate success.
          })
          .catch(error => {
            this.$sciris.fail(this, 'Cannot delete last databook: ensure there are at least 2 databooks before deleting one', error)
          })
      },
      
      downloadDatabook(uid, selectedDataSet) {
        console.log('downloadDatabook() called')
        this.$sciris.start(this, 'Downloading databook...')
        this.$sciris.download('download_databook', [uid], {'key': selectedDataSet})
          .then(response => {
            this.$sciris.succeed(this, '')  // No green popup message.
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not download databook', error)
          })
      },

      uploadDatabook(uid) {
        console.log('uploadDatabook() called')
        this.$sciris.upload('upload_databook', [uid], {}, '.xlsx')
          .then(response => {
            this.$sciris.start(this, 'Uploading databook...')
            this.updateProjectSummaries(uid) // Update the project summaries
            this.$sciris.succeed(this, 'Data uploaded to project') // Indicate success.
          })
          .catch(error => {
            this.$sciris.fail(this, 'Could not upload data', error) // Indicate failure.
          })
      },

      // Confirmation alert
      deleteModal() {
        let selectProjectsUIDs = this.projectSummaries.filter(theProj => // Pull out the names of the projects that are selected.
          theProj.selected).map(theProj => theProj.project.id)
        if (selectProjectsUIDs.length > 0) { // Only if something is selected...
          var obj = { // Alert object data
            message: this.$t('projects.Are you sure you want to delete the selected projects?'),
            useConfirmBtn: true,
            customConfirmBtnClass: 'btn __red',
            customCloseBtnClass: 'btn',
            customConfirmBtnText: this.$t('Delete projects'),
            customCloseBtnText: this.$t('Cancel'),
            onConfirm: this.deleteSelectedProjects
          }
          this.$Simplert.open(obj)
        }
      },

      deleteSelectedProjects() {
        let selectProjectKeys = this.projectSummaries.filter(theProj => // Pull out the names of the projects that are selected.
          theProj.selected).map(theProj => theProj.project.key)
        console.log('deleteSelectedProjects() called for ', selectProjectKeys)
        if (selectProjectKeys.length > 0) { // Have the server delete the selected projects.
          this.$sciris.start(this)
          this.$sciris.rpc('delete_projects', [selectProjectKeys, this.$store.state.currentUser.username])
            .then(response => {
              let activeProjectId = this.$store.state.activeProject.project.id // Get the active project ID.
              if (activeProjectId === undefined) {
                activeProjectId = null
              }
              if (selectProjectKeys.find(theId => theId === activeProjectId)) { // If the active project ID is one of the ones deleted...
                this.$store.commit('newActiveProject', {}) // Set the active project to an empty project.
                activeProjectId = null // Null out the project.
              }
              this.updateProjectSummaries(activeProjectId) // Update the project summaries so the deletions show up on the list. Make sure it tries to set the project that was active (if any).
              this.$sciris.succeed(this, '')  // No green popup message.
            })
            .catch(error => {
              this.$sciris.fail(this, 'Could not delete project(s)', error)
            })
        }
      },

      downloadSelectedProjects() {
        let selectProjectsUIDs = this.projectSummaries.filter(theProj => // Pull out the names of the projects that are selected.
          theProj.selected).map(theProj => theProj.project.id)
        console.log('downloadSelectedProjects() called for ', selectProjectsUIDs)
        if (selectProjectsUIDs.length > 0) { // Have the server download the selected projects.
          this.$sciris.start(this)
          this.$sciris.download('download_projects', [selectProjectsUIDs, this.$store.state.currentUser.username])
            .then(response => {
              // Indicate success.
              this.$sciris.succeed(this, '')  // No green popup message.
            })
            .catch(error => {
              this.$sciris.fail(this, 'Could not download project(s)', error) // Indicate failure.
            })
        }
      },

      pullCountryList() {
        console.log('pullCountryList() called');
        this.$sciris.start(this) // Start indicating progress.
        this.$sciris.rpc('pull_country_list', [i18n.locale]) // Pull the list of countries.
          .then(response => {
            this.countryList = response.data.sort()
            this.country_name = response.data[0]
            this.$sciris.succeed(this, '')  // No green popup message.
          })
          .catch(error => {
            this.$sciris.fail(this, i18n.t('Could not initialize LiST country set'), error)    // Indicate failure.
          })
      },

      addCountryProject() {
        console.log('addCountryProject() called');
        this.$modal.show('country-proj');
      },

      loadCountryProj() {
        console.log('loadCountryProj() called');
        this.$sciris.start(this) // Start indicating progress.
        this.$sciris.rpc('create_country_project', [this.$store.state.currentUser.username, this.country_name, i18n.locale]) // Have the server create a new project.
          .then(response => {
            this.updateProjectSummaries(response.data.projectID); // Update the project summaries so the new project shows up on the list.
            this.$sciris.succeed(this, '') // Indicate success.
          })
          .catch(error => {
            this.$sciris.fail(this, i18n.t('projects.Could not add new project'), error)    // Indicate failure.
          })
      },
    }
  }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss" scoped>
</style>
