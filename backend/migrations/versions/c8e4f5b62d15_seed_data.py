"""seed data

Development/demo dataset (users, institutions, exams, sample applications),
extracted from the former database/overseas.sql dump. Runs BEFORE the triggers
revision (same order pg_dump uses): the historical rows include applications
past the initial statuses and symmetric partner pairs, which the INSERT
triggers would reject or duplicate.

Revision ID: c8e4f5b62d15
Revises: 33e4600ce890
Create Date: 2026-07-04

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'c8e4f5b62d15'
down_revision = '33e4600ce890'
branch_labels = None
depends_on = None


SEED_SQL = r"""
--
-- PostgreSQL database dump
--


-- Dumped from database version 17.10
-- Dumped by pg_dump version 17.10


--
-- Data for Name: institutions; Type: TABLE DATA; Schema: public; Owner: myuser
--

INSERT INTO public.institutions (id, name, country, city) VALUES (1, 'Ca'' Foscari University of Venice', 'Italy', 'Venice');
INSERT INTO public.institutions (id, name, country, city) VALUES (2, 'Sorbonne University', 'France', 'Paris');
INSERT INTO public.institutions (id, name, country, city) VALUES (3, 'Ludwig Maximilian University of Munich', 'Germany', 'Munich');
INSERT INTO public.institutions (id, name, country, city) VALUES (4, 'University of Oxford', 'England', 'Oxford');
INSERT INTO public.institutions (id, name, country, city) VALUES (5, 'University of Amsterdam', 'Netherlands', 'Amsterdam');
INSERT INTO public.institutions (id, name, country, city) VALUES (6, 'ETH Zurich', 'Switzerland', 'Zurich');
INSERT INTO public.institutions (id, name, country, city) VALUES (7, 'Complutense University of Madrid', 'Spain', 'Madrid');
INSERT INTO public.institutions (id, name, country, city) VALUES (8, 'University of Warsaw', 'Poland', 'Warsaw');
INSERT INTO public.institutions (id, name, country, city) VALUES (9, 'Charles University', 'Czech Republic', 'Prague');
INSERT INTO public.institutions (id, name, country, city) VALUES (10, 'KU Leuven', 'Belgium', 'Leuven');
INSERT INTO public.institutions (id, name, country, city) VALUES (11, 'University of Vienna', 'Austria', 'Vienna');
INSERT INTO public.institutions (id, name, country, city) VALUES (12, 'University of Helsinki', 'Finland', 'Helsinki');
INSERT INTO public.institutions (id, name, country, city) VALUES (13, 'Stockholm University', 'Sweden', 'Stockholm');
INSERT INTO public.institutions (id, name, country, city) VALUES (14, 'University of Copenhagen', 'Denmark', 'Copenhagen');
INSERT INTO public.institutions (id, name, country, city) VALUES (15, 'University of Oslo', 'Norway', 'Oslo');
INSERT INTO public.institutions (id, name, country, city) VALUES (16, 'University of Lisbon', 'Portugal', 'Lisbon');
INSERT INTO public.institutions (id, name, country, city) VALUES (17, 'University of Athens', 'Greece', 'Athens');
INSERT INTO public.institutions (id, name, country, city) VALUES (18, 'Eötvös Loránd University', 'Hungary', 'Budapest');
INSERT INTO public.institutions (id, name, country, city) VALUES (19, 'University of Bucharest', 'Romania', 'Bucharest');
INSERT INTO public.institutions (id, name, country, city) VALUES (20, 'University of Zagreb', 'Croatia', 'Zagreb');


--
-- Data for Name: partner_institution; Type: TABLE DATA; Schema: public; Owner: myuser
--

INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (1, 1, 3);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (2, 1, 4);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (3, 1, 5);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (4, 1, 6);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (5, 1, 7);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (6, 2, 5);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (7, 2, 6);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (8, 2, 10);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (9, 2, 18);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (10, 2, 19);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (11, 3, 11);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (12, 3, 16);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (13, 3, 17);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (14, 4, 9);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (15, 4, 12);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (16, 4, 13);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (17, 4, 16);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (18, 5, 11);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (19, 5, 16);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (20, 5, 17);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (21, 6, 11);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (22, 6, 13);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (23, 6, 20);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (24, 7, 10);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (25, 7, 14);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (26, 7, 16);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (27, 8, 15);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (28, 8, 20);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (29, 9, 15);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (30, 9, 17);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (31, 10, 13);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (32, 11, 12);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (33, 11, 15);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (34, 12, 17);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (35, 12, 20);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (36, 13, 18);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (37, 13, 19);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (38, 14, 16);
INSERT INTO public.partner_institution (id, id_institution, id_partner_institution) VALUES (41, 14, 1);


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: myuser
--

INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (1, 'marco.rossi@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Marco', 'Rossi', 1);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (2, 'giulia.ferrari@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Giulia', 'Ferrari', 1);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (3, 'luca.bianchi@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Luca', 'Bianchi', 1);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (4, 'sofia.romano@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Sofia', 'Romano', 1);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (5, 'matteo.conti@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Matteo', 'Conti', 1);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (6, 'elena.ricci@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Elena', 'Ricci', 1);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (7, 'davide.marino@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Davide', 'Marino', 1);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (8, 'chiara.greco@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Chiara', 'Greco', 1);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (9, 'andrea.bruno@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Andrea', 'Bruno', 1);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (10, 'valentina.gallo@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Valentina', 'Gallo', 1);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (11, 'pierre.martin@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Pierre', 'Martin', 2);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (12, 'camille.durand@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Camille', 'Durand', 2);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (13, 'hans.mueller@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Hans', 'Mueller', 3);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (14, 'anna.schmidt@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Anna', 'Schmidt', 3);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (15, 'james.smith@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'James', 'Smith', 4);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (16, 'emily.jones@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Emily', 'Jones', 4);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (17, 'lars.janssen@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Lars', 'Janssen', 5);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (18, 'sophie.vandenberg@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Sophie', 'Vandenberg', 5);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (19, 'felix.keller@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Felix', 'Keller', 6);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (20, 'nina.brunner@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Nina', 'Brunner', 6);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (21, 'carlos.garcia@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Carlos', 'Garcia', 7);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (22, 'lucia.fernandez@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Lucia', 'Fernandez', 7);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (23, 'piotr.kowalski@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Piotr', 'Kowalski', 8);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (24, 'katarzyna.nowak@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Katarzyna', 'Nowak', 8);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (25, 'jan.novak@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Jan', 'Novak', 9);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (26, 'petra.dvorak@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Petra', 'Dvorak', 9);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (27, 'pieter.desmet@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Pieter', 'Desmet', 10);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (28, 'elien.claes@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Elien', 'Claes', 10);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (29, 'stefan.huber@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Stefan', 'Huber', 11);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (30, 'lisa.wagner@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Lisa', 'Wagner', 11);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (31, 'mikko.virtanen@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Mikko', 'Virtanen', 12);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (32, 'aino.makinen@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Aino', 'Makinen', 12);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (33, 'erik.lindqvist@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Erik', 'Lindqvist', 13);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (34, 'maja.johansson@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Maja', 'Johansson', 13);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (35, 'rasmus.nielsen@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Rasmus', 'Nielsen', 14);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (36, 'ida.andersen@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Ida', 'Andersen', 14);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (37, 'olav.berg@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Olav', 'Berg', 15);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (38, 'ingrid.hansen@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Ingrid', 'Hansen', 15);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (39, 'joao.silva@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'João', 'Silva', 16);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (40, 'ana.costa@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Ana', 'Costa', 16);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (41, 'nikos.papadopoulos@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Nikos', 'Papadopoulos', 17);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (42, 'eleni.georgiou@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Eleni', 'Georgiou', 17);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (43, 'balazs.nagy@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Balázs', 'Nagy', 18);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (44, 'reka.kovacs@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Réka', 'Kovács', 18);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (45, 'andrei.popescu@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Andrei', 'Popescu', 19);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (46, 'ioana.ionescu@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Ioana', 'Ionescu', 19);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (47, 'luka.horvat@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Luka', 'Horvat', 20);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (48, 'ana.maric@stud.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'student', 'Ana', 'Marić', 20);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (49, 'giovanni.ferrari@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Giovanni', 'Ferrari', 1);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (50, 'laura.bianchi@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Laura', 'Bianchi', 1);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (51, 'carlo.rossi@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Carlo', 'Rossi', 1);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (52, 'jean.dupont@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Jean', 'Dupont', 2);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (53, 'marie.leroy@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Marie', 'Leroy', 2);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (54, 'thomas.bauer@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Thomas', 'Bauer', 3);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (55, 'julia.richter@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Julia', 'Richter', 3);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (56, 'william.taylor@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'William', 'Taylor', 4);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (57, 'sarah.wright@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Sarah', 'Wright', 4);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (58, 'jan.dekker@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Jan', 'Dekker', 5);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (59, 'maria.berg@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Maria', 'Berg', 6);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (60, 'pedro.alves@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Pedro', 'Alves', 7);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (61, 'agnieszka.wisniewska@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Agnieszka', 'Wiśniewska', 8);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (62, 'tomas.blazek@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Tomáš', 'Blažek', 9);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (63, 'inge.willems@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Inge', 'Willems', 10);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (64, 'markus.gruber@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Markus', 'Gruber', 11);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (65, 'sari.heikkinen@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Sari', 'Heikkinen', 12);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (66, 'anders.svensson@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Anders', 'Svensson', 13);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (67, 'anne.christensen@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Anne', 'Christensen', 14);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (68, 'kari.olsen@prof.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'referent', 'Kari', 'Olsen', 15);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (69, 'giuseppe.verdi@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Giuseppe', 'Verdi', 1);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (70, 'anna.colombo@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Anna', 'Colombo', 1);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (71, 'roberto.mancini@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Roberto', 'Mancini', 1);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (72, 'claire.moreau@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Claire', 'Moreau', 2);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (73, 'francois.simon@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'François', 'Simon', 2);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (74, 'klaus.zimmer@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Klaus', 'Zimmer', 3);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (75, 'heike.fischer@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Heike', 'Fischer', 3);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (76, 'oliver.brown@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Oliver', 'Brown', 4);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (77, 'charlotte.davies@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Charlotte', 'Davies', 4);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (78, 'emma.visser@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Emma', 'Visser', 5);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (79, 'david.meier@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'David', 'Meier', 6);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (80, 'carmen.ruiz@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Carmen', 'Ruiz', 7);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (81, 'marek.wojcik@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Marek', 'Wójcik', 8);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (82, 'lenka.horakova@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Lenka', 'Horáková', 9);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (83, 'thomas.claes@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Thomas', 'Claes', 10);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (84, 'monika.fischer@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Monika', 'Fischer', 11);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (85, 'paivi.leinonen@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Päivi', 'Leinonen', 12);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (86, 'per.nilsson@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Per', 'Nilsson', 13);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (87, 'mette.larsen@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Mette', 'Larsen', 14);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (88, 'sigrid.dahl@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Sigrid', 'Dahl', 15);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (89, 'rui.ferreira@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Rui', 'Ferreira', 16);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (90, 'stavros.alexiou@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Stavros', 'Alexiou', 17);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (91, 'zoltan.fekete@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Zoltán', 'Fekete', 18);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (92, 'mihai.dinu@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Mihai', 'Dinu', 19);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (93, 'tomislav.babic@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Tomislav', 'Babić', 20);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (94, 'katia.lombardi@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Katia', 'Lombardi', 16);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (95, 'nuno.santos@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Nuno', 'Santos', 17);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (96, 'george.pappas@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'George', 'Pappas', 18);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (97, 'diana.stoica@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Diana', 'Stoica', 19);
INSERT INTO public.users (id, email, password_hash, role, firstname, lastname, id_institution) VALUES (98, 'ivana.petrovic@staff.uni.com', 'pbkdf2:sha256:1000000$5Y4gz7EU8aIfEBbW$1051a735da5485c3f3cc9fa20ac0e7cbf603f9850a2670f5dd8ab2b44fc58fff', 'staff', 'Ivana', 'Petrović', 20);


--
-- Data for Name: applications; Type: TABLE DATA; Schema: public; Owner: myuser
--

--
-- Data for Name: exams; Type: TABLE DATA; Schema: public; Owner: myuser
--

INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (1, 'CT3-CS0101', 'Distributed Systems', 9, 1);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (2, 'CT3-CS0102', 'Compilers', 9, 1);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (3, 'CT3-CS0103', 'Operating Systems', 6, 1);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (4, 'CT3-CS0104', 'Algorithm Design', 9, 1);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (5, 'CT3-CS0105', 'Computer Architecture', 6, 1);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (6, 'FRA-CS0201', 'Formal Methods', 6, 2);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (7, 'FRA-CS0202', 'Logic Programming', 6, 2);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (8, 'FRA-CS0203', 'Type Theory', 6, 2);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (9, 'FRA-CS0204', 'Cryptography', 6, 2);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (10, 'FRA-CS0205', 'Parallel Computing', 6, 2);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (11, 'TUM-CS0301', 'Embedded Systems', 12, 3);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (12, 'TUM-CS0302', 'Real-Time Systems', 9, 3);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (13, 'TUM-CS0303', 'Digital Signal Processing', 9, 3);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (14, 'TUM-CS0304', 'Control Theory', 12, 3);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (15, 'TUM-CS0305', 'Hardware Design', 12, 3);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (16, 'OXF-CS0401', 'Machine Learning', 9, 4);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (17, 'OXF-CS0402', 'Neural Networks', 6, 4);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (18, 'OXF-CS0403', 'Computer Vision', 9, 4);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (19, 'OXF-CS0404', 'Data Mining', 9, 4);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (20, 'OXF-CS0405', 'Probabilistic Graphical Models', 6, 4);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (21, 'AMS-CS0501', 'Software Engineering', 9, 5);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (22, 'AMS-CS0502', 'Design Patterns', 12, 5);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (23, 'AMS-CS0503', 'Agile Methods', 9, 5);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (24, 'AMS-CS0504', 'Testing & Verification', 9, 5);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (25, 'AMS-CS0505', 'DevOps', 6, 5);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (26, 'ETH-CS0601', 'Web Engineering', 6, 6);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (27, 'ETH-CS0602', 'Cloud Computing', 9, 6);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (28, 'ETH-CS0603', 'Microservices', 12, 6);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (29, 'ETH-CS0604', 'REST API Design', 6, 6);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (30, 'ETH-CS0605', 'Containerization', 6, 6);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (31, 'MADR-CS0701', 'Cybersecurity', 9, 7);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (32, 'MADR-CS0702', 'Network Security', 12, 7);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (33, 'MADR-CS0703', 'Ethical Hacking', 6, 7);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (34, 'MADR-CS0704', 'Digital Forensics', 9, 7);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (35, 'MADR-CS0705', 'Malware Analysis', 6, 7);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (36, 'WARSW-CS0801', 'Database Systems', 6, 8);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (37, 'WARSW-CS0802', 'Query Optimization', 12, 8);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (38, 'WARSW-CS0803', 'NoSQL Systems', 9, 8);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (39, 'WARSW-CS0804', 'Data Warehousing', 12, 8);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (40, 'WARSW-CS0805', 'Transaction Management', 6, 8);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (41, 'CHU-CS0901', 'Human-Computer Interaction', 9, 9);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (42, 'CHU-CS0902', 'UX Design', 6, 9);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (43, 'CHU-CS0903', 'Accessibility', 9, 9);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (44, 'CHU-CS0904', 'Cognitive Ergonomics', 6, 9);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (45, 'CHU-CS0905', 'Interaction Prototyping', 6, 9);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (46, 'KUL-CS1001', 'Mobile Computing', 9, 10);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (47, 'KUL-CS1002', 'IoT Systems', 6, 10);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (48, 'KUL-CS1003', 'Edge Computing', 9, 10);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (49, 'KUL-CS1004', 'Wireless Protocols', 6, 10);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (50, 'KUL-CS1005', 'Sensor Networks', 6, 10);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (51, 'WIEN-CS1101', 'Computer Graphics', 9, 11);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (52, 'WIEN-CS1102', '3D Rendering', 6, 11);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (53, 'WIEN-CS1103', 'Game Engine Design', 9, 11);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (54, 'WIEN-CS1104', 'Shader Programming', 9, 11);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (55, 'WIEN-CS1105', 'Geometric Modeling', 6, 11);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (56, 'HEL-CS1201', 'Bioinformatics', 9, 12);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (57, 'HEL-CS1202', 'Computational Genomics', 9, 12);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (58, 'HEL-CS1203', 'Protein Modeling', 6, 12);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (59, 'HEL-CS1204', 'Medical Imaging', 6, 12);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (60, 'HEL-CS1205', 'Health Informatics', 6, 12);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (61, 'STOSWE-CS1301', 'Quantum Computing', 6, 13);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (62, 'STOSWE-CS1302', 'Quantum Algorithms', 12, 13);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (63, 'STOSWE-CS1303', 'Post-Quantum Cryptography', 6, 13);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (64, 'STOSWE-CS1304', 'Quantum Error Correction', 12, 13);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (65, 'STOSWE-CS1305', 'Quantum Programming', 9, 13);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (66, 'COP-CS1401', 'Robotics', 9, 14);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (67, 'COP-CS1402', 'Motion Planning', 6, 14);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (68, 'COP-CS1403', 'Computer Vision for Robotics', 9, 14);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (69, 'COP-CS1404', 'ROS Programming', 12, 14);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (70, 'COP-CS1405', 'Autonomous Systems', 6, 14);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (71, 'OSLO-CS1501', 'Natural Language Processing', 6, 15);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (72, 'OSLO-CS1502', 'Speech Recognition', 6, 15);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (73, 'OSLO-CS1503', 'Information Retrieval', 6, 15);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (74, 'OSLO-CS1504', 'Text Mining', 6, 15);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (75, 'OSLO-CS1505', 'Computational Linguistics', 9, 15);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (76, 'LISBOA-CS1601', 'High-Performance Computing', 12, 16);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (77, 'LISBOA-CS1602', 'GPU Programming', 9, 16);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (78, 'LISBOA-CS1603', 'Cluster Computing', 6, 16);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (79, 'LISBOA-CS1604', 'Scientific Computing', 9, 16);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (80, 'LISBOA-CS1605', 'Numerical Methods', 12, 16);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (81, 'ATHNS-CS1701', 'Network Engineering', 6, 17);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (82, 'ATHNS-CS1702', 'Routing Protocols', 6, 17);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (83, 'ATHNS-CS1703', 'SDN', 6, 17);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (84, 'ATHNS-CS1704', 'Network Virtualization', 9, 17);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (85, 'ATHNS-CS1705', '5G Systems', 6, 17);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (86, 'UHUNG-CS1801', 'Functional Programming', 9, 18);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (87, 'UHUNG-CS1802', 'Haskell', 6, 18);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (88, 'UHUNG-CS1803', 'Scala', 6, 18);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (89, 'UHUNG-CS1804', 'Category Theory for CS', 9, 18);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (90, 'UHUNG-CS1805', 'Lambda Calculus', 9, 18);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (91, 'BUCHRST-CS1901', 'Systems Programming', 6, 19);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (92, 'BUCHRST-CS1902', 'Rust Programming', 6, 19);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (93, 'BUCHRST-CS1903', 'Memory Safety', 12, 19);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (94, 'BUCHRST-CS1904', 'Low-Level Optimization', 6, 19);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (95, 'BUCHRST-CS1905', 'Linkers & Loaders', 9, 19);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (96, 'ZAGR-CS2001', 'Data Science', 6, 20);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (97, 'ZAGR-CS2002', 'Statistical Learning', 9, 20);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (98, 'ZAGR-CS2003', 'Big Data Processing', 9, 20);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (99, 'ZAGR-CS2004', 'Data Visualization', 6, 20);
INSERT INTO public.exams (id, code, name, credits, id_institution) VALUES (100, 'ZAGR-CS2005', 'Feature Engineering', 6, 20);


--
-- Data for Name: uploaded_documents; Type: TABLE DATA; Schema: public; Owner: myuser
--

--
-- Data for Name: la_modifications; Type: TABLE DATA; Schema: public; Owner: myuser
--

--
-- Data for Name: la_modification_exams; Type: TABLE DATA; Schema: public; Owner: myuser
--


--
-- Data for Name: mapped_exams; Type: TABLE DATA; Schema: public; Owner: myuser
--


--
-- Name: applications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.applications_id_seq', 27, true);


--
-- Name: exams_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.exams_id_seq', 101, true);


--
-- Name: institutions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.institutions_id_seq', 1, false);


--
-- Name: la_modification_exams_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.la_modification_exams_id_seq', 30, true);


--
-- Name: la_modifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.la_modifications_id_seq', 16, true);


--
-- Name: mapped_exams_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.mapped_exams_id_seq', 221, true);


--
-- Name: partner_institution_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.partner_institution_id_seq', 41, true);


--
-- Name: uploaded_documents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.uploaded_documents_id_seq', 67, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.users_id_seq', 99, true);


--
-- PostgreSQL database dump complete
--
"""


def upgrade():
    op.execute(SEED_SQL)


def downgrade():
    op.execute(
        "TRUNCATE public.la_modification_exams, public.la_modifications, "
        "public.uploaded_documents, public.mapped_exams, public.applications, "
        "public.exams, public.partner_institution, public.users, "
        "public.institutions RESTART IDENTITY CASCADE;"
    )
