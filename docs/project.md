# Project Requirements
----------------------
	- auto populate the database on containerized db
	- preload test data when the backend starts, to simplify exam-day testing 
	- each component (backend, database, frontend) must run in its own Docker container — TAW requirement 
	- dual stack note: the DB course wants Python + Flask + SQLAlchemy + PostgreSQL; the TAW course wants Node.js + Express + Angular SPA with MongoDB or a relational DB. Same domain, two backends. 


# Entities & Permissions
----------------------
## Student
    - List of created Mobility Applications
        - Applicaiton Preview
            - with the ability view or add modifications
			- upload
		- upload transcript of records
    - Application Creation View
        - confirm creation (preview the document in a separate view then confirm)
    - Upload signed Learning Agreement file as part of an application 
    - Enter actual arrival / departure dates at the host institution once mobility starts 
    - Propose modifications to exam mapping during mobility — each modification carries a textual description and requires uploading a new LA; if rejected, the previous mapping/LA must be restored 
    - After return: fill in score and exam date for each mapped exam, alongside the Transcript of Records upload 

## Lecturer 
    - List of exisitng Mobile Applications assigned to that specific lecturer
        - Application Preview
            - show information (form input & uploaded file)
            - show exam mappings
			- approve or reject + reason
		- approve transcript of records
	- Add can exams for its own institution
    - Approve or reject each LA modification proposed during mobility, recording date and reason 
    - Approve or reject each individual exam + score after the ToR is uploaded (per-exam, not just the document as a whole) 
    - Every approve/reject action records a decision date and, on reject, a motivation 

## Overseas Staff 
    - All applicantions (host institution, guest institution, assigned applicaiton)
    - Applicaiton Preview 
		- set pre-departure phase (complete only if approved by lecturer)
        - can complete or close
		- close application after transcript of records is uploaded
	- Ability to add new partner Institution (extra)
	- Ability to remove partner Instution, + keep applications history? (extra)
    - Close application only after ToR is uploaded AND all exams have been individually approved by the referent lecturer 
    - Dashboard with applications grouped by status, country, host institution (extra) 
    - Notifications / flagging for incomplete or stalled applications (extra) 


# Frontend Views & capabilities
----------------------
## Dashboard (top-level)
    - sidebar with entries fetched from the db based on role
    - topbar for quick access to other stuff

## Authentication
    - login using JWT
    - JWT stored in cookie or localStorage — TAW spec explicitly requires one of the two 

## Application Creation
### Students
	- form information
	- exam mappings
    - essential application fields: academic year, host institution (from partner list), expected period (1st semester / 2nd semester / full year), referent lecturer 
    - exam mapping rows must capture: foreign code, foreign title, foreign credits, Ca' Foscari code, Ca' Foscari title, Ca' Foscari credits 

## Application Preview
### Students & Referents
    - show information about application
    - show the mapping between exams
    - show the uploaded documents
    - show the application's current state in the workflow 
    - show decision history: LA approvals/rejections with date + reason, modification proposals with their outcomes 

## In-Progress Mobility View 
### Students
    - input actual arrival / departure dates 
    - submit LA modification proposals: textual description + new mapping + new LA file 

## Post-Mobility View 
### Students
    - upload Transcript of Records 
    - fill score and date for each exam in the mapping 
### Lecturers
    - per-exam approve/reject of the recognized exam + score 


# Database
----------------------
## Istitutions
	- is partnered with other institutions
	- has assigned lecturers
    - has assigned students
    - has assigned exams/lectures
	- TODO: if an institution gets deleted must be handled
    - fields: at least name, country, city 

## Partnership
    - between two institutions
    - has assigned applications
    - cannot be self-assigned
	
## Student
	- assigned to istitution
	- assigned to multiple applications
	- If a student gets deleted all data associated to him must be deleted

## Application
	- assigned student
	- partner & host institutions
    - stato
        - bozza / draft
        - attesa LA / waiting for LA
        - partenza / departure
        - in corso / in progress
        - riconoscimento esami / recognition
        - chiusa / closed
        - annullata / canceled — added by TAW spec 
	- assigned lecturer
	- exam mappings
    - academic year 
    - expected period: 1st semester / 2nd semester / full year 
    - actual arrival date, actual departure date (filled during mobility) 

## Lecturer / Refernt
	- assigned to only one istitutions, a referent cannot work for two universities

## Learning Agreement 
    - file blob/path, upload date, version 
    - linked to one application; an application may have multiple LA versions over time (history of uploads is suggested by both specs) 
    - latest LA holds approval state (approved / rejected / pending), decision date, reason on reject 

## Exam Mapping 
    - linked to one application (one application → many mapping rows) 
    - foreign side: code, title, credits 
    - home (Ca' Foscari) side: code, title, credits 
    - after mobility: score, exam date, recognition status (pending / approved / rejected), lecturer decision date, reason on reject 

## LA Modification Proposal 
    - linked to one application 
    - textual description of the change, new LA file reference, proposed new mapping snapshot 
    - state: pending / approved / rejected; on reject, the application's exam mapping and LA must revert to the previous version atomically 
    - decision date, reason on reject 

## Transcript of Records 
    - file blob/path, upload date, version 
    - linked to one application 


# Critical Implementation Areas 
----------------------
## Data integrity — emphasized by the DB course 
    - FK constraints: application ↔ student / institution / lecturer 
    - referent lecturer must belong to Ca' Foscari (sending institution), enforced at DB or app level 
    - partnership.institution_a ≠ partnership.institution_b — CHECK constraint 
    - application state transitions enforced via trigger or app-level state machine — e.g. cannot reach "pre-departure completed" without an approved LA; cannot reach "closed" without all exam recognitions approved 
    - rejecting an LA modification must restore the previous mapping in a single transaction 

## Security 
    - role-based authorization on every endpoint: student → own applications only; lecturer → applications where they are referent; office → all 
    - JWT verification middleware (Express) / decorator (Flask) on protected routes 
    - uploaded files (LA, ToR) must be access-controlled, not served from a public static path 

## Performance 
    - indexes on: application.student_id, application.lecturer_id, application.state, application.host_institution_id 
    - consider a materialized view for the office dashboard (counts grouped by state / country / institution) 

## REST API design — emphasized by the TAW course 
    - endpoints grouped by resource: /applications, /institutions, /users, /exam-mappings, /la-modifications, /transcripts 
    - actions modeled as sub-resources where it reads cleanly: POST /applications/:id/la, POST /applications/:id/la/decision, POST /applications/:id/exam-mappings/:eid/recognition 
    - TAW report must document endpoints, parameters, and request/response JSON examples — design the API with the doc in mind 
