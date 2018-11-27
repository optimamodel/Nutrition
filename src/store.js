import Vue from 'vue';
import Vuex from 'vuex';

Vue.use(Vuex);

const store = new Vuex.Store({
  state: {
    currentUser: {},
    activeProject: {},
    helpLinks: {
      baseURL: 'https://docs.google.com/document/d/1YIsB7kqtd7gRPSZl33dpho4fnp5Fssfp4pF-_-VdFbA/edit#heading=h.4d34og8',
      linkMap: {
        // 'create-projects': 'h.wohgolfxe9ko',
        // 'manage-projects': 'h.fcnvzbrouon2'
      }
    },
    sidebarLinks: [
      {
        name: 'Projects',
        icon: 'ti-view-grid',
        path: '/projects'
      },
      {
        name: 'Inputs',
        path: '/inputs',
        icon: 'ti-ruler-alt-2',
      },
      {
        name: 'Scenarios',
        path: '/scenarios',
        icon: 'ti-control-shuffle',
      },
      {
        name: 'Optimizations',
        path: '/optimizations',
        icon: 'ti-stats-up',
      },
      {
        name: 'Geospatial', 
        path: '/geospatial',
        icon: 'ti-world',
      },
      {
        name: 'Help',
        icon: 'ti-help',
        path: '/help'
      },
      {
        name: 'Contact',
        icon: 'ti-comment-alt',
        path: '/contact'
      },
      {
        name: 'About',
        icon: 'ti-shine',
        path: '/about'
      },
    ],
    navbarLinks: [
      {
        name: 'Projects',
        path: '/projects'
      },
      {
        name: 'Inputs',
        path: '/inputs'
      },
      {
        name: 'Scenarios',
        path: '/scenarios'
      },
      {
        name: 'Optimizations',
        path: '/optimizations'
      },
      {
        name: 'Geospatial', 
        path: '/geospatial'
      },
    ]
  },
  mutations: {
    newUser(state, user) {
      state.currentUser = user
    }, 
    newActiveProject(state, project) {
      state.activeProject = project
    }
  },
});

export default store
