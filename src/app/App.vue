<!--
App.vue App component, the main page

Last update: 2018sep23
-->

<template>
  <div :class="{'nav-open': $sidebar.showSidebar}">
    <simplert></simplert>
    <router-view></router-view>
    <vue-progress-bar></vue-progress-bar>
    <popup-spinner size="75px" padding="15px" title="Please wait..."></popup-spinner>
    <sidebar 
      class="main-sidebar" 
      type="navbar" 
      logo="/static/img/optima-inverted-logo.png" 
      :links="sidebarLinks">
    <!--
    This sidebar appears only for screens 
    smaller than 992px otherwise, it is rendered in TopNavbar.vue
    -->
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
        <li>
            <a 
            class="username"
            data-toggle="collapse" 
            href="#userTools">
              <i class="ti-user"></i> {{ activeUserName }}</strong>
            </a>

            <div class="collapse" id="userTools">
              <ul class="nav navbar-nav"> 
                <router-link to="/changeinfo" tag="li">
                  <a><i class="ti-pencil"></i>&nbsp;Edit account</a>
                </router-link>
                <router-link to="/changepassword" tag="li">
                  <a><i class="ti-key"></i>&nbsp;Change password</a>
                </router-link>
                <li>
                  <a href="#/" v-on:click=logOut()><i class="ti-car"></i>&nbsp;Log out</a>
                </li>
              </ul>
            </div>
        </li>
        <li class="divider"></li>
      </ul>
    </sidebar>
  </div>
</template>

<script>
import sciris from 'sciris-js';

export default {
  created() {
    sciris.getUserInfo(this.$store)
  },
  computed: {
    currentUser: () => {
      return this.$store.state.currentUser
    },

    sidebarLinks(){
      return this.$store.state.sidebarLinks;
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
      sciris.logOut()
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
@import "~sciris-uikit/dist/scss/_dialogs.scss";
.username {
color: #c1c8cf;
font-size: 16px;
font-weight: 600;
}

.divider {
margin: 10px 0;
padding: 1px;
}

.main-sidebar {
font-size: 14px;
}

#userTools.collapsing {
-webkit-transition: none;
transition: none;
display: none;
}

#userTools.collapsing .nav {
width: 100%;
}

#userTools .nav {
width: 100%;
}

</style>
