<!--
User registration page

Last update: 2018-08-26
-->


<template>
  <div class="SitePage" style="background-color:#f8f8f4; position:fixed; min-height:100%; min-width:100%; padding:0 0 0 0" v-model="getVersionInfo"> <!-- Should match _variables.scss:$bg-nude -->
    <div style="background-color:#0c2544; position:absolute; height:100%; width:260px">
      <div class="logo">
        <div class="simple-text" style="font-size:20px; color:#fff; font-weight:bold; padding:20px">
          <span style="padding-left:10px">
            <a href="http://ocds.co" target="_blank">
              <img src="static/img/optima-inverted-logo.png" width="160px" vertical-align="middle" alt> <!--  ATOMICA-NUTRITION DIFFERENCE -->
            </a>
          </span>
          <br/><br/>
          <div style="font-size:14px; font-weight:normal">
            Version {{ version }} ({{ date }})
          </div>

          <br/><br/>
          <LocaleSwitcher />

        </div>
      </div>
    </div>
    <div style="margin-right:-260px">
      <form name="RegisterForm" @submit.prevent="tryRegister" style="max-width: 500px; min-width: 100px; margin: 0 auto">

        <div class="modal-body">
          <h2>{{ $t("Register") }}</h2>

          <div class="section" v-if="registerResult != ''">{{ registerResult }}</div>

          <div class="section form-input-validate">
            <input class="txbox __l"
                   type="text"
                   name="username"
                   :placeholder="$t('placeholder.Username')"
                   required="required"
                   v-model='registerUserName'/>
          </div>

          <div class="section form-input-validate">
            <input class="txbox __l"
                   type="password"
                   name="password"
                   :placeholder="$t('placeholder.Password')"
                   required="required"
                   v-model='registerPassword'/>
          </div>

          <div class="section form-input-validate">
            <input class="txbox __l"
                   type="text"
                   name="displayname"
                   :placeholder="$t('placeholder.Display name (optional)')"
                   v-model='registerDisplayName'/>
          </div>

          <div class="section form-input-validate">
            <input class="txbox __l"
                   type="text"
                   name="email"
                   :placeholder="$t('placeholder.Email (optional)')"
                   v-model='registerEmail'/>
          </div>

          <button type="submit" class="section btn __l __block">{{ $t("Register") }}</button>

          <div class="section">
            {{ $t("register.Already registered?") }}
            <router-link to="/login">
              {{ $t("Login") }}
            </router-link>
          </div>

        </div>
      </form>
    </div>
  </div>
</template>


<script>
import router from '../router.js'
import LocaleSwitcher from "./LocaleSwitcher.vue"

export default {
  name: 'RegisterPage',
  components: {LocaleSwitcher},
  data () {
    return {
      registerUserName: '',
      registerPassword: '',
      registerDisplayName: '',
      registerEmail: '',
      registerResult: '',
      version: '',
      date: '',
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
    tryRegister () {
      this.$sciris.registerUser(this.registerUserName, this.registerPassword,
        this.registerDisplayName, this.registerEmail)
      .then(response => {
        if (response.data === 'success') { // Set a success result to show.
          this.registerResult = 'Success! Please wait while you are redirected...';
          setTimeout(function() {router.push('/login')}, 1000); // Navigate automatically to the login page after a delay
        } else { // Set a failure result to show.
          this.registerResult = response.data;
        }
      })
      .catch(error => {
          console.log('Register failed', error)
          this.registerResult = "We're sorry, it seems we're having trouble communicating with the server.  Please contact support or try again later."
      })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
