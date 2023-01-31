<!--
Admin page

Last update: 2018sep23
-->

<template>
  <div class="SitePage">
    <h2>Users</h2>
    <table v-if="usersList[0] != undefined">
      <tr>
        <th>Username</th>
        <th>Display name</th>
        <th>Email</th>
        <th>Admin?</th>
        <th>Actions</th>
      </tr>
      <tr v-for="userobj in usersList">
        <td>{{ userobj.user.username }}</td>
        <td>{{ userobj.user.displayname }}</td>
        <td>{{ userobj.user.email }}</td>
        <td>{{ userobj.user.admin }}</td>
        <td>
          <button @click="grantAdmin(userobj.user.username)">Grant Admin</button>
          <button @click="revokeAdmin(userobj.user.username)">Revoke Admin</button>
          <button @click="resetPassword(userobj.user.username)">Reset Password</button>
          <button @click="deleteUser(userobj.user.username)">Delete Account</button>
        </td>
      </tr>
    </table>

    <p v-if="adminResult != ''">{{ adminResult }}</p>
  </div>
</template>

<script>
import router from '../router.js'

export default {
  name: 'MainAdminPage',

  data () {
    return {
      usersList: [],
      adminResult: ''
    }
  },

  created () {
    this.getUsersInfo()
  },

  methods: {
    getUsersInfo () {
      this.$sciris.rpc('admin_get_users')
      .then(response => {
        this.usersList = response.data
      })
      .catch(error => {
        // Give result message.
        this.adminResult = 'Could not load users from server.'
      })
    },

    activateAccount (username) {
      this.$sciris.activateUserAccount(username)
      .then(response => {
        // If the response was successful...
        if (response.data == 'success')
          // Give result message.
          this.adminResult = 'User account activated.'
        // Otherwise (failure)
        else
          // Give result message.
          this.adminResult = 'Account activation not successful.'

        // Get the users info again.
        this.getUsersInfo()
      })
      .catch(error => {
        // Give result message.
        this.adminResult = 'Account activation not successful.'
      })
    },

    deactivateAccount (username) {
      this.$sciris.deactivateUserAccount(username)
      .then(response => {
        // If the response was successful...
        if (response.data == 'success')
          // Give result message.
          this.adminResult = 'User account deactivated.'
        // Otherwise (failure)
        else
          // Give result message.
          this.adminResult = 'Account deactivation not successful.'

        // Get the users info again.
        this.getUsersInfo()
      })
      .catch(error => {
        // Give result message.
        this.adminResult = 'Account deactivation not successful.'
      })
    },

    grantAdmin (username) {
      this.$sciris.grantUserAdminRights(username)
      .then(response => {
        // If the response was successful...
        if (response.data == 'success')
          // Give result message.
          this.adminResult = 'Admin access granted.'
        // Otherwise (failure)
        else
          // Give result message.
          this.adminResult = 'Admin granting not successful.'

        // Get the users info again.
        this.getUsersInfo()
      })
      .catch(error => {
        // Give result message.
        this.adminResult = 'Admin granting not successful.'
      })
    },

    revokeAdmin (username) {
      this.$sciris.revokeUserAdminRights(username)
      .then(response => {
        // If the response was successful...
        if (response.data == 'success')
          // Give result message.
          this.adminResult = 'Admin access revoked.'
        // Otherwise (failure)
        else
          // Give result message.
          this.adminResult = 'Admin revocation not successful.'

        // Get the users info again.
        this.getUsersInfo()
      })
      .catch(error => {
        // Give result message.
        this.adminResult = 'Admin revocation not successful.'
      })
    },

    resetPassword (username) {
      this.$sciris.resetUserPassword(username)
      .then(response => {
        // If the response was successful...
        if (response.data == 'success')
          // Give result message.
          this.adminResult = 'Password reset.'
        // Otherwise (failure)
        else
          // Give result message.
          this.adminResult = 'Password reset not successful.'

        // Get the users info again.
        this.getUsersInfo()
      })
      .catch(error => {
        // Give result message.
        this.adminResult = 'Password reset not successful.'
      })
    },

    deleteUser (username) {
      this.$sciris.deleteUser(username)
      .then(response => {
        // Give result message.
        this.adminResult = 'User deleted.'

        // Get the users info again.
        this.getUsersInfo()
      })
      .catch(error => {
        // Give result message.
        this.adminResult = 'Deletion not successful.'
      })
    }

  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
