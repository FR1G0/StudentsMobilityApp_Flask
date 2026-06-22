import { Component, ChangeDetectorRef, Inject, PLATFORM_ID } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { App } from '../app';
import { Cookies } from '../cookies';
import { User, Users } from '../api/users';
import { Institutions, PartnerLink } from '../api/institutions';
import { Applications, ApplicationInsertBody, ApplicationUpdateBody, UploadedDocument } from '../api/applications';
import { Exams, Exam, MappedExamRow } from '../api/exams';

@Component({
  selector: 'app-application-form',
  imports: [CommonModule, FormsModule],
  templateUrl: './application-form.html',
  styleUrl: './application-form.css',
})
export class ApplicationForm {
  constructor(
    private cookie_manager: Cookies,
    private institutionsApi: Institutions,
    private applicationsApi: Applications,
    private examsApi: Exams,
    private usersApi: Users,
    private app: App,
    private router: Router,
    private cdr: ChangeDetectorRef,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {}

  // returns the error message sent back by the backend, or the given fallback
  private backendError(err: any, fallback: string): string {
    if (err && err.error && err.error.error) {
      return err.error.error;
    }
    return fallback;
  }

  // notifies the user the save went well and goes back to the applications list
  private goToApplications() {
    let message = 'Application created';
    if (this.action === 'edit') {
      message = 'Application updated';
    }
    this.app.send_notification(message, 'success');
    this.router.navigate(['/applications']);
  }

  action: string = 'create';
  editApplicationId: number = 0;
  editUserId: number = 0;

  user: User = {} as User;

  // form fields
  year: number = 0;
  semester: string = '';
  host_institution_id: number = 0;
  referent_id: number = 0;
  start_date: string = '';
  end_date: string = '';
  notes: string = '';
  status: string = '';

  // dropdown data
  semesters: string[] = [];
  academic_years: number[] = [];
  institutions: PartnerLink[] = [];
  referents: User[] = [];
  sendingExams: Exam[] = [];
  hostExams: Exam[] = [];

  examPairs: ExamPair[] = [{ local_exam_id: 0,  host_exam_id: 0 }];
  existingMappingIds: number[] = [];
  selectedFile: File | null = null;
  existingDocument: UploadedDocument | null = null;
  existingTranscript: UploadedDocument | null = null;
  transcriptFile: File | null = null;

  isSubmitting = false;
  submitError = '';

  cancel() {
    this.router.navigate(['/applications']);
  }

  ngOnInit() {
    const userData = this.cookie_manager.getCookie('user');
    if (userData) {
      this.user = JSON.parse(userData);
    }

    if(isPlatformBrowser(this.platformId)) {
      const state = history.state;
      if (state?.mode === 'edit' && state?.application) {
        this.action = 'edit';
        const app = state.application;
        this.editApplicationId = app.id;
        this.editUserId = app.user_id;
        this.year = app.year;
        this.semester = app.semester;
        this.host_institution_id = app.host_institution;
        this.referent_id = app.referent_id ?? 0;
        this.notes = app.notes ?? '';
        this.status = app.status ?? '';
        this.start_date = app.date_arrived ?? '';
        this.end_date = app.date_departure ?? '';
      }
      this.cdr.markForCheck();
    }


    this.applicationsApi.getSemesters().subscribe({
      next: res => this.semesters = res,
      complete : () => { this.cdr.markForCheck(); }
    });
    this.applicationsApi.getAcademicYears().subscribe({
      next: res => this.academic_years = res,
      complete : () => { this.cdr.markForCheck(); }
    });
  }

  ngAfterViewInit() {
    const id = this.user?.id_institution;
    if (!id) return;

    this.institutionsApi.getInstitutionPartners(id).subscribe({
      next: res => this.institutions = res,
      error: err => console.error(err),
      complete : () => { this.cdr.markForCheck(); }
    });

    this.institutionsApi.getInstitutionReferents(id).subscribe({
      next: res => this.referents = res,
      error: err => console.error(err),
      complete : () => { this.cdr.markForCheck(); }
    });

    this.examsApi.listExamsByInstitution(id).subscribe({
      next: res => this.sendingExams = res,
      error: err => console.error(err),
      complete : () => { this.cdr.markForCheck(); }
    });

    if (this.action === 'edit' && this.host_institution_id > 0) {
      // update user data
      this.usersApi.getUser(this.editUserId).subscribe({
        next: res => this.user = res,
        error: err => console.error(err),
      complete : () => { this.cdr.markForCheck(); }
      })

      // get exam mappings
      this.applicationsApi.listApplicationExamMappings(this.editApplicationId).subscribe({
        next: res => {
          this.onHostInstitutionChange();
          this.examPairs = [];
          this.existingMappingIds = [];
          for(let exam_map of res) {
            this.examPairs.push({
              local_exam_id: exam_map.sending_exam_id,
              host_exam_id: exam_map.host_exam_id,
              status: exam_map.status,
              notes: exam_map.notes
            });
            this.existingMappingIds.push(exam_map.id);
          }
          // keep at least one empty row so the user can still edit
          if (this.examPairs.length === 0) {
            this.examPairs.push({ local_exam_id: 0, host_exam_id: 0 });
          }
        },
        error: err => {
          console.error(err)
        },
        complete : () => { this.cdr.markForCheck(); }
      });

      // get selectedFile
      this.applicationsApi.listApplicationDocuments(this.editApplicationId).subscribe({
        next: res => {
          const la = res.find(d => d.document_type === 'learning_agreement');
          if (la) this.existingDocument = la;
          const tor = res.find(d => d.document_type === 'transcript');
          if (tor) this.existingTranscript = tor;
        },
        error : err => console.error(err),
        complete: () => { this.cdr.markForCheck(); }
      });
    }
  }

  onHostInstitutionChange() {
    this.hostExams = [];
    this.examPairs.forEach(p => p.host_exam_id = 0);
    if (this.host_institution_id > 0) {
      this.examsApi.listExamsByInstitution(this.host_institution_id).subscribe({
        next: res => this.hostExams = res,
        error: err => console.error(err),
        complete : () => { this.cdr.markForCheck(); }
      });
    }
  }

  addExamPair() {
    this.examPairs.push({ local_exam_id: 0, host_exam_id: 0 });
  }

  removeExamPair(index: number) {
    if (this.examPairs.length > 1) {
      this.examPairs.splice(index, 1);
    }
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files?.length) {
      this.selectedFile = input.files[0];
    }
  }

  removeFile() {
    this.selectedFile = null;
    const input = document.getElementById('la-upload') as HTMLInputElement;
    if (input) input.value = '';
  }

  // downloads the given uploaded document by fetching its blob and saving it
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

  formatFileSize(bytes: number): string {
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  submitApplication() {
    if (!this.year || !this.semester || !this.host_institution_id) {
      this.submitError = 'Please fill in all required fields.';
      return;
    }

    this.isSubmitting = true;
    this.submitError = '';

    if (this.action === 'edit' && this.editApplicationId !== null) {
      const body: ApplicationUpdateBody = {
        year: this.year,
        semester: this.semester,
        host_institution: this.host_institution_id,
        referent_id: this.referent_id || undefined,
        notes: this.notes || undefined,
        date_arrived: this.start_date || undefined,
        date_departure: this.end_date || undefined
      };
      this.applicationsApi.updateApplication(this.editApplicationId, body).subscribe({
        next: () => this.handleFileAndExams(this.editApplicationId!),
        error: err => {
          console.error(err);
          this.isSubmitting = false;
          this.submitError = this.backendError(err, 'Update failed. Please try again.');
          this.app.send_notification(this.submitError, 'error');
        }
      });
    } else {
      const body: ApplicationInsertBody = {
        year: this.year,
        semester: this.semester,
        sending_institution: this.user.id_institution,
        host_institution: this.host_institution_id,
        referent_id: this.referent_id || undefined,
        notes: this.notes || undefined
      };
      this.applicationsApi.insertApplication(body).subscribe({
        next: res => {
          if (res.error) {
            this.isSubmitting = false;
            this.submitError = res.error;
            this.app.send_notification(res.error, 'error');
            return;
          }
          const appId = res.id;
          if (!appId) {
            this.goToApplications();
            return;
          }
          if (this.start_date || this.end_date) {
            this.applicationsApi.updateApplication(appId, {
              date_arrived: this.start_date || undefined,
              date_departure: this.end_date || undefined
            }).subscribe({
              next: () => this.handleFileAndExams(appId),
              error: () => this.handleFileAndExams(appId)
            });
          } else {
            this.handleFileAndExams(appId);
          }
        },
        error: err => {
          console.error(err);
          this.isSubmitting = false;
          this.submitError = this.backendError(err, 'Submission failed. Please try again.');
          this.app.send_notification(this.submitError, 'error');
        }
      });
    }
  }

  private handleFileAndExams(applicationId: number) {
    if (!this.selectedFile) {
      this.handleExamMappings(applicationId);
      return;
    }

    // when replacing, remove the previous learning agreement row first
    if (this.existingDocument) {
      this.applicationsApi.deleteApplicationDocument(this.existingDocument.id).subscribe({
        next: () => console.log("uploaded"),
        error: err => console.error(err),
        complete : () => this.uploadAndInsert(applicationId)
      });
    } else {
      this.uploadAndInsert(applicationId);
    }
  }

  private uploadAndInsert(applicationId: number) {
      this.applicationsApi.uploadApplicationDocument(applicationId, this.selectedFile!).subscribe({
        next: res => {
          if (res.status === 'success' && res.file_path) {
            this.applicationsApi.insertApplicationDocument({
              document_type: 'learning_agreement',
              file_path: res.file_path,
              application_id: applicationId
            }).subscribe({
              next: () => this.handleExamMappings(applicationId),
              error: err => {
                console.log(err);
                this.app.send_notification(this.backendError(err, 'Could not save the learning agreement'), 'warning');
                this.handleExamMappings(applicationId);
              }
            });
          } else {
            console.log(res);
            this.handleExamMappings(applicationId);
          }
        },
        error: err => {
          this.app.send_notification(this.backendError(err, 'Could not upload the learning agreement'), 'warning');
          this.handleExamMappings(applicationId);
        }
      });
    }


  private handleExamMappings(applicationId: number) {
    const validPairs = this.examPairs.filter(p => p.local_exam_id > 0 && p.host_exam_id > 0);

    // in edit mode, drop the previous mappings first so removals/changes take
    // effect and re-inserts do not collide with the unique constraints
    if (this.existingMappingIds.length > 0) {
      let deleted = 0;
      const total = this.existingMappingIds.length;
      const afterDelete = () => {
        deleted = deleted + 1;
        if (deleted === total) {
          this.insertMappings(applicationId, validPairs);
        }
      };
      for (let mappingId of this.existingMappingIds) {
        this.examsApi.deleteMappedExam(mappingId).subscribe({ next: afterDelete, error: afterDelete });
      }
    } else {
      this.insertMappings(applicationId, validPairs);
    }
  }

  private insertMappings(applicationId: number, validPairs: ExamPair[]) {
    if (!validPairs.length) {
      this.goToApplications();
      return;
    }
    let done = 0;
    const finish = () => { if (++done === validPairs.length) this.goToApplications(); };
    for (let pair of validPairs) {
      this.examsApi.insertMappedExam(applicationId, {
        sending_exam_id: pair.local_exam_id,
        host_exam_id: pair.host_exam_id
      }).subscribe({
        next: finish,
        error: err => {
          this.app.send_notification(this.backendError(err, 'An exam mapping could not be saved'), 'warning');
          finish();
        }
      });
    }
  }

  shortenStatus(status: string): string {
    if (status == 'learning_agreement_pending') return 'la pending';
    if (status == 'pre_departure_completed') return 'pre completed';
    if (status == 'mobility_ongoing') return 'ongoing';
    if (status == 'exam_recognition') return 'exam recognition';
    return status;
  }

  // ---- Student mobility lifecycle ----
  // start mobility moves the application to 'mobility_ongoing' and registers the
  // arrival date; end mobility moves it to 'exam_recognition' so the transcript of
  // records can then be uploaded. the database triggers validate each transition.

  startMobility() {
    this.studentSetStatus('mobility_ongoing', 'Mobility started');
  }

  endMobility() {
    this.studentSetStatus('exam_recognition', 'Mobility ended');
  }

  private studentSetStatus(newStatus: string, message: string) {
    this.applicationsApi.updateApplication(this.editApplicationId, {
      status: newStatus,
      date_arrived: this.start_date || undefined,
      date_departure: this.end_date || undefined
    }).subscribe({
      next: res => {
        if (res.status !== 'success') {
          this.app.send_notification(res.error || 'Operation failed', 'error');
          return;
        }
        this.status = newStatus;
        this.app.send_notification(message, 'success');
      },
      error: err => this.app.send_notification(this.backendError(err, 'Operation failed'), 'error'),
      complete: () => this.cdr.markForCheck()
    });
  }

  onTranscriptSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files?.length) {
      this.transcriptFile = input.files[0];
    }
  }

  // uploads the transcript of records during 'exam_recognition'
  uploadTranscript() {
    if (!this.transcriptFile) {
      this.app.send_notification('Please select a transcript file', 'warning');
      return;
    }
    this.applicationsApi.uploadApplicationDocument(this.editApplicationId, this.transcriptFile).subscribe({
      next: res => {
        if (res.status === 'success' && res.file_path) {
          this.applicationsApi.insertApplicationDocument({
            document_type: 'transcript',
            file_path: res.file_path,
            application_id: this.editApplicationId
          }).subscribe({
            next: () => {
              this.transcriptFile = null;
              this.app.send_notification('Transcript uploaded', 'success');
              this.reloadTranscript();
            },
            error: err => this.app.send_notification(this.backendError(err, 'Could not save the transcript'), 'error'),
            complete: () => this.cdr.markForCheck()
          });
        } else {
          this.app.send_notification('Could not upload the transcript', 'error');
        }
      },
      error: err => this.app.send_notification(this.backendError(err, 'Could not upload the transcript'), 'error'),
      complete: () => this.cdr.markForCheck()
    });
  }

  // reloads the transcript document after a successful upload
  private reloadTranscript() {
    this.applicationsApi.listApplicationDocuments(this.editApplicationId).subscribe({
      next: res => {
        const tor = res.find(d => d.document_type === 'transcript');
        if (tor) this.existingTranscript = tor;
      },
      error: err => console.error(err),
      complete: () => this.cdr.markForCheck()
    });
  }
}

interface ExamPair {
  local_exam_id: number;
  host_exam_id: number;
  // decision info coming from the existing mapping (used to show a rejection note)
  status?: string;
  notes?: string;
}
