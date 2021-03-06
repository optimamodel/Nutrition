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
      name: 'Inputs', // ATOMICA-NUTRITION DIFFERENCE
      icon: 'ti-ruler-alt-2',
      path: '/inputs'
    },
    {
      name: 'Scenarios',
      icon: 'ti-control-shuffle',
      path: '/scenarios'
    },
    {
      name: 'Optimizations',
      icon: 'ti-stats-up',
      path: '/optimizations'
    },
    {
      name: 'Geospatial',
      icon: 'ti-world',
      path: '/geospatial'
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
