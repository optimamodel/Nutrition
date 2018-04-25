import Sidebar from './SideBar.vue'

const SidebarStore = {
  showSidebar: false,
  sidebarLinks: [
    {
      name: 'Projects',
      icon: 'ti-view-grid',
      path: '/projects'
    },
    {
      name: 'Demographics',
      icon: 'ti-bar-chart',
      path: '/demographics'
    },
    {
      name: 'Calibration',
      icon: 'ti-ruler-alt-2',
      path: '/calibration'
    },
    {
      name: 'Interventions',
      icon: 'ti-pulse',
      path: '/interventions'
    },
    {
      name: 'Analysis',
      icon: 'ti-stats-up',
      path: '/analysis'
    },
    {
      name: 'Disease burden',
      icon: 'ti-bar-chart',
      path: '/bod'
    },
    {
      name: 'Equity',
      icon: 'ti-ruler',
      path: '/equity'
    },
    {
      name: 'Financial risk',
      icon: 'ti-bolt',
      path: '/financialrisk'
    },
    {
      name: 'Health packages',
      icon: 'ti-heart',
      path: '/healthpackages'
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

  displaySidebar (value) {
    this.showSidebar = value
  },
}

const SidebarPlugin = {

  install (Vue) {
    Vue.mixin({
      data () {
        return {
          sidebarStore: SidebarStore
        }
      }
    })

    Object.defineProperty(Vue.prototype, '$sidebar', {
      get () {
        return this.$root.sidebarStore
      }
    })
    Vue.component('side-bar', Sidebar)
  }
}

export default SidebarPlugin
