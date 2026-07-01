--
-- PostgreSQL database dump
--

\restrict 08onwZCvhM0ELc7ygGxFrMtvoF6daOY9GBFJ4haoQkTuLbyexsQt79Y5BrtIBoR

-- Dumped from database version 17.10
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: check_application_close(); Type: FUNCTION; Schema: public; Owner: myuser
--

CREATE FUNCTION public.check_application_close() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.status = 'closed' THEN
        IF NOT EXISTS (
            SELECT 1
            FROM uploaded_documents
            WHERE application_id = NEW.id
              AND document_type = 'transcript'
              AND status = 'approved'
        ) THEN
            RAISE EXCEPTION 'cannot close application without an approved transcript of records';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM mapped_exams
            WHERE application_id = NEW.id
              AND status <> 'approved'
        ) THEN
            RAISE EXCEPTION 'cannot close application: all mapped exams must be approved';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.check_application_close() OWNER TO myuser;

--
-- Name: check_application_data(); Type: FUNCTION; Schema: public; Owner: myuser
--

CREATE FUNCTION public.check_application_data() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
	-- valid referent, institution is checked by existing constraint
	IF NEW.referent_id IS NOT NULL AND NOT EXISTS(
		SELECT 1 
        FROM users
        WHERE id = NEW.referent_id 
		AND role='referent' 
	) THEN 
        RAISE EXCEPTION 'application referent must have role=referent';
	END IF;

-- valid student, institution is checked by existing constraint
	IF NOT EXISTS(
		SELECT 1
		FROM users
		WHERE id=NEW.user_id
		AND role='student'
	) THEN
        RAISE EXCEPTION 'application student must have role=student';
	END IF;

	-- student cannot create a application that is already past all the LA & exams validation process
	IF TG_OP='INSERT' AND NEW.status NOT IN('created','learning_agreement_pending') THEN
		RAISE EXCEPTION 'application status cannot start with %', NEW.status;
	END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.check_application_data() OWNER TO myuser;

--
-- Name: check_application_status_workflow(); Type: FUNCTION; Schema: public; Owner: myuser
--

CREATE FUNCTION public.check_application_status_workflow() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN

	-- learning_agreement_pending -> pre_departure_completed
	IF NEW.status='pre_departure_completed' AND OLD.status='learning_agreement_pending' THEN
		-- check if associated learning agreement exists and has been approved
		IF NOT EXISTS ( SELECT 1 
				FROM uploaded_documents
				WHERE application_id=NEW.id 
				AND document_type='learning_agreement'
				AND status='approved'
			) THEN
			RAISE EXCEPTION 'approved learning agreement for the application is required';
		END IF;

		-- check if mapped exams exists and are all approved (search for at least 1 that has not been approved)
		IF EXISTS (SELECT 1
			FROM mapped_exams
			WHERE application_id=NEW.id
			AND status<>'approved'
			) THEN
			RAISE EXCEPTION 'all mapped exams of the application must be approved';
		END IF;
	ELSE 
		RAISE EXCEPTION 'application status cannot pass from % -> %', OLD.status, NEW.status;
	END IF;

	-- pre_departure_completed -> mobility_ongoing
	IF NEW.status='mobility_ongoing' AND OLD.status<>'pre_departure_completed' THEN
		RAISE EXCEPTION 'application status cannot pass from % -> %', OLD.status, NEW.status;
	END IF;
	
	-- mobility_ongoing -> exam_recognition
	IF NEW.status='exam_recognition' AND OLD.status<>'mobility_ongoing' THEN
		RAISE EXCEPTION 'application status cannot pass from % -> %', OLD.status, NEW.status;
	END IF;

	IF NEW.status='closed' AND OLD.status='exam_recognition' THEN
		-- check uploaded transcript of records, if it exists and has been approved
		IF NOT EXISTS (SELECT 1
			FROM uploaded_documents
			WHERE application_id=NEW.id
			AND document_type='transcript'
			AND status='approved'
			) THEN
			RAISE EXCEPTION 'approved transcript of records required';
		END IF;

		-- check if all mapped_exams are graded (if exists at least 1 that has no grade)
		IF EXISTS(SELECT 1
				FROM mapped_exams
				WHERE application_id=NEW.id
				AND grade IS NULL OR grade=-1
			) THEN
			RAISE EXCEPTION 'all exams must requre a grade';
		END IF;
	ELSE
		RAISE EXCEPTION 'application status cannot pass from % -> %', OLD.status, NEW.status;
	END IF;

	RETURN NEW;
END;
$$;


ALTER FUNCTION public.check_application_status_workflow() OWNER TO myuser;

--
-- Name: check_document_status_update(); Type: FUNCTION; Schema: public; Owner: myuser
--

CREATE FUNCTION public.check_document_status_update() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
	app_status VARCHAR(32);
BEGIN
	SELECT status INTO app_status
	FROM applications
	WHERE id = NEW.application_id;

    IF NEW.status IN ('approved', 'rejected') THEN
		-- prevent status change when application is not in adequate status 
		IF NEW.document_type='learning_agreement' THEN
			IF app_status NOT IN ('created','learning_agreement_pending') THEN
				RAISE EXCEPTION 'cannot change exam status when associated application is in % status', app_status;
			END IF;
		END IF;
		IF NEW.document_type='transcript' THEN
			IF app_status <> 'exam_recognition' THEN
				RAISE EXCEPTION 'cannot change exam status when associated application is in % status', app_status;
			END IF;
		END IF;

        NEW.decision_date := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.check_document_status_update() OWNER TO myuser;

--
-- Name: check_mapped_exam_institutions(); Type: FUNCTION; Schema: public; Owner: myuser
--

CREATE FUNCTION public.check_mapped_exam_institutions() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    app_host_inst       INT;
    app_sending_inst    INT;
    host_exam_inst      INT;
    sending_exam_inst   INT;
BEGIN
    SELECT host_institution, sending_institution
        INTO app_host_inst, app_sending_inst
        FROM applications
        WHERE id = NEW.application_id;

    SELECT id_institution INTO host_exam_inst
        FROM exams WHERE id = NEW.host_exam_id;

    SELECT id_institution INTO sending_exam_inst
        FROM exams WHERE id = NEW.sending_exam_id;

	-- this can be possible through an independent insert
    IF host_exam_inst <> app_host_inst THEN
        RAISE EXCEPTION 'host_exam_id institution does not match application host_institution';
    END IF;

	-- this can be possible through an independent insert
    IF sending_exam_inst <> app_sending_inst THEN
        RAISE EXCEPTION 'sending_exam_id institution does not match application sending_institution';
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.check_mapped_exam_institutions() OWNER TO myuser;

--
-- Name: check_update_status_mapped_exams(); Type: FUNCTION; Schema: public; Owner: myuser
--

CREATE FUNCTION public.check_update_status_mapped_exams() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
	app_status VARCHAR(32);
BEGIN
    IF NEW.status IN ('approved', 'rejected') THEN
		-- check if the application is on status 'learning_agreement_pending' or 'created'
		SELECT status INTO app_status
		FROM applications
		WHERE id = NEW.application_id;
		IF app_status NOT IN ('created','learning_agreement_pending') THEN
			RAISE EXCEPTION 'cannot change exam status when associated application is in % status', app_status;
		END IF;

        NEW.decision_date := CURRENT_TIMESTAMP;
    END IF;


    RETURN NEW;
END;
$$;


ALTER FUNCTION public.check_update_status_mapped_exams() OWNER TO myuser;

--
-- Name: mirror_partner_institution(); Type: FUNCTION; Schema: public; Owner: myuser
--

CREATE FUNCTION public.mirror_partner_institution() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM partner_institution
        WHERE id_institution = NEW.id_partner_institution
          AND id_partner_institution = NEW.id_institution
    ) THEN
        INSERT INTO partner_institution (id_institution, id_partner_institution)
            VALUES (NEW.id_partner_institution, NEW.id_institution);
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.mirror_partner_institution() OWNER TO myuser;

--
-- Name: update_application_on_upload(); Type: FUNCTION; Schema: public; Owner: myuser
--

CREATE FUNCTION public.update_application_on_upload() RETURNS trigger
    LANGUAGE plpgsql
    AS $$ 
DECLARE
	app_status VARCHAR(32);
BEGIN
	SELECT status 
		INTO app_status
		FROM applications
		WHERE id = NEW.application_id;

	IF NEW.document_type = 'learning_agreement' THEN
		-- check if the status of associated applicaiton is valid
		IF app_status NOT IN ('created','learning_agreement_pending') THEN
			RAISE EXCEPTION 'new learning agreement document cannot be changed while the application is in % status', app_status;
		END IF;

		IF app_status = 'created' THEN
			UPDATE applications SET status='learning_agreement_pending' WHERE id=NEW.application_id;
		END IF;
	ELSE
		-- if it's not a LA, it must be a transcript of records (because of check constraint), check if the status of associated application is valid
		IF app_status <> 'exam_recognition' THEN
			RAISE EXCEPTION 'new transcript of records document cannot be changed while the application is in % status', app_status;
		END IF;
	END IF;

	RETURN NEW;
END
$$;


ALTER FUNCTION public.update_application_on_upload() OWNER TO myuser;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO myuser;

--
-- Name: applications; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.applications (
    id integer NOT NULL,
    year integer NOT NULL,
    semester character varying(50) NOT NULL,
    status character varying(32) NOT NULL,
    date_submitted timestamp with time zone,
    sending_institution integer NOT NULL,
    host_institution integer NOT NULL,
    user_id integer NOT NULL,
    date_arrived date,
    date_departure date,
    notes text,
    referent_id integer,
    CONSTRAINT valid_ongoing CHECK ((NOT (((status)::text = 'mobility_ongoing'::text) AND (date_arrived IS NULL)))),
    CONSTRAINT valid_recognition CHECK ((NOT (((status)::text = 'exam_recognition'::text) AND (date_departure IS NULL))))
);


ALTER TABLE public.applications OWNER TO myuser;

--
-- Name: applications_id_seq; Type: SEQUENCE; Schema: public; Owner: myuser
--

CREATE SEQUENCE public.applications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.applications_id_seq OWNER TO myuser;

--
-- Name: applications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: myuser
--

ALTER SEQUENCE public.applications_id_seq OWNED BY public.applications.id;


--
-- Name: exams; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.exams (
    id integer NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(255) NOT NULL,
    credits integer NOT NULL,
    id_institution integer NOT NULL
);


ALTER TABLE public.exams OWNER TO myuser;

--
-- Name: exams_id_seq; Type: SEQUENCE; Schema: public; Owner: myuser
--

CREATE SEQUENCE public.exams_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.exams_id_seq OWNER TO myuser;

--
-- Name: exams_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: myuser
--

ALTER SEQUENCE public.exams_id_seq OWNED BY public.exams.id;


--
-- Name: institutions; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.institutions (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    country character varying(255) NOT NULL,
    city character varying(255) NOT NULL
);


ALTER TABLE public.institutions OWNER TO myuser;

--
-- Name: partner_institution; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.partner_institution (
    id integer NOT NULL,
    id_institution integer NOT NULL,
    id_partner_institution integer NOT NULL
);


ALTER TABLE public.partner_institution OWNER TO myuser;

--
-- Name: institution_partner_count_view; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.institution_partner_count_view AS
 SELECT i.id,
    i.name,
    i.country,
    i.city,
    count(pi.id) AS partner_count
   FROM (public.institutions i
     LEFT JOIN public.partner_institution pi ON ((pi.id_institution = i.id)))
  GROUP BY i.id, i.name, i.country, i.city;


ALTER VIEW public.institution_partner_count_view OWNER TO myuser;

--
-- Name: institutions_id_seq; Type: SEQUENCE; Schema: public; Owner: myuser
--

CREATE SEQUENCE public.institutions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.institutions_id_seq OWNER TO myuser;

--
-- Name: institutions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: myuser
--

ALTER SEQUENCE public.institutions_id_seq OWNED BY public.institutions.id;


--
-- Name: mapped_exams; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.mapped_exams (
    id integer NOT NULL,
    application_id integer NOT NULL,
    date_passed date,
    grade integer,
    status character varying(32) NOT NULL,
    decision_date timestamp with time zone,
    notes text,
    previous_id integer NOT NULL,
    host_exam_id integer NOT NULL,
    sending_exam_id integer NOT NULL
);


ALTER TABLE public.mapped_exams OWNER TO myuser;

--
-- Name: mapped_exams_id_seq; Type: SEQUENCE; Schema: public; Owner: myuser
--

CREATE SEQUENCE public.mapped_exams_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.mapped_exams_id_seq OWNER TO myuser;

--
-- Name: mapped_exams_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: myuser
--

ALTER SEQUENCE public.mapped_exams_id_seq OWNED BY public.mapped_exams.id;


--
-- Name: mv_applications_by_host_institution; Type: MATERIALIZED VIEW; Schema: public; Owner: myuser
--

CREATE MATERIALIZED VIEW public.mv_applications_by_host_institution AS
 SELECT hi.id AS host_institution_id,
    hi.name AS host_institution_name,
    hi.country AS host_institution_country,
    count(a.id) AS applications_count
   FROM (public.applications a
     JOIN public.institutions hi ON ((hi.id = a.host_institution)))
  GROUP BY hi.id, hi.name, hi.country
  WITH NO DATA;


ALTER MATERIALIZED VIEW public.mv_applications_by_host_institution OWNER TO myuser;

--
-- Name: mv_applications_by_status; Type: MATERIALIZED VIEW; Schema: public; Owner: myuser
--

CREATE MATERIALIZED VIEW public.mv_applications_by_status AS
 SELECT status,
    count(*) AS applications_count
   FROM public.applications
  GROUP BY status
  WITH NO DATA;


ALTER MATERIALIZED VIEW public.mv_applications_by_status OWNER TO myuser;

--
-- Name: users; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role character varying(50) NOT NULL,
    firstname character varying(255) NOT NULL,
    lastname character varying(255) NOT NULL,
    id_institution integer NOT NULL
);


ALTER TABLE public.users OWNER TO myuser;

--
-- Name: mv_institution_activity; Type: MATERIALIZED VIEW; Schema: public; Owner: myuser
--

CREATE MATERIALIZED VIEW public.mv_institution_activity AS
 SELECT id AS institution_id,
    name,
    country,
    city,
    ( SELECT count(*) AS count
           FROM public.users u
          WHERE ((u.id_institution = i.id) AND ((u.role)::text = 'student'::text))) AS students_count,
    ( SELECT count(*) AS count
           FROM public.users u
          WHERE ((u.id_institution = i.id) AND ((u.role)::text = 'staff'::text))) AS staff_count,
    ( SELECT count(*) AS count
           FROM public.users u
          WHERE ((u.id_institution = i.id) AND ((u.role)::text = 'referent'::text))) AS referents_count,
    ( SELECT count(*) AS count
           FROM public.exams e
          WHERE (e.id_institution = i.id)) AS exams_count,
    ( SELECT count(*) AS count
           FROM public.applications a
          WHERE (a.sending_institution = i.id)) AS sent_applications,
    ( SELECT count(*) AS count
           FROM public.applications a
          WHERE (a.host_institution = i.id)) AS hosted_applications,
    ( SELECT count(*) AS count
           FROM public.partner_institution pi
          WHERE (pi.id_institution = i.id)) AS partners_count
   FROM public.institutions i
  WITH NO DATA;


ALTER MATERIALIZED VIEW public.mv_institution_activity OWNER TO myuser;

--
-- Name: partner_institution_id_seq; Type: SEQUENCE; Schema: public; Owner: myuser
--

CREATE SEQUENCE public.partner_institution_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.partner_institution_id_seq OWNER TO myuser;

--
-- Name: partner_institution_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: myuser
--

ALTER SEQUENCE public.partner_institution_id_seq OWNED BY public.partner_institution.id;


--
-- Name: uploaded_documents; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.uploaded_documents (
    id integer NOT NULL,
    document_type character varying(50) NOT NULL,
    file_path character varying(255) NOT NULL,
    user_id integer NOT NULL,
    application_id integer NOT NULL,
    date_updated timestamp with time zone DEFAULT now() NOT NULL,
    status character varying(32) NOT NULL,
    decision_date timestamp with time zone,
    notes text
);


ALTER TABLE public.uploaded_documents OWNER TO myuser;

--
-- Name: uploaded_documents_id_seq; Type: SEQUENCE; Schema: public; Owner: myuser
--

CREATE SEQUENCE public.uploaded_documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.uploaded_documents_id_seq OWNER TO myuser;

--
-- Name: uploaded_documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: myuser
--

ALTER SEQUENCE public.uploaded_documents_id_seq OWNED BY public.uploaded_documents.id;


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: myuser
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO myuser;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: myuser
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: applications id; Type: DEFAULT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.applications ALTER COLUMN id SET DEFAULT nextval('public.applications_id_seq'::regclass);


--
-- Name: exams id; Type: DEFAULT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.exams ALTER COLUMN id SET DEFAULT nextval('public.exams_id_seq'::regclass);


--
-- Name: institutions id; Type: DEFAULT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.institutions ALTER COLUMN id SET DEFAULT nextval('public.institutions_id_seq'::regclass);


--
-- Name: mapped_exams id; Type: DEFAULT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.mapped_exams ALTER COLUMN id SET DEFAULT nextval('public.mapped_exams_id_seq'::regclass);


--
-- Name: partner_institution id; Type: DEFAULT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.partner_institution ALTER COLUMN id SET DEFAULT nextval('public.partner_institution_id_seq'::regclass);


--
-- Name: uploaded_documents id; Type: DEFAULT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.uploaded_documents ALTER COLUMN id SET DEFAULT nextval('public.uploaded_documents_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: myuser
--

COPY public.alembic_version (version_num) FROM stdin;
00cd7fdc75d9
\.


--
-- Data for Name: applications; Type: TABLE DATA; Schema: public; Owner: myuser
--

COPY public.applications (id, year, semester, status, date_submitted, sending_institution, host_institution, user_id, date_arrived, date_departure, notes, referent_id) FROM stdin;
9	2026	full	closed	\N	1	5	1	2026-06-17	2026-06-23		51
5	2026	first	closed	\N	1	5	1	2026-06-14	2026-06-24		50
\.


--
-- Data for Name: exams; Type: TABLE DATA; Schema: public; Owner: myuser
--

COPY public.exams (id, code, name, credits, id_institution) FROM stdin;
1	MIT-CS0101	Distributed Systems	9	1
2	MIT-CS0102	Compilers	9	1
3	MIT-CS0103	Operating Systems	6	1
4	MIT-CS0104	Algorithm Design	9	1
5	MIT-CS0105	Computer Architecture	6	1
6	ETH-CS0201	Formal Methods	6	2
7	ETH-CS0202	Logic Programming	6	2
8	ETH-CS0203	Type Theory	6	2
9	ETH-CS0204	Cryptography	6	2
10	ETH-CS0205	Parallel Computing	6	2
11	TUBERLIN-CS0301	Embedded Systems	12	3
12	TUBERLIN-CS0302	Real-Time Systems	9	3
13	TUBERLIN-CS0303	Digital Signal Processing	9	3
14	TUBERLIN-CS0304	Control Theory	12	3
15	TUBERLIN-CS0305	Hardware Design	12	3
16	EPFL-CS0401	Machine Learning	9	4
17	EPFL-CS0402	Neural Networks	6	4
18	EPFL-CS0403	Computer Vision	9	4
19	EPFL-CS0404	Data Mining	9	4
20	EPFL-CS0405	Probabilistic Graphical Models	6	4
21	KULEUVEN-CS0501	Software Engineering	9	5
22	KULEUVEN-CS0502	Design Patterns	12	5
23	KULEUVEN-CS0503	Agile Methods	9	5
24	KULEUVEN-CS0504	Testing & Verification	9	5
25	KULEUVEN-CS0505	DevOps	6	5
26	POLIMI-CS0601	Web Engineering	6	6
27	POLIMI-CS0602	Cloud Computing	9	6
28	POLIMI-CS0603	Microservices	12	6
29	POLIMI-CS0604	REST API Design	6	6
30	POLIMI-CS0605	Containerization	6	6
31	TUDELFT-CS0701	Cybersecurity	9	7
32	TUDELFT-CS0702	Network Security	12	7
33	TUDELFT-CS0703	Ethical Hacking	6	7
34	TUDELFT-CS0704	Digital Forensics	9	7
35	TUDELFT-CS0705	Malware Analysis	6	7
36	UPC-CS0801	Database Systems	6	8
37	UPC-CS0802	Query Optimization	12	8
38	UPC-CS0803	NoSQL Systems	9	8
39	UPC-CS0804	Data Warehousing	12	8
40	UPC-CS0805	Transaction Management	6	8
41	ULIEGE-CS0901	Human-Computer Interaction	9	9
42	ULIEGE-CS0902	UX Design	6	9
43	ULIEGE-CS0903	Accessibility	9	9
44	ULIEGE-CS0904	Cognitive Ergonomics	6	9
45	ULIEGE-CS0905	Interaction Prototyping	6	9
46	AALTO-CS1001	Mobile Computing	9	10
47	AALTO-CS1002	IoT Systems	6	10
48	AALTO-CS1003	Edge Computing	9	10
49	AALTO-CS1004	Wireless Protocols	6	10
50	AALTO-CS1005	Sensor Networks	6	10
51	DTU-CS1101	Computer Graphics	9	11
52	DTU-CS1102	3D Rendering	6	11
53	DTU-CS1103	Game Engine Design	9	11
54	DTU-CS1104	Shader Programming	9	11
55	DTU-CS1105	Geometric Modeling	6	11
56	UPPSALA-CS1201	Bioinformatics	9	12
57	UPPSALA-CS1202	Computational Genomics	9	12
58	UPPSALA-CS1203	Protein Modeling	6	12
59	UPPSALA-CS1204	Medical Imaging	6	12
60	UPPSALA-CS1205	Health Informatics	6	12
61	UWARSAW-CS1301	Quantum Computing	6	13
62	UWARSAW-CS1302	Quantum Algorithms	12	13
63	UWARSAW-CS1303	Post-Quantum Cryptography	6	13
64	UWARSAW-CS1304	Quantum Error Correction	12	13
65	UWARSAW-CS1305	Quantum Programming	9	13
66	ULJUBLJANA-CS1401	Robotics	9	14
67	ULJUBLJANA-CS1402	Motion Planning	6	14
68	ULJUBLJANA-CS1403	Computer Vision for Robotics	9	14
69	ULJUBLJANA-CS1404	ROS Programming	12	14
70	ULJUBLJANA-CS1405	Autonomous Systems	6	14
71	ELTE-CS1501	Natural Language Processing	6	15
72	ELTE-CS1502	Speech Recognition	6	15
73	ELTE-CS1503	Information Retrieval	6	15
74	ELTE-CS1504	Text Mining	6	15
75	ELTE-CS1505	Computational Linguistics	9	15
76	UOULU-CS1601	High-Performance Computing	12	16
77	UOULU-CS1602	GPU Programming	9	16
78	UOULU-CS1603	Cluster Computing	6	16
79	UOULU-CS1604	Scientific Computing	9	16
80	UOULU-CS1605	Numerical Methods	12	16
81	AGH-CS1701	Network Engineering	6	17
82	AGH-CS1702	Routing Protocols	6	17
83	AGH-CS1703	SDN	6	17
84	AGH-CS1704	Network Virtualization	9	17
85	AGH-CS1705	5G Systems	6	17
86	UPORTO-CS1801	Functional Programming	9	18
87	UPORTO-CS1802	Haskell	6	18
88	UPORTO-CS1803	Scala	6	18
89	UPORTO-CS1804	Category Theory for CS	9	18
90	UPORTO-CS1805	Lambda Calculus	9	18
91	UGHENT-CS1901	Systems Programming	6	19
92	UGHENT-CS1902	Rust Programming	6	19
93	UGHENT-CS1903	Memory Safety	12	19
94	UGHENT-CS1904	Low-Level Optimization	6	19
95	UGHENT-CS1905	Linkers & Loaders	9	19
96	UBOLOGNA-CS2001	Data Science	6	20
97	UBOLOGNA-CS2002	Statistical Learning	9	20
98	UBOLOGNA-CS2003	Big Data Processing	9	20
99	UBOLOGNA-CS2004	Data Visualization	6	20
100	UBOLOGNA-CS2005	Feature Engineering	6	20
\.


--
-- Data for Name: institutions; Type: TABLE DATA; Schema: public; Owner: myuser
--

COPY public.institutions (id, name, country, city) FROM stdin;
1	Ca' Foscari University of Venice	Italy	Venice
2	Sorbonne University	France	Paris
3	Ludwig Maximilian University of Munich	Germany	Munich
4	University of Oxford	England	Oxford
5	University of Amsterdam	Netherlands	Amsterdam
6	ETH Zurich	Switzerland	Zurich
7	Complutense University of Madrid	Spain	Madrid
8	University of Warsaw	Poland	Warsaw
9	Charles University	Czech Republic	Prague
10	KU Leuven	Belgium	Leuven
11	University of Vienna	Austria	Vienna
12	University of Helsinki	Finland	Helsinki
13	Stockholm University	Sweden	Stockholm
14	University of Copenhagen	Denmark	Copenhagen
15	University of Oslo	Norway	Oslo
16	University of Lisbon	Portugal	Lisbon
17	University of Athens	Greece	Athens
18	Eötvös Loránd University	Hungary	Budapest
19	University of Bucharest	Romania	Bucharest
20	University of Zagreb	Croatia	Zagreb
\.


--
-- Data for Name: mapped_exams; Type: TABLE DATA; Schema: public; Owner: myuser
--

COPY public.mapped_exams (id, application_id, date_passed, grade, status, decision_date, notes, previous_id, host_exam_id, sending_exam_id) FROM stdin;
69	9	\N	-1	approved	2026-06-21 19:04:11.246943+00		-1	22	3
70	9	\N	-1	approved	2026-06-22 20:05:05.08656+00	a	-1	25	5
71	9	\N	-1	approved	2026-06-22 20:05:06.501595+00	atat	-1	23	1
68	9	\N	-1	approved	2026-06-22 20:06:36.905624+00		-1	21	2
67	5	\N	-1	approved	2026-06-22 21:11:47.752494+00		-1	21	4
66	5	\N	-1	approved	2026-06-22 21:11:48.48415+00		-1	22	5
\.


--
-- Data for Name: partner_institution; Type: TABLE DATA; Schema: public; Owner: myuser
--

COPY public.partner_institution (id, id_institution, id_partner_institution) FROM stdin;
1	1	3
2	1	4
3	1	5
4	1	6
5	1	7
6	2	5
7	2	6
8	2	10
9	2	18
10	2	19
11	3	11
12	3	16
13	3	17
14	4	9
15	4	12
16	4	13
17	4	16
18	5	11
19	5	16
20	5	17
21	6	11
22	6	13
23	6	20
24	7	10
25	7	14
26	7	16
27	8	15
28	8	20
29	9	15
30	9	17
31	10	13
32	11	12
33	11	15
34	12	17
35	12	20
36	13	18
37	13	19
38	14	16
\.


--
-- Data for Name: uploaded_documents; Type: TABLE DATA; Schema: public; Owner: myuser
--

COPY public.uploaded_documents (id, document_type, file_path, user_id, application_id, date_updated, status, decision_date, notes) FROM stdin;
20	learning_agreement	/home/fr1g0/dev/ProgettoBD/backend/uploads/applications/9/JOSEPH_FRIGO_learning-agreement-studies.pdf	1	9	2026-06-21 19:03:05.540362+00	approved	2026-06-22 20:05:08.34024+00	aa
21	transcript	/home/fr1g0/dev/ProgettoBD/backend/uploads/applications/9/Bando_Unico_DJD_2025_def.pdf	1	9	2026-06-22 21:00:18.156059+00	approved	2026-06-22 21:10:27.34826+00	sd
19	learning_agreement	/home/fr1g0/dev/ProgettoBD/backend/uploads/applications/5/(OLD)FRIGO_JOSEPH_Learning_Agreement.pdf	1	5	2026-06-21 17:45:39.543985+00	approved	2026-06-22 21:11:49.346143+00	
22	transcript	/home/fr1g0/dev/ProgettoBD/backend/uploads/applications/5/StampaAutocertificazione.pdf	1	5	2026-06-22 21:13:17.098005+00	approved	2026-06-22 21:14:12.625443+00	
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: myuser
--

COPY public.users (id, email, password_hash, role, firstname, lastname, id_institution) FROM stdin;
1	marco.rossi@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Marco	Rossi	1
2	giulia.ferrari@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Giulia	Ferrari	1
3	luca.bianchi@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Luca	Bianchi	1
4	sofia.romano@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Sofia	Romano	1
5	matteo.conti@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Matteo	Conti	1
6	elena.ricci@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Elena	Ricci	1
7	davide.marino@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Davide	Marino	1
8	chiara.greco@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Chiara	Greco	1
9	andrea.bruno@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Andrea	Bruno	1
10	valentina.gallo@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Valentina	Gallo	1
11	pierre.martin@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Pierre	Martin	2
12	camille.durand@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Camille	Durand	2
13	hans.mueller@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Hans	Mueller	3
14	anna.schmidt@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Anna	Schmidt	3
15	james.smith@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	James	Smith	4
16	emily.jones@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Emily	Jones	4
17	lars.janssen@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Lars	Janssen	5
18	sophie.vandenberg@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Sophie	Vandenberg	5
19	felix.keller@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Felix	Keller	6
20	nina.brunner@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Nina	Brunner	6
21	carlos.garcia@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Carlos	Garcia	7
22	lucia.fernandez@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Lucia	Fernandez	7
23	piotr.kowalski@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Piotr	Kowalski	8
24	katarzyna.nowak@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Katarzyna	Nowak	8
25	jan.novak@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Jan	Novak	9
26	petra.dvorak@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Petra	Dvorak	9
27	pieter.desmet@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Pieter	Desmet	10
28	elien.claes@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Elien	Claes	10
29	stefan.huber@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Stefan	Huber	11
30	lisa.wagner@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Lisa	Wagner	11
31	mikko.virtanen@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Mikko	Virtanen	12
32	aino.makinen@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Aino	Makinen	12
33	erik.lindqvist@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Erik	Lindqvist	13
34	maja.johansson@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Maja	Johansson	13
35	rasmus.nielsen@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Rasmus	Nielsen	14
36	ida.andersen@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Ida	Andersen	14
37	olav.berg@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Olav	Berg	15
38	ingrid.hansen@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Ingrid	Hansen	15
39	joao.silva@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	João	Silva	16
40	ana.costa@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Ana	Costa	16
41	nikos.papadopoulos@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Nikos	Papadopoulos	17
42	eleni.georgiou@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Eleni	Georgiou	17
43	balazs.nagy@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Balázs	Nagy	18
44	reka.kovacs@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Réka	Kovács	18
45	andrei.popescu@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Andrei	Popescu	19
46	ioana.ionescu@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Ioana	Ionescu	19
47	luka.horvat@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Luka	Horvat	20
48	ana.maric@stud.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	student	Ana	Marić	20
49	giovanni.ferrari@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Giovanni	Ferrari	1
50	laura.bianchi@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Laura	Bianchi	1
51	carlo.rossi@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Carlo	Rossi	1
52	jean.dupont@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Jean	Dupont	2
53	marie.leroy@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Marie	Leroy	2
54	thomas.bauer@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Thomas	Bauer	3
55	julia.richter@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Julia	Richter	3
56	william.taylor@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	William	Taylor	4
57	sarah.wright@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Sarah	Wright	4
58	jan.dekker@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Jan	Dekker	5
59	maria.berg@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Maria	Berg	6
60	pedro.alves@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Pedro	Alves	7
61	agnieszka.wisniewska@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Agnieszka	Wiśniewska	8
62	tomas.blazek@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Tomáš	Blažek	9
63	inge.willems@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Inge	Willems	10
64	markus.gruber@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Markus	Gruber	11
65	sari.heikkinen@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Sari	Heikkinen	12
66	anders.svensson@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Anders	Svensson	13
67	anne.christensen@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Anne	Christensen	14
68	kari.olsen@prof.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	referent	Kari	Olsen	15
69	giuseppe.verdi@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Giuseppe	Verdi	1
70	anna.colombo@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Anna	Colombo	1
71	roberto.mancini@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Roberto	Mancini	1
72	claire.moreau@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Claire	Moreau	2
73	francois.simon@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	François	Simon	2
74	klaus.zimmer@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Klaus	Zimmer	3
75	heike.fischer@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Heike	Fischer	3
76	oliver.brown@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Oliver	Brown	4
77	charlotte.davies@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Charlotte	Davies	4
78	emma.visser@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Emma	Visser	5
79	david.meier@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	David	Meier	6
80	carmen.ruiz@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Carmen	Ruiz	7
81	marek.wojcik@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Marek	Wójcik	8
82	lenka.horakova@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Lenka	Horáková	9
83	thomas.claes@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Thomas	Claes	10
84	monika.fischer@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Monika	Fischer	11
85	paivi.leinonen@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Päivi	Leinonen	12
86	per.nilsson@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Per	Nilsson	13
87	mette.larsen@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Mette	Larsen	14
88	sigrid.dahl@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Sigrid	Dahl	15
89	rui.ferreira@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Rui	Ferreira	16
90	stavros.alexiou@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Stavros	Alexiou	17
91	zoltan.fekete@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Zoltán	Fekete	18
92	mihai.dinu@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Mihai	Dinu	19
93	tomislav.babic@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Tomislav	Babić	20
94	katia.lombardi@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Katia	Lombardi	16
95	nuno.santos@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Nuno	Santos	17
96	george.pappas@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	George	Pappas	18
97	diana.stoica@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Diana	Stoica	19
98	ivana.petrovic@staff.uni.com	pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff	staff	Ivana	Petrović	20
\.


--
-- Name: applications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.applications_id_seq', 9, true);


--
-- Name: exams_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.exams_id_seq', 100, true);


--
-- Name: institutions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.institutions_id_seq', 1, false);


--
-- Name: mapped_exams_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.mapped_exams_id_seq', 71, true);


--
-- Name: partner_institution_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.partner_institution_id_seq', 38, true);


--
-- Name: uploaded_documents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.uploaded_documents_id_seq', 22, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.users_id_seq', 98, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: applications applications_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_pkey PRIMARY KEY (id);


--
-- Name: exams exams_code_id_institution_key; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.exams
    ADD CONSTRAINT exams_code_id_institution_key UNIQUE (code, id_institution);


--
-- Name: exams exams_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.exams
    ADD CONSTRAINT exams_pkey PRIMARY KEY (id);


--
-- Name: institutions institutions_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.institutions
    ADD CONSTRAINT institutions_pkey PRIMARY KEY (id);


--
-- Name: mapped_exams mapped_exams_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.mapped_exams
    ADD CONSTRAINT mapped_exams_pkey PRIMARY KEY (id);


--
-- Name: mapped_exams mapped_exams_unique_application_id_host_exam_id; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.mapped_exams
    ADD CONSTRAINT mapped_exams_unique_application_id_host_exam_id UNIQUE (application_id, host_exam_id);


--
-- Name: mapped_exams mapped_exams_unique_application_id_sending_exam_id; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.mapped_exams
    ADD CONSTRAINT mapped_exams_unique_application_id_sending_exam_id UNIQUE (application_id, sending_exam_id);


--
-- Name: partner_institution partner_institution_id_institution_id_partner_institution_key; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.partner_institution
    ADD CONSTRAINT partner_institution_id_institution_id_partner_institution_key UNIQUE (id_institution, id_partner_institution);


--
-- Name: partner_institution partner_institution_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.partner_institution
    ADD CONSTRAINT partner_institution_pkey PRIMARY KEY (id);


--
-- Name: uploaded_documents uploaded_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.uploaded_documents
    ADD CONSTRAINT uploaded_documents_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_id_id_institution_key; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_id_id_institution_key UNIQUE (id, id_institution);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_applications_date_submitted_desc; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_applications_date_submitted_desc ON public.applications USING btree (date_submitted DESC);


--
-- Name: idx_applications_host_institution; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_applications_host_institution ON public.applications USING btree (host_institution);


--
-- Name: idx_applications_referent_id; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_applications_referent_id ON public.applications USING btree (referent_id);


--
-- Name: idx_applications_sending_institution; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_applications_sending_institution ON public.applications USING btree (sending_institution);


--
-- Name: idx_applications_status; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_applications_status ON public.applications USING btree (status);


--
-- Name: idx_applications_user_id; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_applications_user_id ON public.applications USING btree (user_id);


--
-- Name: idx_exams_id_institution; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_exams_id_institution ON public.exams USING btree (id_institution);


--
-- Name: idx_mapped_exams_application_id; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_mapped_exams_application_id ON public.mapped_exams USING btree (application_id);


--
-- Name: idx_mapped_exams_application_status; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_mapped_exams_application_status ON public.mapped_exams USING btree (application_id, status);


--
-- Name: idx_mapped_exams_host_exam_id; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_mapped_exams_host_exam_id ON public.mapped_exams USING btree (host_exam_id);


--
-- Name: idx_mapped_exams_sending_exam_id; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_mapped_exams_sending_exam_id ON public.mapped_exams USING btree (sending_exam_id);


--
-- Name: idx_partner_institution_partner_id; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_partner_institution_partner_id ON public.partner_institution USING btree (id_partner_institution);


--
-- Name: idx_uploaded_documents_app_type_date; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_uploaded_documents_app_type_date ON public.uploaded_documents USING btree (application_id, document_type, date_updated DESC);


--
-- Name: idx_uploaded_documents_app_type_status; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_uploaded_documents_app_type_status ON public.uploaded_documents USING btree (application_id, document_type, status);


--
-- Name: idx_uploaded_documents_application_id; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_uploaded_documents_application_id ON public.uploaded_documents USING btree (application_id);


--
-- Name: idx_uploaded_documents_user_id; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_uploaded_documents_user_id ON public.uploaded_documents USING btree (user_id);


--
-- Name: idx_users_id_institution; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_users_id_institution ON public.users USING btree (id_institution);


--
-- Name: idx_users_institution_role; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_users_institution_role ON public.users USING btree (id_institution, role);


--
-- Name: applications applicaiton_status_workflow; Type: TRIGGER; Schema: public; Owner: myuser
--

CREATE TRIGGER applicaiton_status_workflow BEFORE UPDATE ON public.applications FOR EACH ROW WHEN (((new.status)::text <> (old.status)::text)) EXECUTE FUNCTION public.check_application_status_workflow();


--
-- Name: uploaded_documents applicaiton_update_on_upload; Type: TRIGGER; Schema: public; Owner: myuser
--

CREATE TRIGGER applicaiton_update_on_upload BEFORE INSERT ON public.uploaded_documents FOR EACH ROW EXECUTE FUNCTION public.update_application_on_upload();


--
-- Name: applications application_close_check; Type: TRIGGER; Schema: public; Owner: myuser
--

CREATE TRIGGER application_close_check BEFORE UPDATE ON public.applications FOR EACH ROW WHEN ((((old.status)::text <> (new.status)::text) AND ((new.status)::text = 'closed'::text))) EXECUTE FUNCTION public.check_application_close();


--
-- Name: applications application_data_check; Type: TRIGGER; Schema: public; Owner: myuser
--

CREATE TRIGGER application_data_check BEFORE INSERT OR UPDATE ON public.applications FOR EACH ROW EXECUTE FUNCTION public.check_application_data();


--
-- Name: uploaded_documents document_status_update_check; Type: TRIGGER; Schema: public; Owner: myuser
--

CREATE TRIGGER document_status_update_check BEFORE UPDATE ON public.uploaded_documents FOR EACH ROW WHEN (((old.status)::text <> (new.status)::text)) EXECUTE FUNCTION public.check_document_status_update();


--
-- Name: mapped_exams mapped_exam_institutions_check; Type: TRIGGER; Schema: public; Owner: myuser
--

CREATE TRIGGER mapped_exam_institutions_check BEFORE INSERT OR UPDATE ON public.mapped_exams FOR EACH ROW EXECUTE FUNCTION public.check_mapped_exam_institutions();


--
-- Name: mapped_exams mapped_exam_update_status_check; Type: TRIGGER; Schema: public; Owner: myuser
--

CREATE TRIGGER mapped_exam_update_status_check BEFORE UPDATE ON public.mapped_exams FOR EACH ROW WHEN (((old.status)::text <> (new.status)::text)) EXECUTE FUNCTION public.check_update_status_mapped_exams();


--
-- Name: mapped_exams mapped_exam_update_status_check; Type: TRIGGER; Schema: public; Owner: myuser
--

CREATE TRIGGER mapped_exam_update_status_check BEFORE UPDATE ON public.mapped_exams FOR EACH ROW WHEN (((old.status)::text <> (new.status)::text)) EXECUTE FUNCTION public.check_update_status_mapped_exams();


--
-- Name: partner_institution partner_institution_symmetry; Type: TRIGGER; Schema: public; Owner: myuser
--

CREATE TRIGGER partner_institution_symmetry AFTER INSERT ON public.partner_institution FOR EACH ROW EXECUTE FUNCTION public.mirror_partner_institution();


--
-- Name: applications application_valid_referent; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT application_valid_referent FOREIGN KEY (referent_id, sending_institution) REFERENCES public.users(id, id_institution);


--
-- Name: applications applications_host_institution_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_host_institution_fkey FOREIGN KEY (host_institution) REFERENCES public.institutions(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: applications applications_referent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_referent_id_fkey FOREIGN KEY (referent_id) REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: applications applications_sending_institution_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_sending_institution_fkey FOREIGN KEY (sending_institution) REFERENCES public.institutions(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: applications applications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: applications applications_user_id_sending_institution_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_user_id_sending_institution_fkey FOREIGN KEY (user_id, sending_institution) REFERENCES public.users(id, id_institution);


--
-- Name: applications applications_valid_partners; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_valid_partners FOREIGN KEY (sending_institution, host_institution) REFERENCES public.partner_institution(id_institution, id_partner_institution) ON UPDATE CASCADE;


--
-- Name: exams exams_id_institution_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.exams
    ADD CONSTRAINT exams_id_institution_fkey FOREIGN KEY (id_institution) REFERENCES public.institutions(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: mapped_exams mapped_exams_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.mapped_exams
    ADD CONSTRAINT mapped_exams_application_id_fkey FOREIGN KEY (application_id) REFERENCES public.applications(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: mapped_exams mapped_exams_host_exam_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.mapped_exams
    ADD CONSTRAINT mapped_exams_host_exam_id_fkey FOREIGN KEY (host_exam_id) REFERENCES public.exams(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: mapped_exams mapped_exams_sending_exam_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.mapped_exams
    ADD CONSTRAINT mapped_exams_sending_exam_id_fkey FOREIGN KEY (sending_exam_id) REFERENCES public.exams(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: partner_institution partner_institution_id_institution_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.partner_institution
    ADD CONSTRAINT partner_institution_id_institution_fkey FOREIGN KEY (id_institution) REFERENCES public.institutions(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: partner_institution partner_institution_id_partner_institution_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.partner_institution
    ADD CONSTRAINT partner_institution_id_partner_institution_fkey FOREIGN KEY (id_partner_institution) REFERENCES public.institutions(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: uploaded_documents uploaded_documents_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.uploaded_documents
    ADD CONSTRAINT uploaded_documents_application_id_fkey FOREIGN KEY (application_id) REFERENCES public.applications(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: uploaded_documents uploaded_documents_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.uploaded_documents
    ADD CONSTRAINT uploaded_documents_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: users users_id_institution_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_id_institution_fkey FOREIGN KEY (id_institution) REFERENCES public.institutions(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: mv_applications_by_host_institution; Type: MATERIALIZED VIEW DATA; Schema: public; Owner: myuser
--

REFRESH MATERIALIZED VIEW public.mv_applications_by_host_institution;


--
-- Name: mv_applications_by_status; Type: MATERIALIZED VIEW DATA; Schema: public; Owner: myuser
--

REFRESH MATERIALIZED VIEW public.mv_applications_by_status;


--
-- Name: mv_institution_activity; Type: MATERIALIZED VIEW DATA; Schema: public; Owner: myuser
--

REFRESH MATERIALIZED VIEW public.mv_institution_activity;


--
-- PostgreSQL database dump complete
--

\unrestrict 08onwZCvhM0ELc7ygGxFrMtvoF6daOY9GBFJ4haoQkTuLbyexsQt79Y5BrtIBoR

