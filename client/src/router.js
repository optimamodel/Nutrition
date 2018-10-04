// index.js -- vue-router path configuration code
//
// Last update: 2018sep23

// Import main things
import Vue from 'vue'
import Router from 'vue-router'
import DashboardLayout from '@/app/DashboardLayout.vue'

// App views
import NotFound from '@/app/NotFoundPage.vue'
import ProjectsPage from '@/app/ProjectsPage'
import InputsPage from '@/app/InputsPage' // ATOMICA-NUTRITION DIFFERENCE
import ScenariosPage from '@/app/ScenariosPage'
import OptimizationsPage from '@/app/OptimizationsPage'
import GeospatialPage from '@/app/GeospatialPage'
import LoginPage from '@/app/LoginPage'
import MainAdminPage from '@/app/MainAdminPage'
import RegisterPage from '@/app/RegisterPage'
import UserChangeInfoPage from '@/app/UserChangeInfoPage'
import ChangePasswordPage from '@/app/ChangePasswordPage'
import HelpPage from '@/app/HelpPage'
import ContactPage from '@/app/ContactPage'
import AboutPage from '@/app/AboutPage'


Vue.use(Router);

export default new Router({
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
          component: ProjectsPage
        },
        {
          path: 'inputs',  // ATOMICA-NUTRITION DIFFERENCE
          name: 'Inputs',
          component: InputsPage
        },
        {
          path: 'scenarios',
          name: 'Create scenarios',
          component: ScenariosPage
        },
        {
          path: 'optimizations',
          name: 'Create optimizations',
          component: OptimizationsPage
        },
        {
          path: 'geospatial',
          name: 'Geospatial analysis',
          component: GeospatialPage
        },
        {
          path: 'mainadmin',
          name: 'Admin',
          component: MainAdminPage
        },
        {
          path: 'changeinfo',
          name: 'Edit account',
          component: UserChangeInfoPage
        },
        {
          path: 'changepassword',
          name: 'Change password',
          component: ChangePasswordPage
        },
        {
          path: 'help',
          name: 'Help',
          component: HelpPage
        },
        {
          path: 'contact',
          name: 'Contact',
          component: ContactPage
        },
        {
          path: 'about',
          name: 'About',
          component: AboutPage
        },
      ]
    },
    { path: '*', component: NotFound }
  ]
})
