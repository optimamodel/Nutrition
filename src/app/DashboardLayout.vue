<!--
Definition of the dashboard itself

Last update: 2018-08-16
-->

<template>
  <div class="wrapper">

    <notifications></notifications>

    <div class="main-panel">

      <navbar
        :links="navbarLinks"
        logo="static/img/optima-logo-nutrition.png"
        homepage="http://ocds.co/"
      ></navbar>

      <dashboard-content @click.native="toggleSidebar"></dashboard-content>

      <content-footer></content-footer>

    </div>
  </div>
</template>
<script>
import sciris from 'sciris-js';
import ContentFooter from './ContentFooter.vue'
import DashboardContent from './Content.vue'

export default {
  components: {
    ContentFooter,
    DashboardContent
  },
  computed: {
    navbarLinks(){
      return this.$store.state.navbarLinks;
    },
  },
  methods: {
    toggleSidebar () {
      if (this.$sidebar.showSidebar) {
        this.$sidebar.displaySidebar(false)
      }
    }
  }
}
</script>
