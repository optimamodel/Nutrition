// index.js -- Vuex store configuration
//
// Last update: 3/7/18 (gchadder3)

import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex);

const persist = store => {
  store.subscribe((mutation, state) => {
    if (mutation.type !== 'loadStorage') {
      try {
        sessionStorage.setItem('appdata', JSON.stringify(state));
      } catch (e) {
      }
    } else {
      console.log('Loading storage');
      try {
        let storage = sessionStorage.getItem('appdata') || false;
        if (storage) {
          storage = JSON.parse(storage);
          store.commit('newUser', storage.currentUser);
          store.commit('newActiveProject', storage.activeProject);
        }
      } catch (e) {
      }
    }
  });
};

const store = new Vuex.Store({
  state: {
    // The currently logged in user
    currentUser: {},

    // The project currently chosen by the user
    activeProject: {}
  },
  plugins: [persist],
  mutations: {
    loadStorage(state) {
    },

    newUser(state, user) {
      state.currentUser = user
    },

    newActiveProject(state, project) {
      state.activeProject = project
    },

    logOut(state) {
      state.currentUser = {};
      state.activeProject = {};
    },

  },
  getters: {
    isLoggedIn: state => "displayname" in state.currentUser && state.currentUser.displayname !== undefined,
    projectOpen: state => state.activeProject !== null,
  },
});

// Comment out line below to quickly disable persistent storage
store.commit('loadStorage');

export default store