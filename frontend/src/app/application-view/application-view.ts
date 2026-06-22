import { Component, ChangeDetectorRef, Inject, PLATFORM_ID } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { App } from '../app';
import { Cookies } from '../cookies';
import { User, Users } from '../api/users';
import { Institutions } from '../api/institutions';
import { Applications, Application, UploadedDocument } from '../api/applications';
import { Exams, Exam, MappedExamRow } from '../api/exams';

@Component({
  selector: 'app-application-view',
  imports: [CommonModule, FormsModule],
  templateUrl: './application-view.html',
  styleUrl: './application-view.css',
})
export class ApplicationView {
  constructor(
    private app: App,
    private cookie_manager: Cookies,
    private usersApi: Users,
    private institutionsApi: Institutions,
    private applicationsApi: Applications,
    private examsApi: Exams,
    private router: Router,
    private cdr: ChangeDetectorRef,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {}

  // the currently logged user: decides which controls are visible (role based)
  user: User = {} as User;

  // the application being viewed (passed through the router navigation state)
  application: Application = {} as Application;
  applicationId: number = 0;

  // the student that owns the application
  student: User = {} as User;

  // resolved labels for read-only display
  hostInstitutionName: string = '';
  referentName: string = '';

  // exams of each institution, used to turn mapping ids into readable labels
  sendingExams: Exam[] = [];
  hostExams: Exam[] = [];

  // exam mappings and documents of the application
  mappings: MappedExamRow[] = [];
  learningAgreement: UploadedDocument | null = null;
  transcript: UploadedDocument | null = null;

  // referent rejection-reason inputs
  mappingReason: { [id: number]: string } = {};
  laReason: string = '';
  torReason: string = '';

  cancel() {
    this.router.navigate(['/applications']);
  }

  ngOnInit() {
    const userData = this.cookie_manager.getCookie('user');
    if (userData) {
      this.user = JSON.parse(userData);
    }

    if (isPlatformBrowser(this.platformId)) {
      const state = history.state;
      if (state && state.application) {
        this.application = state.application;
        this.applicationId = this.application.id;
      }
      this.cdr.markForCheck();
    }
  }

  ngAfterViewInit() {
    if (!this.applicationId) {
      return;
    }

    // load the student that owns the application
    this.usersApi.getUser(this.application.user_id).subscribe({
      next: res => this.student = res,
      error: err => console.error(err),
      complete: () => this.cdr.markForCheck()
    });

    // resolve the referent name (if the application has one)
    if (this.application.referent_id) {
      this.usersApi.getUser(this.application.referent_id).subscribe({
        next: res => this.referentName = res.firstname + ' ' + res.lastname,
        error: err => console.error(err),
        complete: () => this.cdr.markForCheck()
      });
    }

    // resolve the host institution name from the sending institution partners
    this.institutionsApi.getInstitutionPartners(this.application.sending_institution).subscribe({
      next: res => {
        for (let partner of res) {
          if (partner.id_partner_institution === this.application.host_institution) {
            this.hostInstitutionName = partner.name + ' — ' + partner.city + ', ' + partner.country;
          }
        }
      },
      error: err => console.error(err),
      complete: () => this.cdr.markForCheck()
    });

    // load the exams of both institutions, to label the mappings
    this.examsApi.listExamsByInstitution(this.application.sending_institution).subscribe({
      next: res => this.sendingExams = res,
      error: err => console.error(err),
      complete: () => this.cdr.markForCheck()
    });
    this.examsApi.listExamsByInstitution(this.application.host_institution).subscribe({
      next: res => this.hostExams = res,
      error: err => console.error(err),
      complete: () => this.cdr.markForCheck()
    });

    // load the exam mappings of the application
    this.applicationsApi.listApplicationExamMappings(this.applicationId).subscribe({
      next: res => this.mappings = res,
      error: err => console.error(err),
      complete: () => this.cdr.markForCheck()
    });

    // load the documents (learning agreement + transcript of records)
    this.applicationsApi.listApplicationDocuments(this.applicationId).subscribe({
      next: res => {
        for (let doc of res) {
          if (doc.document_type === 'learning_agreement') {
            this.learningAgreement = doc;
          }
          if (doc.document_type === 'transcript') {
            this.transcript = doc;
          }
        }
      },
      error: err => console.error(err),
      complete: () => this.cdr.markForCheck()
    });
  }

  // returns a readable label for an exam id, using the given exam list
  examLabel(examId: number, exams: Exam[]): string {
    for (let exam of exams) {
      if (exam.id === examId) {
        return exam.name + ' (' + exam.code + ', ' + exam.credits + ' cr.)';
      }
    }
    return '#' + examId;
  }

  formatYear(year: number): string {
    return year + '/' + (year + 1);
  }

  shortenStatus(status: string): string {
    if (status == 'learning_agreement_pending') return 'la pending';
    if (status == 'pre_departure_completed') return 'pre completed';
    if (status == 'mobility_ongoing') return 'ongoing';
    if (status == 'exam_recognition') return 'exam recognition';
    return status;
  }

  // downloads an uploaded document by fetching its blob and saving it
  downloadDocument(doc: UploadedDocument) {
    this.applicationsApi.downloadDocument(doc.id).subscribe({
      next: blob => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = doc.file_path.split('/').pop() || 'document';
        link.click();
        window.URL.revokeObjectURL(url);
      },
      error: err => console.error(err)
    });
  }

  // ---- Referent decisions on exam mappings ----

  approveMapping(mapping: MappedExamRow) {
    this.examsApi.updateMappedExamStatus(mapping.id, { status: 'approved' }).subscribe({
      next: res => {
        if (res.status === 'success') {
          mapping.status = 'approved';
          mapping.notes = '';
          this.app.send_notification('Exam mapping approved', 'success');
        } else {
          this.app.send_notification(res.error || 'Could not approve the mapping', 'error');
        }
      },
      error: err => this.app.send_notification(this.readError(err), 'error'),
      complete: () => this.cdr.markForCheck()
    });
  }

  rejectMapping(mapping: MappedExamRow) {
    let reason = (this.mappingReason[mapping.id] || '').trim();
    if (!reason) {
      this.app.send_notification('Please provide a reason for the rejection', 'warning');
      return;
    }
    this.examsApi.updateMappedExamStatus(mapping.id, { status: 'rejected', notes: reason }).subscribe({
      next: res => {
        if (res.status === 'success') {
          mapping.status = 'rejected';
          mapping.notes = reason;
          this.app.send_notification('Exam mapping rejected', 'success');
        } else {
          this.app.send_notification(res.error || 'Could not reject the mapping', 'error');
        }
      },
      error: err => this.app.send_notification(this.readError(err), 'error'),
      complete: () => this.cdr.markForCheck()
    });
  }

  // ---- Referent decisions on the learning agreement ----
  // approving the LA moves the application to 'created';
  // rejecting it moves the application to 'learning_agreement_pending' and needs a reason.

  approveLearningAgreement() {
    if (!this.learningAgreement) {
      return;
    }
    let documentId = this.learningAgreement.id;
    this.applicationsApi.updateDocumentStatus(documentId, { status: 'approved' }).subscribe({
      next: res => {
        if (res.status !== 'success') {
          this.app.send_notification(res.error || 'Could not approve the learning agreement', 'error');
          return;
        }
        this.learningAgreement!.status = 'approved';
        this.learningAgreement!.notes = '';
        this.setApplicationStatus('created', 'Learning agreement approved');
      },
      error: err => this.app.send_notification(this.readError(err), 'error'),
      complete: () => this.cdr.markForCheck()
    });
  }

  rejectLearningAgreement() {
    if (!this.learningAgreement) {
      return;
    }
    let reason = this.laReason.trim();
    if (!reason) {
      this.app.send_notification('Please provide a reason for the rejection', 'warning');
      return;
    }
    let documentId = this.learningAgreement.id;
    this.applicationsApi.updateDocumentStatus(documentId, { status: 'rejected', notes: reason }).subscribe({
      next: res => {
        if (res.status !== 'success') {
          this.app.send_notification(res.error || 'Could not reject the learning agreement', 'error');
          return;
        }
        this.learningAgreement!.status = 'rejected';
        this.learningAgreement!.notes = reason;
        this.setApplicationStatus('learning_agreement_pending', 'Learning agreement rejected');
      },
      error: err => this.app.send_notification(this.readError(err), 'error'),
      complete: () => this.cdr.markForCheck()
    });
  }

  // updates the application status and notifies the user when done
  private setApplicationStatus(status: string, successMessage: string) {
    this.applicationsApi.updateApplication(this.applicationId, { status: status }).subscribe({
      next: () => {
        this.application.status = status;
        this.app.send_notification(successMessage, 'success');
      },
      error: err => this.app.send_notification(this.readError(err), 'error'),
      complete: () => this.cdr.markForCheck()
    });
  }

  // ---- Referent decisions on the transcript of records ----

  approveTranscript() {
    if (!this.transcript) {
      return;
    }
    this.applicationsApi.updateDocumentStatus(this.transcript.id, { status: 'approved' }).subscribe({
      next: res => {
        if (res.status === 'success') {
          this.transcript!.status = 'approved';
          this.transcript!.notes = '';
          this.app.send_notification('Transcript approved', 'success');
        } else {
          this.app.send_notification(res.error || 'Could not approve the transcript', 'error');
        }
      },
      error: err => this.app.send_notification(this.readError(err), 'error'),
      complete: () => this.cdr.markForCheck()
    });
  }

  rejectTranscript() {
    if (!this.transcript) {
      return;
    }
    let reason = this.torReason.trim();
    if (!reason) {
      this.app.send_notification('Please provide a reason for the rejection', 'warning');
      return;
    }
    this.applicationsApi.updateDocumentStatus(this.transcript.id, { status: 'rejected', notes: reason }).subscribe({
      next: res => {
        if (res.status === 'success') {
          this.transcript!.status = 'rejected';
          this.transcript!.notes = reason;
          this.app.send_notification('Transcript rejected', 'success');
        } else {
          this.app.send_notification(res.error || 'Could not reject the transcript', 'error');
        }
      },
      error: err => this.app.send_notification(this.readError(err), 'error'),
      complete: () => this.cdr.markForCheck()
    });
  }

  // pulls a readable message out of an http error response
  private readError(err: any): string {
    if (err && err.error && err.error.error) {
      return err.error.error;
    }
    return 'Operation failed';
  }
}
