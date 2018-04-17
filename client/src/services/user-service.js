import rpcservice from '@/services/rpc-service'
import store from './../store'
import router from '@/router'
var state = {
  currentUser: {}
};

function getUserInfo() {
  rpcservice.rpcGetCurrentUserInfo('get_current_user_info')
  .then(response => {
    // Set the username to what the server indicates.
    store.commit('newUser', response.data.user)
  })
  .catch(error => {
    // Set the username to {}.  An error probably means the
    // user is not logged in.
    store.commit('newUser', {})
  })
}

function currentUser() {
    return store.state.currentUser
}

function checkLoggedIn () {
  if (this.currentUser.displayname == undefined)
    return false
  else
    return true
}

function checkAdminLoggedIn() {
  console.log(this)
  if (this.checkLoggedIn()) {
    return this.currentUser.admin
  }
}

function logOut (){
  // Do the logout request.
  console.log('it works1')
  rpcservice.rpcLogoutCall('user_logout')
    .then(response => {
      // Update the user info.
      getUserInfo()

      // Clear out the active project.
      store.commit('newActiveProject', {})

      // Navigate to the login page automatically.
      router.push('/login')
    })
}





export default {getUserInfo, currentUser, checkLoggedIn, checkAdminLoggedIn,  logOut}