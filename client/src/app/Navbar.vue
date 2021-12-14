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
          <span class="sr-only">{{ $t("navbar.Toggle navigation") }}</span>
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
              <span>{{ $t("navbar.Projects") }}</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/inputs"> <!--  ATOMICA-NUTRITION DIFFERENCE -->
              <span>{{ $t("navbar.Inputs") }}</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/scenarios">
              <span>{{ $t("navbar.Scenarios") }}</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/optimizations">
              <span>{{ $t("navbar.Optimizations") }}</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/geospatial">
              <span>{{ $t("navbar.Geospatial") }}</span>
            </router-link>
          </li>
        </ul>
        <ul class="nav navbar-nav navbar-right">
          <li class="nav-item">
            <div class="nav-link">
              <i class="ti-view-grid"></i>
              <span>{{ $t("navbar.Project") }}: {{ activeProjectName }}</span>
            </div>
          </li>
          <dropdown>
            <!--            The template behaves oddly if content is bound to the dropdown properties, so just manually fill out the title slot instead-->
            <template v-slot:title>
              <div class="dropdown-title">
                <i class="ti-user dropdown-icon"></i>
                {{ $t("navbar.User") }}: {{ activeUserName }}
                <b class="caret"></b>
              </div>
            </template>
            <li><a href="#/changeinfo"><i class="ti-pencil"></i>&nbsp;&nbsp;{{ $t("navbar.Edit account") }}</a></li>
            <li><a href="#/changepassword"><i class="ti-key"></i>&nbsp;&nbsp;{{ $t("navbar.Change password") }}</a></li>
            <li><a href="#/help"><i class="ti-help"></i>&nbsp;&nbsp;{{ $t("navbar.Help") }}</a></li>
            <li><a href="#/about"><i class="ti-shine"></i>&nbsp;&nbsp;{{ $t("navbar.About") }}</a></li>
            <li><a href="#" v-on:click=logOut()><i class="ti-car"></i>&nbsp;&nbsp;{{ $t("navbar.Log out") }}</a></li>
          </dropdown>


          <li v-if="projectLocale !== uiLocale" class="nav-item">
            <div class="nav-link">
              <i class="ti-alert" v-b-tooltip.hover :title="$t('navbar.language_warning')" />
            </div>
          </li>


          <li class="nav-item">
            <div class="nav-link">
              <LocaleSwitcher/>
            </div>
          </li>

        </ul>

      </div>


    </div>

  </nav>
</template>


<script>

import LocaleSwitcher from "./LocaleSwitcher.vue"
import i18n from '../i18n'

export default {
  name: 'Navbar',
  components: {LocaleSwitcher},

  data() {
    return {
      activePage: 'manage projects'
    }
  },

  computed: {

    activeProjectName() {
      return this.$store.getters.activeProjectName
    },
    activeUserName() {
      return this.$store.getters.activeUserName
    },
    projectLocale() {
      return this.$store.getters.projectLocale
    },
    uiLocale() {
      return i18n.locale
    },

    // Theme function
    routeName() {
      const route_name = this.$route.name;
      return this.capitalizeFirstLetter(route_name)
    },
  },

  created() {
    this.$sciris.getUserInfo(this.$store)
  },


  methods: {

    checkLoggedIn() {
      this.$sciris.checkLoggedIn
    },

    checkAdminLoggedIn() {
      this.$sciris.checkAdminLoggedIn
    },

    logOut() {
      this.$sciris.logoutCall();
      this.$store.commit('logOut');
      this.$router.push('/login');
    },

    // Theme functions
    capitalizeFirstLetter(string) {
      return string.charAt(0).toUpperCase() + string.slice(1)
    },

    toggleSidebar() {
      this.$sidebar.displaySidebar(!this.$sidebar.showSidebar)
    },
  }
}

</script>

