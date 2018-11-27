import Vue from 'vue';
import Router from 'vue-router';

import AboutPage from './app/AboutPage.vue';
import ContactPage from './app/ContactPage.vue';
import DashboardLayout from './app/DashboardLayout.vue'
import GeospatialPage from './app/GeospatialPage.vue'
import HelpPage from './app/HelpPage.vue';
import InputsPage from './app/InputsPage.vue';
import NotFoundPage from './app/NotFoundPage.vue';
import OptimizationsPage from './app/OptimizationsPage.vue';
import ProjectsPage from './app/ProjectsPage.vue';
import ScenariosPage from './app/ScenariosPage.vue';

import { views } from 'sciris-uikit';

Vue.use(Router);

const appProps = {
  logo: "static/img/optima-inverted-logo.png",
  homepage: "http://ocds.co" 
}

let router = new Router({
  routes: [
    {
      path: '/mainadmin',
      name: 'Admin',
      component: views.MainAdminPage,
    },
    {
      path: '/login',
      name: 'Login',
      component: views.LoginPage,
      props: appProps 
    },
    {
      path: '/register',
      name: 'Registration',
      component: views.RegisterPage,
      props: appProps 
    },
    {
      path: '/',
      component: DashboardLayout,
      redirect: '/projects',
      children: [
        {
          path: 'optimizations',
          name: 'Create optimizations',
          component: OptimizationsPage
        },
        {
          path: '/changepassword',
          name: 'Change password',
          component: views.ChangePasswordPage,
        }, {
          path: '/changeinfo',
          name: 'Edit account',
          component: views.UserChangeInfoPage,
        },
        {
          path: 'projects',
          name: 'Manage projects',
          component: ProjectsPage
        },
        {
          path: 'inputs', 
          name: 'Inputs',
          component: InputsPage
        },
        {
          path: 'geospatial',
          name: 'Geospatial analysis',
          component: GeospatialPage
        },
        {
          path: 'scenarios',
          name: 'Create scenarios',
          component: ScenariosPage
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
    { path: '*', component: NotFoundPage }
  ]
});

export default router
