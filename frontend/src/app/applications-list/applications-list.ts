import { Component, OnInit, ChangeDetectorRef, Inject, PLATFORM_ID } from '@angular/core';
import { NgClass, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { App } from '../app';
import { Applications, Application } from '../api/applications';
import { Institutions } from '../api/institutions';
import { Users } from '../api/users';

@Component({
  selector: 'app-applications-list',
  imports: [FormsModule, NgClass],
  templateUrl: './applications-list.html',
  styleUrl: './applications-list.css',
})
export class ApplicationsList implements OnInit {
  constructor(
    private applicationsApi: Applications,
    private institutionsApi: Institutions,
    private usersApi: Users,
    private app : App,
    private router: Router,
    private cdr: ChangeDetectorRef,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {}

  inputSearch: string = '';
  inputFilterBy: string = 'all';
  isLoading = true;

  applications: Application[] = [];

  // lookup maps to resolve ids into readable values (institution name, student email)
  institutionNames: { [id: number]: string } = {};
  userEmails: { [id: number]: string } = {};

  // id of the application whose action menu is currently open (null = none)
  openMenuId: number | null = null;

  // role of the logged user, decides which actions are available
  get role(): string {
    return this.app.user_data ? this.app.user_data.role : '';
  }

  filterOptions: FilterOption[] = [
    { id: 'all',                        name: 'All' },
    { id: 'created',                    name: 'Created' },
    { id: 'learning_agreement_pending', name: 'LA Pending' },
    { id: 'pre_departure_completed',    name: 'Pre-Departure' },
    { id: 'mobility_ongoing',           name: 'Ongoing' },
    { id: 'exam_recognition',           name: 'Exam Recognition' },
    { id: 'closed',                     name: 'Closed' }
  ];

  ngOnInit() {
    if(!isPlatformBrowser(this.platformId)) { return; }
    this.applicationsApi.getApplications().subscribe({
      next: res => {
        this.applications = res;
        this.isLoading = false;
        this.cdr.markForCheck();
      },
      error: err => {
        console.error(err);
        this.app.send_notification(err,'error');
        this.isLoading = false;
        this.cdr.markForCheck();
      }
    });

    // load institution names so we can show sending/host names instead of ids
    this.institutionsApi.getInstitutions().subscribe({
      next: res => {
        for (let institution of res) {
          this.institutionNames[institution.id] = institution.name;
        }
        this.cdr.markForCheck();
      },
      error: err => console.error(err)
    });

    // load user emails so we can show the applicant email instead of the user id
    this.usersApi.getAllUsers().subscribe({
      next: res => {
        for (let user of res) {
          this.userEmails[user.id] = user.email;
        }
        this.cdr.markForCheck();
      },
      error: err => console.error(err)
    });
  }

  // returns the institution name for the given id (falls back to the id)
  institutionName(id: number): string {
    return this.institutionNames[id] || ('#' + id);
  }

  // returns the applicant email for the given application
  applicantEmail(application: Application): string {
    return this.userEmails[application.user_id] || '';
  }

  // opens/closes the action dropdown menu of a single application row
  toggleMenu(id: number, event: Event) {
    event.stopPropagation();
    if (this.openMenuId === id) {
      this.openMenuId = null;
    } else {
      this.openMenuId = id;
    }
  }

  closeMenu() {
    this.openMenuId = null;
  }

  get filteredApplications(): Application[] {
    return this.applications
      .filter(a => this.inputFilterBy === 'all' || a.status === this.inputFilterBy)
      .filter(a => {
        if (!this.inputSearch) return true;
        const q = this.inputSearch.toLowerCase();
        return String(a.id).includes(q) ||
               String(a.year).includes(q) ||
               a.semester.toLowerCase().includes(q) ||
               a.status.toLowerCase().includes(q) ||
               a.notes.toLowerCase().includes(q);
      });
  }

  formatYear(year: number): string {
    return `${year}/${year + 1}`;
  }

  shortenStatus(status: string): string {
    if(status=='learning_agreement_pending') return 'la pending';
    if(status=='pre_departure_completed') return 'pre completed';
    if(status=='mobility_ongoing') return 'ongoing';
    if(status=='learning_agreement_pending') return 'closed';
    return status;
  }

  viewApplication(application: Application) {
    this.router.navigate(['/application-view'], { state: { application } });
  }

  editApplication(application: Application) {
    this.router.navigate(['/form-modify'], { state: { application, mode: 'edit' } });
  }

  deleteApplication(application: Application) {
    if (!isPlatformBrowser(this.platformId)) { return; }
    const confirmed = window.confirm('Delete application #' + application.id + '? This cannot be undone.');
    if (!confirmed) { return; }

    this.applicationsApi.deleteApplication(application.id).subscribe({
      next: res => {
        if (res.status === 'success') {
          this.applications = this.applications.filter(a => a.id !== application.id);
        } else {
          this.app.send_notification(res.error || 'deleting error','error');
          console.error(res.error);
        }
      },
      error: err => {
        console.error(err);
        this.app.send_notification(err.error.error || 'deleting error','error');
      },
      complete: () => this.cdr.markForCheck()
    });
  }
}

interface FilterOption {
  id: string;
  name: string;
}
