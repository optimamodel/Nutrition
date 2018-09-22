<!--
Help page

Last update: 2018sep22
-->

<template>
  <div class="SitePage" style="text-align:center">
    <div style="display:inline-block; margin:auto; text-align:left" v-model="getVersionInfo">
      <p>We are in the process of writing a user guide.</p>
      <p>For assistance in the mean time, please email <a href="mailto:help@ocds.co">help@ocds.co</a>.</p>

      <table class="table table-bordered table-striped table-hover">
        <thead>
        <tr>
          <th colspan=100>Optima Nutrition technical information</th>
        </tr>
        </thead>
        <tbody>
        <tr>
          <td class="tlabel">Version </td>
          <td>{{ version }}</td>
        </tr>
        <tr>
          <td class="tlabel">Date </td>
          <td>{{ date }}</td>
        </tr>
        <tr>
          <td class="tlabel">Branch </td>
          <td>{{ gitbranch }}</td>
        </tr>
        <tr>
          <td class="tlabel">Hash </td>
          <td>{{ githash }}</td>
        </tr>
        <tr>
          <td class="tlabel">Timestamp </td>
          <td>{{ gitdate }}</td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
  import rpcs from '@/js/rpc-service'

  export default {
    name: 'About',

    data () {
      return {
        version: '',
        date: '',
        gitbranch: '',
        githash: '',
        gitdate: '',
      }
    },

    computed: {
      getVersionInfo() {
        rpcs.rpc('get_version_info')
          .then(response => {
            this.version = response.data['version'];
            this.date = response.data['date'];
            this.gitbranch = response.data['gitbranch'];
            this.githash = response.data['githash'];
            this.gitdate = response.data['gitdate'];
          })
      },
    },
  }
</script>

<style scoped>
  .tlabel {
    font-weight:bold;
  }

</style>