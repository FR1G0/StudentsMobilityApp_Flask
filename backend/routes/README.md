# Backend Routes

All routes are registered under the `/api` prefix.
All bodies and responses use **JSON** unless stated otherwise.
Most routes require a valid JWT (`Authorization: Bearer <token>`) — routes that do not are marked **public**.

---

## Users

### `/login`
**method:** POST · **public**
Authenticates a user and returns a JWT token plus the user info.

request body:
```json
{
  "email": "alex.jones@example.com",
  "password": "AAAAAAAA"
}
```

### `/user`
**method:** GET
Returns the list of all users in the database.

### `/user/<id>`
**method:** GET
Returns the user row with the given id.

### `/user/name:<name>`
**method:** GET
Returns the list of users whose firstname matches `name`.

### `/user/<name>/<surname>`
**method:** GET
Returns the user matching firstname and lastname.

### `/user/insert`
**method:** POST
Inserts a new user.

request body:
```json
{
  "email": "alex.jones@example.com",
  "password_hash": "AAAAAAAA",
  "role": "student",
  "firstname": "Alex",
  "lastname": "Jones",
  "id_institution": 42
}
```

### `/user/update`
**method:** POST
Updates an existing user. The body must contain the `id` of the user plus any field to change (`email`, `password_hash`, `firstname`, `lastname`, `id_institution`).

request body:
```json
{
  "id": 1,
  "email": "new@example.com",
  "firstname": "Alex"
}
```

### `/user/delete/<id>`
**method:** POST
Deletes the user with the given id. *WARNING: must be protected.*

### `/user/info/role`
**method:** GET · **public**
Returns the list of allowed user roles: `["student", "referent", "staff"]`.

---

## Applications

### `/applications`
**method:** GET
Returns the list of applications visible to the current user (filtered by role).

### `/applications/<application_id>`
**method:** PATCH
Updates the fields of an application (`year`, `semester`, `status`, `date_submitted`, `sending_institution`, `host_institution`). Scoped by role.

### `/application/insert`
**method:** POST · **role: student only**
Creates a new application and prepares the `uploads/applications/<id>/` directory.
This route only inserts data — file uploading is handled by `/application/document/upload`.

request body:
```json
{
  "year": 2026,
  "semester": "first",
  "referent_id": 12,
  "sending_institution": 1,
  "host_institution": 2,
  "notes": "optional"
}
```

### `/application/update/<id>`
**method:** POST
Updates fields of the application with the given id.

request body:
```json
{
  "status": "mobility_ongoing",
  "date_arrived": "2026-09-15",
  "date_departure": "2027-01-30"
}
```

### `/application/delete/<id>`
**method:** POST · **role: student, staff**
Deletes the application with the given id. Students can only delete their own.

### `/application/info/semester`
**method:** GET · **public**
Returns the list of allowed semester values: `["first", "second", "full"]`.

### `/application/info/status`
**method:** GET · **public**
Returns the list of allowed status values:
`["created", "learning_agreement_pending", "pre_departure_completed", "mobility_ongoing", "exam_recognition", "closed"]`.

### `/application/info/academic_years`
**method:** GET · **public**
Returns the list of academic years from the current year for 5 years (e.g. `[2026, 2027, 2028, 2029, 2030]`).

---

## Documents

### `/application/documents/<id>`
**method:** POST
Returns the list of uploaded documents associated to the application with the given id.

### `/application/document/insert`
**method:** POST
Inserts a new uploaded_document row.

request body:
```json
{
  "document_type": "learning_agreement",
  "file_path": "/backend/uploads/applications/3/la.pdf",
  "application_id": 3,
  "notes": ""
}
```

### `/application/document/upload`
**method:** POST · **multipart/form-data**
Uploads a file (form field `myfile`) into `uploads/applications/<application_id>/`.

form fields:
- `application_id` (text)
- `myfile` (file, from `<input type='file' name='myfile'>`)

### `/application/document/<id>/delete`
**method:** POST
Deletes the uploaded file from disk and removes the related row from the database.

### `/application/document/info/type`
**method:** GET · **public**
Returns the list of allowed document types: `["learning_agreement", "transcript"]`.

### `/application/document/info/status`
**method:** GET · **public**
Returns the list of allowed document status values: `["pending", "approved", "rejected"]`.

---

## Exams

### `/exam/list/<id_institution>`
**method:** GET
Returns the list of exams that belong to the given institution.

### `/exam/<id>`
**method:** GET
Returns the exam row with the given id.

### `/exam/insert`
**method:** POST
Inserts a new exam.

request body:
```json
{
  "code": "CM0XYZ",
  "name": "Database Systems",
  "credits": 6,
  "id_institution": 1
}
```

### `/exam/delete/<id>`
**method:** POST
Deletes the exam with the given id.

### `/exam/mapping/insert/<application_id>`
**method:** POST
Creates a new mapped_exams row for the application.

request body:
```json
{
  "host_exam_id": 10,
  "sending_exam_id": 22,
  "notes": "",
  "previous_id": -1
}
```

### `/exam/mapping/update/<id>`
**method:** POST
Updates the status (and notes) of the mapped exam with the given id. Sets `decision_date` to now.

request body:
```json
{
  "status": "approved",
  "notes": "ok"
}
```

### `/exam/mapping/passed/<id>`
**method:** POST
Registers grade and date passed for the mapped exam.

request body:
```json
{
  "grade": 28,
  "date_passed": "2027-01-20"
}
```

### `/exam/mapped/info/status`
**method:** GET · **public**
Returns the list of allowed status values for mapped exams: `["pending", "approved", "rejected"]`.

---

## Institutions

### `/institution/insert`
**method:** POST · **role: staff only**
Inserts a new institution row.

request body:
```json
{
  "name": "Ca Foscari",
  "country": "Italy",
  "city": "Venice"
}
```

### `/institution/update/<id>`
**method:** POST · **role: staff only**
Updates an existing institution.

request body:
```json
{
  "name": "New Name",
  "country": "Italy",
  "city": "Venice"
}
```

### `/institution/delete/<id>`
**method:** POST · **role: staff only**
Deletes the institution row with the given id.

### `/institution/<id_institution>/partners`
**method:** GET
Returns the list of partner institutions linked to the given institution.

### `/institution/<id>/referents`
**method:** GET
Returns the list of referents (users with role=referent) associated to the institution.

### `/institution/<id>/students`
**method:** GET
Returns the list of students associated to the institution.

### `/institution/<id>/staff`
**method:** GET
Returns the list of staff members associated to the institution.

### `/institution/<id>/exams`
**method:** GET
Returns the list of all exams associated to the institution.

### `/institution/partner/insert`
**method:** POST
Creates a new partner_institution mapping.

request body:
```json
{
  "id_institution": 1,
  "id_partner_institution": 2
}
```

### `/institution/partner/<id>/delete`
**method:** POST
Deletes the partner_institution mapping with the given row id.

### `/institution/partner/<id>/update`
**method:** POST
Updates the partner_institution mapping with the given row id.

request body:
```json
{
  "id_institution": 1,
  "id_partner_institution": 3
}
```

---

## Misc / Health

### `/` (app.py)
**method:** GET · **public**
Health check. Returns the connected database name.

### `/api/health`
**method:** GET · **public**
Returns database info and row counts for users / institutions / applications / exams.

### `/api/summary`
**method:** GET
Returns counts, the 5 most recent applications, and the top 5 institutions by partner count.

### `/api/institutions`
**method:** GET
Returns the list of institutions with partner counts.

### `/api/exams`
**method:** GET
Returns the list of exams joined with their institution.
