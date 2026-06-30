import { ChangeDetectionStrategy, Component } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatSidenavModule,
    MatToolbarModule,
    MatListModule,
    MatIconModule,
  ],
  template: `
    <mat-sidenav-container class="app-container">
      <mat-sidenav mode="side" opened class="app-sidenav">
        <div class="nav-header">
          <mat-icon class="logo-icon">school</mat-icon>
          <span class="logo-text">AI Tutor</span>
        </div>
        <mat-nav-list>
          <a mat-list-item routerLink="/tutor" routerLinkActive="active-nav">
            <mat-icon matListItemIcon>chat</mat-icon>
            <span matListItemTitle>Tutor</span>
          </a>
          <a mat-list-item routerLink="/dashboard" routerLinkActive="active-nav">
            <mat-icon matListItemIcon>bar_chart</mat-icon>
            <span matListItemTitle>Dashboard</span>
          </a>
          <a mat-list-item routerLink="/settings" routerLinkActive="active-nav">
            <mat-icon matListItemIcon>settings</mat-icon>
            <span matListItemTitle>Settings</span>
          </a>
        </mat-nav-list>
      </mat-sidenav>

      <mat-sidenav-content class="app-content">
        <router-outlet />
      </mat-sidenav-content>
    </mat-sidenav-container>
  `,
  styles: [`
    .app-container { height: 100vh; background: #0f1117; }

    .app-sidenav {
      width: 220px;
      background: #1a1d27;
      border-right: 1px solid #2d3748;
    }

    .nav-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 1.25rem 1rem;
      border-bottom: 1px solid #2d3748;

      .logo-icon { color: #7c3aed; font-size: 1.75rem; }
      .logo-text { font-size: 1rem; font-weight: 700; color: #e2e8f0; }
    }

    .active-nav {
      background: rgba(124, 58, 237, 0.15) !important;
      color: #a78bfa !important;
      border-left: 3px solid #7c3aed;
    }

    .app-content { display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
  `],
})
export class AppComponent {}
