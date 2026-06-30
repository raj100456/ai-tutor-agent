import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'tutor',
    pathMatch: 'full',
  },
  {
    path: 'tutor',
    loadComponent: () =>
      import('./features/tutor/tutor.component').then(m => m.TutorComponent),
    title: 'AI Tutor',
  },
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent),
    title: 'Progress Dashboard',
  },
  {
    path: 'settings',
    loadComponent: () =>
      import('./features/settings/settings.component').then(m => m.SettingsComponent),
    title: 'Settings',
  },
  {
    path: '**',
    redirectTo: 'tutor',
  },
];
