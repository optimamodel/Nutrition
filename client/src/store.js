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
          store.commit('newScenSummaries', storage.scenSummaries);
          store.commit('newOptimSummaries', storage.optimSummaries);
        }
      } catch (e) {
      }
    }
  });
};

const store = new Vuex.Store({
  state: {
    // The currently logged in user
    currentUser: null,

    // The project currently chosen by the user
    activeProject: null,

    // The scenario/optim summaries for the currently active project
    scenSummaries: null,
    optimSummaries: null,
    checkProject: null,
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

    newScenSummaries(state, summaries) {
      state.scenSummaries = summaries
      state.checkProject = state.activeProject
    },

    newOptimSummaries(state, summaries) {
      state.optimSummaries = summaries
      state.checkProject = state.activeProject
    },

    logOut(state) {
      state.currentUser = null;
      state.activeProject = null;
      state.checkProject = null;
      state.scenSummaries = null;
      state.optimSummaries = null;
    },

  },
  getters: {
    activeProjectName: state => state.activeProject ? state.activeProject.project.name : 'none',
    activeProjectID: state => state.activeProject ? state.activeProject.project.id : undefined,
    isLoggedIn: state => !!state.currentUser,
    projectOpen: state => !!state.activeProject,
    activeUserName: state => state.currentUser ?  state.currentUser.displayname || state.currentUser.username : 'none',
    projectLocale: state => state.activeProject?  state.activeProject.project.locale : undefined,
  },
});

// Comment out line below to quickly disable persistent storage
store.commit('loadStorage');

export default store