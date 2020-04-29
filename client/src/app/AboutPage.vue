<!--
About page

Last update: 2018sep23
-->

<template>
  <div class="SitePage">
    <div style="max-width:800px; margin:auto">
      <div style="text-align:center;">

        <img src="static/img/optima-logo-nutrition.png" width="250px">
        <br/><br/>

        <a href="#" @click="showChangelog=true">
          Version {{ version }} ({{ date }})
        </a>
        <Changelog v-if="showChangelog" @close="showChangelog=false"/>

      </div>

      <br/>

      <p>Optima Nutrition is currently under development. Development is supported through a partnership
        between the <a href="http://www.burnet.edu.au">Burnet Institute</a> and the <a href="http://www.worldbank.org">World Bank</a>.</p>

      <p>
        Information about Optima Nutrition is available as a <a href="http://ocds.co/appfiles/Optima_Nutrition_Overview.pdf" target="_blank">PDF</a> or
        <a href="http://ocds.co/appfiles/Optima_Nutrition_Overview.pdf" target="_blank">PowerPoint</a> presentation.
      </p>

      <br/>
      <br/>
      <div class="divTable" style="width:100%">
        <div class="divTableBody">
          <div class="divTableRow">
            <div class="divRowContent" style="text-align:center; padding-bottom:30px"><img src="static/img/burnet-logo-transparent.png" height="60px"></div>
            <div class="divRowContent" style="text-align:center; padding-bottom:30px"><img src="static/img/world-bank-logo.png" height="60px"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import router from '../router.js'
  import Changelog from './Changelog.vue'

  export default {
    name: 'AboutPage',
    components: {Changelog},

    data() {
      return {
        version: '',
        date: '',
        showChangelog: false,
      }
    },

    async created() {
      let response = await this.$sciris.rpc('get_version_info');
      this.version = response.data.version;
      this.date = response.data.date;
    },

  }
</script>