// index.js -- vue-router path configuration code
//
// Last update: 2/21/18 (gchadder3)

// Import main things
import Vue from 'vue'
import Router from 'vue-router'
import DashboardLayout from '@/components/app/DashboardLayout.vue'

// App views
import NotFound from '@/components/generic/NotFoundPage.vue'
import ProjectsPage from '@/components/app/ProjectsPage'
import DemographicsPage from '@/components/app/DemographicsPage'
import CalibrationPage from '@/components/app/CalibrationPage'
import ScenariosPage from '@/components/app/ScenariosPage'
import AnalysisPage from '@/components/app/AnalysisPage'
//import DiseaseRiskPage from '@/components/app/DiseaseRiskPage'
//import InterventionsPage from '@/components/app/InterventionsPage'
import LoginPage from '@/components/app/LoginPage'
import MainAdminPage from '@/components/app/MainAdminPage'
import RegisterPage from '@/components/app/RegisterPage'
import UserChangeInfoPage from '@/components/app/UserChangeInfoPage'
import ChangePasswordPage from '@/components/app/ChangePasswordPage'
import Help from '@/components/app/Help'
import Contact from '@/components/app/Contact'
import About from '@/components/app/About'


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
          path: 'demographics',
          name: 'Demographics',
          component: DemographicsPage
        },
        {
          path: 'calibration',
          name: 'Calibration',
          component: CalibrationPage
        },
        {
          path: 'scenarios',
          name: 'Scenarios',
          component: ScenariosPage
        },
        {
          path: 'analysis',
          name: 'Analysis',
          component: AnalysisPage
        },
        // {
        //   path: 'disease-risk',
        //   name: 'Disease risk',
        //   component: DiseaseRiskPage
        // },
        // {
        //   path: 'interventions',
        //   name: 'Define interventions',
        //   component: InterventionsPage
        // },
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
          component: Help
        },
        {
          path: 'contact',
          name: 'Contact',
          component: Contact
        },
        {
          path: 'about',
          name: 'About',
          component: About
        },
      ]
    },
    { path: '*', component: NotFound }
  ]
})
