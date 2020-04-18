// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'

// Plugins
import Simplert from 'vue2-simplert-plugin' // Simple alert plugin
require('vue2-simplert-plugin/dist/vue2-simplert-plugin.css')
import VModal from 'vue-js-modal' // Modal dialogs plugin
import SideBar from './app/Sidebar' // SideBar plugin

import GlobalComponents from './globalComponents'
import GlobalDirectives from './globalDirectives'
import App from './App.vue'
import router from './router.js'
import store from './store.js'
import sciris from 'sciris-js';

Vue.config.productionTip = false
// library imports
import Chartist from 'chartist'
import 'bootstrap/dist/css/bootstrap.css'
import './sass/project.scss'
import 'es6-promise/auto'

// plugin setup
Vue.use(GlobalComponents);
Vue.use(GlobalDirectives);
// Vue.use(Notifications);
Vue.use(SideBar);
Vue.use(Simplert);
Vue.use(VModal);
// Vue.use(VueProgressBar, {
//   color: 'rgb(0, 0, 255)',
//   failedColor: 'red',
//   thickness: '3px',
//   transition: {
//     speed: '0.2s',
//     opacity: '0.6s',
//     termination: 300
//   }
// });

Vue.use(sciris);

Vue.use(sciris.ScirisVue, {
  notifications: {
    disable: false,
  },
  spinner: {
    disable: false,
  },
  progressbar: {
    disable: false,
    options: {
      color: 'rgb(0, 0, 255)',
      failedColor: 'red',
      thickness: '3px',
      transition: {
        speed: '0.2s',
        opacity: '0.6s',
        termination: 300
      }
    }
  }
})

// global library setup
Object.defineProperty(Vue.prototype, '$Chartist', {
  get () {
    return this.$root.Chartist
  }
})

Vue.prototype.$sciris = sciris;

new Vue({
  el: '#app',
  render: h => h(App),
  router: router,
  store: store,
  template: '<App/>',
  components: { App },
  data: {
    Chartist: Chartist
  }
})
