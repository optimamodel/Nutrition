<!--
Definition of top navigation bar

Last update: 2018sep23
-->

<template>
  <nav class="navbar navbar-default">
    <div class="container-fluid">
      <div class="navbar-header">
        <div class="logo">
          <a href="http://ocds.co" target="_blank">
            <img src="static/img/optima-logo-nutrition.png" height="50px" vertical-align="middle" alt> <!--  ATOMICA-NUTRITION DIFFERENCE -->
          </a>
        </div>
        <button type="button" class="navbar-toggle" :class="{toggled: $sidebar.showSidebar}" @click="toggleSidebar">
          <span class="sr-only">Toggle navigation</span>
          <span class="icon-bar bar1"></span>
          <span class="icon-bar bar2"></span>
          <span class="icon-bar bar3"></span>
        </button>
      </div>
      <div class="collapse navbar-collapse">
        <!-- If you edit this section, make sure to fix the section in App.vue for the narrow screen -->
        <ul class="nav navbar-nav navbar-main">
          <li class="nav-item">
            <router-link to="/projects">
              <span>Projects</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/inputs"> <!--  ATOMICA-NUTRITION DIFFERENCE -->
              <span>Inputs</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/scenarios">
              <span>Scenarios</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/optimizations">
              <span>Optimizations</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/geospatial">
              <span>Geospatial</span>
            </router-link>
          </li>
        </ul>
        <ul class="nav navbar-nav navbar-right">
          <li class="nav-item">
            <div class="nav-link">
              <i class="ti-view-grid"></i>
              <span>Project: {{ activeProjectName }}</span>
            </div>
          </li>
          <dropdown>
<!--            The template behaves oddly if content is bound to the dropdown properties, so just manually fill out the title slot instead-->
            <template v-slot:title>
              <div class="dropdown-title">
                <i class="ti-user dropdown-icon"></i>
                User: {{ activeUserName }}
                <b class="caret"></b>
              </div>
            </template>
            <li><a href="#/changeinfo"><i class="ti-pencil"></i>&nbsp;&nbsp;Edit account</a></li>
            <li><a href="#/changepassword"><i class="ti-key"></i>&nbsp;&nbsp;Change password</a></li>
            <li><a href="#/help"><i class="ti-help"></i>&nbsp;&nbsp;Help</a></li>
            <li><a href="#/about"><i class="ti-shine"></i>&nbsp;&nbsp;About</a></li>
            <li><a href="#" v-on:click=logOut()><i class="ti-car"></i>&nbsp;&nbsp;Log out</a></li>
          </dropdown>
        </ul>
      </div>
    </div>
  </nav>
</template>


<script>
  import router from '../router.js'

  export default {
    name: 'TopNavbar',

    // Health prior function
    data() {
      return {
        activePage: 'manage projects'
      }
    },

    computed: {


      activeProjectName() {
        if (this.$store.state.activeProject.project === undefined) {
          return 'none'
        } else {
          return this.$store.state.activeProject.project.name
        }
      },

      activeUserName() {
        // Get the active user name -- the display name if defined; else the user name
        var username = this.$store.state.currentUser.username;
        var dispname = this.$store.state.currentUser.displayname;
        var userlabel = '';
        if (dispname === undefined || dispname === '') {
          userlabel = username;
        } else {
          userlabel = dispname;
        }

        return userlabel;
      },

      // Theme function
      routeName() {
        const route_name = this.$route.name
        return this.capitalizeFirstLetter(route_name)
      },
    },

    // Health prior function
    created() {
      this.$sciris.getUserInfo(this.$store)
    },

    // Theme function
    data() {
      return {
        activeNotifications: false
      }
    },
    methods: {
      // Health prior functions
      checkLoggedIn() {
        this.$sciris.checkLoggedIn
      },

      checkAdminLoggedIn() {
        this.$sciris.checkAdminLoggedIn
      },

      logOut() {
        this.$sciris.logOut()
      },

      // Theme functions
      capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1)
      },
      toggleNotificationDropDown() {
        this.activeNotifications = !this.activeNotifications
      },
      closeDropDown() {
        this.activeNotifications = false
      },
      toggleSidebar() {
        this.$sidebar.displaySidebar(!this.$sidebar.showSidebar)
      },
      hideSidebar() {
        this.$sidebar.displaySidebar(false)
      }
    }
  }

</script>

