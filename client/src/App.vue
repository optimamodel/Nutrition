<!--
App.vue -- App component, the main page

Last update: 7/28/18 (gchadder3)
-->

<template>
  <div :class="{'nav-open': $sidebar.showSidebar}">
    <simplert></simplert>
    <router-view></router-view>
    <vue-progress-bar></vue-progress-bar>    
    <!--This sidebar appears only for screens smaller than 992px -- otherwise, it is rendered in TopNavbar.vue-->
    <side-bar type="navbar" :sidebar-links="$sidebar.sidebarLinks">
      <ul class="nav navbar-nav">
        <!-- Below requires a userService -->
        <li>
          <a href="#" class="btn-rotate">
            <i class="ti-view-grid"></i>
            <p>
              Project: <span>{{ activeProjectName }}</span>
            </p>
          </a>
        </li>
        <drop-down v-bind:title="activeUserName" icon="ti-user">
          <li><a href="#/changeinfo"><i class="ti-pencil"></i>&nbsp;Edit account</a></li>
          <li><a href="#/changepassword"><i class="ti-key"></i>&nbsp;Change password</a></li>
          <li><a href="#" v-on:click=logOut()><i class="ti-car"></i>&nbsp;Log out</a></li>
        </drop-down>
        <li class="divider"></li>
      </ul>
    </side-bar>
  </div>

</template>

<script>
import userService from '@/services/user-service'

export default {
  computed: {
    // Health prior function
    currentUser: () => {
      return userService.currentUser()
    },

    activeProjectName() {
      if (this.$store.state.activeProject.project === undefined) {
        return 'none'
      } else {
        return this.$store.state.activeProject.project.name
      }
    },

    activeUserName() {
      // Get the active user name -- the display name if defined; else the user name -- WARNING, duplicates TopNavbar.vue
      var username = userService.currentUser().username;
      var dispname = userService.currentUser().displayname;
      var userlabel = '';
      if (dispname === undefined || dispname === '') {
        userlabel = username;
      } else {
        userlabel = dispname;
      }
      return 'User: '+userlabel
    },
  },
  methods: {
    logOut() {
      userService.logOut()
    },
  }

}

</script>

<!-- Global SCSS/SASS settings go here. -->
<style lang="scss">
  // @import './sass/main.scss';

/* #app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
} */

  // Modal dialog styling.
  .vue-dialog div {
    box-sizing: border-box;
  }
  .vue-dialog .dialog-flex {
    width: 100%;
    height: 100%;
  }
  .vue-dialog .dialog-content {
    flex: 1 0 auto;
    width: 100%;
    padding: 15px;
    font-size: 14px;
  }
  .vue-dialog .dialog-c-title {
    font-weight: 600;
    padding-bottom: 15px;
  }
  .vue-dialog .dialog-c-text {
  }
  .vue-dialog .vue-dialog-buttons {
    display: flex;
    flex: 0 1 auto;
    width: 100%;
    border-top: 1px solid #eee;
  }
  .vue-dialog .vue-dialog-buttons-none {
    width: 100%;
    padding-bottom: 15px;
  }
  .vue-dialog-button {
    font-size: 12px !important;
    background: transparent;
    padding: 0;
    margin: 0;
    border: 0;
    cursor: pointer;
    box-sizing: border-box;
    line-height: 40px;
    height: 40px;
    color: inherit;
    font: inherit;
    outline: none;
  }
  .vue-dialog-button:hover {
    background: rgba(0, 0, 0, 0.01);
  }
  .vue-dialog-button:active {
    background: rgba(0, 0, 0, 0.025);
  }
  .vue-dialog-button:not(:first-of-type) {
    border-left: 1px solid #eee;
  }
</style>
