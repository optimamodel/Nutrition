<!--
App.vue -- App component, the main page

Last update: 2018sep23
-->

<template>
  <div :class="{'nav-open': $sidebar.showSidebar}">
    <simplert></simplert>
    <router-view></router-view>
    <vue-progress-bar></vue-progress-bar>
    <popup-spinner size="75px" padding="15px" title="Please wait..."></popup-spinner>
    <side-bar type="navbar" :sidebar-links="$sidebar.sidebarLinks"> <!--This sidebar appears only for screens smaller than 992px -- otherwise, it is rendered in Navbar.vue-->
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
        <dropdown v-bind:title="activeUserName" icon="ti-user">
          <li><a href="#/changeinfo"><i class="ti-pencil"></i>&nbsp;Edit account</a></li>
          <li><a href="#/changepassword"><i class="ti-key"></i>&nbsp;Change password</a></li>
          <li><a href="#" v-on:click=logOut()><i class="ti-car"></i>&nbsp;Log out</a></li>
        </dropdown>
        <li class="divider"></li>
      </ul>
    </side-bar>
  </div>

</template>

<script>

  import sciris from 'sciris-js';
  import Vue from 'vue'; // This needs to appear somewhere but only once

export default {
  computed: {

    activeProjectName() {
      if (this.$store.state.activeProject.project === undefined) {
        return 'none'
      } else {
        return this.$store.state.activeProject.project.name
      }
    },

    activeUserName() {
      // Get the active user name -- the display name if defined; else the user name -- WARNING, duplicates Navbar.vue
      var username = this.$store.state.currentUser.username;
      var dispname = this.$store.state.currentUser.displayname;
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
      this.$sciris.logoutCall();
      this.$store.commit('logOut');
      this.$router.push('/login');
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
  @import './sass/_dialogs.scss';
</style>
