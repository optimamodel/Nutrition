<!--
Login page

Last update: 2018sep22
-->

<template>
  <div class="SitePage" style="background-color:#f8f8f4; position:fixed; min-height:100%; min-width:100%; padding:0 0 0 0" v-model="getVersionInfo"> <!-- Should match _variables.scss:$bg-nude -->
    <div style="background-color:#0c2544; position:absolute; height:100%; width:260px">
      <div class="logo">
        <div class="simple-text" style="font-size:20px; font-weight:bold; padding:20px">
          <span style="padding-left:10px">
            <a href="http://ocds.co" target="_blank">
              <img src="static/img/optima-inverted-logo.png" width="160px" vertical-align="middle" alt> <!-- // ATOMICA-NUTRITION DIFFERENCE -->
            </a>
          </span>
          <br/><br/>
          <div v-if="version" style="font-size:14px; font-weight:normal">
            <a href="#" @click="showChangelog=true">
            Version {{ version }} ({{ date }})
            </a>
            <Changelog v-if="showChangelog" @close="showChangelog=false" />
          </div>

          <br/><br/>
          <LocaleSwitcher />

        </div>
      </div>
    </div>
    <div style="margin-right:-260px">
      <form name="LogInForm" @submit.prevent="tryLogin" style="max-width: 500px; min-width: 100px; margin: 0 auto">

        <div class="modal-body">
          <h2>{{ $t("Login") }}</h2>
          <div class="section">
            {{ $t("login.deprecation_warning") }}
            <a href="http://nutrition.legacy.optimamodel.com" target="_blank">
            {{ $t("Access the legacy version here") }}
            </a>
          </div>

          <div class="section" v-if="loginResult != ''">{{ loginResult }}</div>

          <div class="section form-input-validate">
            <input class="txbox __l"
                   type="text"
                   name="username"
                   :placeholder="$t('placeholder.Username')"
                   required="required"
                   v-model='loginUserName'/>
          </div>

          <div class="section form-input-validate">
            <input class="txbox __l"
                   type="password"
                   name="password"
                   :placeholder="$t('placeholder.Password')"
                   required="required"
                   v-model='loginPassword'/>
          </div>

          <button type="submit" class="section btn __l __block">{{ $t("Login") }}</button>

          <div class="section">
            {{ $t("login.New user?") }}
            <router-link to="/register">
              {{ $t("login.Register here") }}
            </router-link>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
  import router from '../router.js'
  import Changelog from './Changelog.vue'
  import LocaleSwitcher from "./LocaleSwitcher.vue"

  export default {
    name: 'LoginPage',
    components: {Changelog, LocaleSwitcher},

    data () {
      return {
        loginUserName: '',
        loginPassword: '',
        loginResult: '',
        version: '',
        date: '',
        showChangelog: false,
      }
    },

    computed: {
      getVersionInfo() {
        this.$sciris.rpc('get_version_info')
        .then(response => {
          this.version = response.data['version'];
          this.date = response.data['date'];
        })
      },
    },

    methods: {
      tryLogin () {
        this.$sciris.loginCall(this.loginUserName, this.loginPassword)
        .then(response => {
          if (response.data === 'success') {
            // Set a success result to show.
            this.loginResult = 'Logging in...'

            console.log('Login accepted')

            // Read in the full current user information.
            this.$sciris.getCurrentUserInfo()
            .then(response2 => {
              // Set the username to what the server indicates.

              console.log('Committing user')

              this.$store.commit('newUser', response2.data.user)

              // Navigate automatically to the home page.

              console.log('Navigating')

              router.push('/')
            })
            .catch(error => {
              // Set the username to {}.  An error probably means the
              // user is not logged in.
              this.$store.commit('newUser', {})
            })
          } else {
            // Set a failure result to show.
            this.loginResult = response.data
          }
        })
        .catch(error => {
          console.log('Login failed', error)
          this.loginResult = "We're sorry, it seems we're having trouble communicating with the server.  Please contact support or try again later."
        })
      }
    }
  }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
