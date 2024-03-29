// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'

// Plugins
import VModal from 'vue-js-modal' // Modal dialogs plugin
import SideBar from './app/Sidebar' // SideBar plugin

import GlobalComponents from './globalComponents.js'
import GlobalDirectives from './globalDirectives.js'
import App from './App.vue'
import router from './router.js'
import store from './store.js'
import sciris from 'sciris-js';

Vue.config.productionTip = false;
// library imports
import Chartist from 'chartist'
import 'bootstrap/dist/css/bootstrap.css'
// import BootstrapVue from 'bootstrap-vue'
// Vue.use(BootstrapVue)
import './sass/project.scss'
import 'es6-promise/auto'
import i18n from "./i18n.js";

import Simplert from 'vue2-simplert-plugin'
require('vue2-simplert-plugin/dist/vue2-simplert-plugin.css');
Vue.use(Simplert);

// plugin setup
Vue.use(GlobalComponents);
Vue.use(GlobalDirectives);
Vue.use(SideBar);
Vue.use(VModal);

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
});

// global library setup
Object.defineProperty(Vue.prototype, '$Chartist', {
  get () {
    return this.$root.Chartist
  }
});

Vue.prototype.$sciris = sciris;

new Vue({
  el: '#app',
  render: h => h(App),
  router: router,
  store: store,
  i18n,
  template: '<App/>',
  components: { App },
  data: {
    Chartist: Chartist
  }
});
