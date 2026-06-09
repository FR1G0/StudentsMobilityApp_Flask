import { Routes } from '@angular/router';


export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'home',
  },
  {
    path: 'home',
    loadComponent: () =>
      import('./pages/home-page.component').then((m) => m.HomePageComponent),
  },
  {
    path: 'application-list',
    loadComponent: () =>
      import('./pages/application-list.component').then(
        (m) => m.ApplicationListComponent,
      ),
  },
  {
    path: '**',
    redirectTo: 'home',
  },
];
