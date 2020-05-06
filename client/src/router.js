// index.js -- vue-router path configuration code
//
// Last update: 2018sep23

// Import main things
import Vue from 'vue'
import Router from 'vue-router'
import DashboardLayout from './app/DashboardLayout.vue'

// App views
import NotFound from './app/NotFoundPage.vue'
import ProjectsPage from './app/ProjectsPage.vue'
import InputsPage from './app/InputsPage.vue' // ATOMICA-NUTRITION DIFFERENCE
import ScenariosPage from './app/ScenariosPage.vue'
import OptimizationsPage from './app/OptimizationsPage.vue'
import GeospatialPage from './app/GeospatialPage.vue'
import LoginPage from './app/LoginPage.vue'
import MainAdminPage from './app/MainAdminPage.vue'
import RegisterPage from './app/RegisterPage.vue'
import UserChangeInfoPage from './app/UserChangeInfoPage.vue'
import ChangePasswordPage from './app/ChangePasswordPage.vue'
import HelpPage from './app/HelpPage.vue'
import ContactPage from './app/ContactPage.vue'
import AboutPage from './app/AboutPage.vue'
import store from './store.js'


Vue.use(Router);

let router = new Router({
  routes: [
    {
      path: '/register',
      name: 'Registration',
      component: RegisterPage
    },
    {
      path: '/login',
      name: 'Login',
      component: LoginPage
    },
    {
      path: '/',
      component: DashboardLayout,
      redirect: '/projects',
      children: [
        {
          path: 'projects',
          name: 'Manage projects',
          component: ProjectsPage,
          meta: {requiresAuth: true}
        },
        {
          path: 'inputs',
          name: 'Inputs',
          component: InputsPage,
          meta: {requiresAuth: true}
        },
        {
          path: 'scenarios',
          name: 'Create scenarios',
          component: ScenariosPage,
          meta: {requiresAuth: true}
        },
        {
          path: 'optimizations',
          name: 'Create optimizations',
          component: OptimizationsPage,
          meta: {requiresAuth: true}
        },
        {
          path: 'geospatial',
          name: 'Geospatial analysis',
          component: GeospatialPage,
          meta: {requiresAuth: true}
        },
        {
          path: 'mainadmin',
          name: 'Admin',
          component: MainAdminPage,
          meta: {requiresAuth: true}
        },
        {
          path: 'changeinfo',
          name: 'Edit account',
          component: UserChangeInfoPage,
          meta: {requiresAuth: true}
        },
        {
          path: 'changepassword',
          name: 'Change password',
          component: ChangePasswordPage,
          meta: {requiresAuth: true}
        },
        {
          path: 'help',
          name: 'Help',
          component: HelpPage,
          meta: {requiresAuth: true}
        },
        {
          path: 'contact',
          name: 'Contact',
          component: ContactPage,
          meta: {requiresAuth: true}
        },
        {
          path: 'about',
          name: 'About',
          component: AboutPage,
          meta: {requiresAuth: true}
        },
      ]
    },
    { path: '*', component: NotFound }
  ]
})

router.beforeEach((to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (store.getters.isLoggedIn) {
      next()
      return
    }
    next({
      name: "Login",
      query: {loginRequired: to.fullPath}
    })
  } else {
    next()
  }
})

export default router
