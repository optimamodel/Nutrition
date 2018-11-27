<!--
Help page

Last update: 2018sep23
-->

<template>
  <div class="SitePage">
    <div style="text-align:center">
      <div style="display:inline-block; margin:auto; text-align:left" v-model="getVersionInfo">
        <div>
          <p>We are in the process of writing a user guide.</p>
          <p>For assistance in the mean time, please email <a href="mailto:help@ocds.co">help@ocds.co</a>.</p>
          <p>Please copy and paste the table below into your email, along with any error messages.</p>
        </div>

        <table class="table table-bordered table-striped table-hover">
          <thead>
          <tr>
            <th colspan=100>Technical information</th>
          </tr>
          </thead>
          <tbody>
          <tr><td class="tlabel">Username    </td><td>{{ username }}</td></tr>
          <tr><td class="tlabel">Browser     </td><td>{{ useragent }}</td></tr>
          <tr><td class="tlabel">App version </td><td>{{ verboseToolName }} {{ version }} ({{ date }}) [{{ gitbranch }}/{{ githash }}]</td></tr>
          <tr><td class="tlabel">Timestamp   </td><td>{{ timestamp }}</td></tr>
          <tr><td class="tlabel">Server name </td><td>{{ server }}</td></tr>
          <tr><td class="tlabel">Server load </td><td>{{ cpu }}</td></tr>
          </tbody>
        </table>

        <div>
          <button @click="adv_consoleModal">
            <span v-if="!adv_showConsole">Developer options</span>
            <span v-if="adv_showConsole">Hide developer options</span>
          </button>
        </div>

        <div v-if="adv_showConsole">
          <br><br>
          <div class="controls-box">
            <b>Token</b><br>
            <input type="password"
                   class="txbox"
                   v-model="adv_authentication"/><br>
            <b>Query</b><br>
            <textarea rows="10" cols="100" v-model="adv_query"/><br>
            <button @click="adv_submit">Submit</button><br><br><br>
            <b>Output</b><br>
            <span v-html="adv_response"></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mixins } from 'sciris-uikit';
export default {
  name: 'About',
  methods: {
    verboseToolName() {
      return 'Optima Nutrition'
    },
  }
}
</script>

<style scoped>
.tlabel {
  font-weight:bold;
}
</style>
