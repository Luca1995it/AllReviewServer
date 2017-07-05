CREATE TABLE utente(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	nome TEXT UNIQUE,
	email TEXT UNIQUE,
	password TEXT NOT NULL,
	fotopath TEXT DEFAULT "default_profile",
	data_reg INTEGER,
	attivato INTEGER DEFAULT 0,
	NuovaRecensioneUtenteCheSeguo INTEGER DEFAULT 1,
    NuovaRecensioneOggettoCheSeguo INTEGER DEFAULT 1,
    NuovoVotoMiaRecensione INTEGER DEFAULT 1,
    NuovaRispostaMiaDomanda INTEGER DEFAULT 1,
    MiaMigliorRisposta INTEGER DEFAULT 1,
	lingua TEXT DEFAULT "Italian",
	code TEXT DEFAULT 0
);

CREATE TABLE categoria(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	nome TEXT NOT NULL
);

CREATE TABLE elemento(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	nome TEXT NOT NULL,
	descr TEXT NOT NULL,
	id_categoria INTEGER,
	FOREIGN KEY(id_categoria) REFERENCES categoria(id)
);

CREATE TABLE foto(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	data INTEGER,
	id_utente INTEGER,
	rimossa INTEGER DEFAULT 0,
	path TEXT NOT NULL,
	id_elemento INTEGER,
	FOREIGN KEY(id_utente) REFERENCES utente(id),
	FOREIGN KEY(id_elemento) REFERENCES elemento(id)
);

CREATE TABLE recensione(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	voto INTEGER DEFAULT 4,
	fotopath TEXT,
	descr TEXT NOT NULL,
	titolo TEXT NOT NULL,
	data integer,
	rimossa INTEGER DEFAULT 0,
	id_utente INTEGER,
	id_elemento INTEGER,
	FOREIGN KEY(id_utente) REFERENCES utente(id),
	FOREIGN KEY(id_elemento) REFERENCES elemento(id)
);

CREATE TABLE domanda(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	data INTEGER,
	testo TEXT NOT NULL,
	id_utente INTEGER,
	id_elemento INTEGER,
	id_risposta_top INTEGER DEFAULT 0,
	FOREIGN KEY(id_risposta_top) REFERENCES risposta(id),
	FOREIGN KEY(id_utente) REFERENCES utente(id),
	FOREIGN KEY(id_elemento) REFERENCES elemento(id)
);

CREATE TABLE risposta(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	data INTEGER,
	testo TEXT NOT NULL,
	id_domanda INTEGER,
	id_utente INTEGER,
	FOREIGN KEY(id_utente) REFERENCES utente(id),
	FOREIGN KEY(id_domanda) REFERENCES domanda(id)
);

CREATE TABLE notifica(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	id_utente INTEGER,
	data INTEGER NOT NULL,
	-- TIPI: 0->NuovaRecensioneUtenteCheSeguo, 1->NuovaRecensioneOggettoCheSeguo, 2->NuovoVotoMiaRecensione, 3->NuovaRispostaMiaDomanda, 4->MiaMigliorRisposta
	tipo INTEGER,
	id_rec INTEGER DEFAULT 0,
	id_domanda INTEGER DEFAULT 0,
	id_risposta INTEGER DEFAULT 0,
	id_voto INTEGER DEFAULT 0,
	FOREIGN KEY(id_voto) REFERENCES voto_rec(id),
	FOREIGN KEY(id_rec) REFERENCES recensione(id),
	FOREIGN KEY(id_domanda) REFERENCES domanda(id),
	FOREIGN KEY(id_risposta) REFERENCES risposta(id)
);

CREATE TABLE preferiti(
	id_utente INTEGER,
	id_elemento INTEGER,
	PRIMARY KEY (id_utente,id_elemento),
	FOREIGN KEY(id_utente) REFERENCES utente(id),
	FOREIGN KEY(id_elemento) REFERENCES elemento(id)
);

CREATE TABLE modifica(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	id_elemento INTEGER,
	id_utente INTEGER,
	rimossa INTEGER DEFAULT 0,
	first INTEGER DEFAULT 1, --0: prima creazione, 1 modifica
	data INTEGER,
	FOREIGN KEY(id_utente) REFERENCES utente(id),
	FOREIGN KEY(id_elemento) REFERENCES elemento(id)
);

CREATE TABLE segue(
	id_utente_from INTEGER,
	id_utente_to INTEGER,
	PRIMARY KEY (id_utente_from,id_utente_to),
	FOREIGN KEY(id_utente_from) REFERENCES utente(id),
	FOREIGN KEY(id_utente_to) REFERENCES utente(id)
);

CREATE TABLE segnala_elemento(
	id_utente INTEGER,
	id_elemento INTEGER,
	motivazione TEXT DEFAULT NULL,
	PRIMARY KEY (id_utente,id_elemento),
	FOREIGN KEY(id_utente) REFERENCES utente(id),
	FOREIGN KEY(id_elemento) REFERENCES elemento(id)
);

CREATE TABLE segnala_recensione(
	id_utente INTEGER,
	id_recensione INTEGER,
	motivazione TEXT DEFAULT NULL,
	PRIMARY KEY (id_utente,id_recensione),
	FOREIGN KEY(id_utente) REFERENCES utente(id),
	FOREIGN KEY(id_recensione) REFERENCES recensione(id)
);

CREATE TABLE segnala_foto(
	id_utente INTEGER,
	id_foto INTEGER,
	motivazione TEXT DEFAULT NULL,
	PRIMARY KEY (id_utente,id_foto),
	FOREIGN KEY(id_utente) REFERENCES utente(id),
	FOREIGN KEY(id_foto) REFERENCES foto(id)
);

CREATE TABLE voto_rec(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	data INTEGER,
	id_utente INTEGER,
	id_recensione INTEGER,
	voto INTEGER DEFAULT 1,
	UNIQUE (id_utente,id_recensione),
	FOREIGN KEY(id_utente) REFERENCES utente(id),
	FOREIGN KEY(id_recensione) REFERENCES recensione(id)
);


CREATE TABLE visite_rec(
	id_utente INTEGER,
	id_recensione INTEGER,
	conto INTEGER DEFAULT 0,
	last INTEGER DEFAULT 0,
	PRIMARY KEY (id_utente,id_recensione),
	FOREIGN KEY(id_utente) REFERENCES utente(id),
	FOREIGN KEY(id_recensione) REFERENCES recensione(id)
);

CREATE TABLE visite_el(
	id_utente INTEGER,
	id_elemento INTEGER,
	conto INTEGER DEFAULT 0,
	last INTEGER DEFAULT 0,
	PRIMARY KEY (id_utente,id_elemento),
	FOREIGN KEY(id_utente) REFERENCES utente(id),
	FOREIGN KEY(id_elemento) REFERENCES elemento(id)
);

CREATE TABLE assistenza(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	email TEXT NOT NULL,
	testo TEXT NOT NULL,
	data INTEGER
);

insert into categoria (id,nome) values (1,"Abbigliamento");
insert into categoria (id,nome) values (2,"Arte & Antiquariato");
insert into categoria (id,nome) values (3,"Auto e Moto");
insert into categoria (id,nome) values (4,"Bellezza & Salute");
insert into categoria (id,nome) values (5,"Biglietti ed eventi");
insert into categoria (id,nome) values (6,"Casa, Arredamento & Bricolage");
insert into categoria (id,nome) values (7,"Collezionismo");
insert into categoria (id,nome) values (8,"Commercio ed industria");
insert into categoria (id,nome) values (9,"Elettrodomestici");
insert into categoria (id,nome) values (10,"Film, Fotografia e Video");
insert into categoria (id,nome) values (11,"Giocattoli & Modellismo");
insert into categoria (id,nome) values (12,"Libri, Fumetti e Lettori elettronici");
insert into categoria (id,nome) values (13,"Informatica e Mondo Online");
insert into categoria (id,nome) values (14,"Orologi e Gioielli");
insert into categoria (id,nome) values (15,"Attrezzatura Sportiva");
insert into categoria (id,nome) values (16,"Telefonia");
insert into categoria (id,nome) values (17,"Televisori");
insert into categoria (id,nome) values (18,"HiFi, Amplificatori e Casse");
insert into categoria (id,nome) values (19,"Videogiochi e Console");
insert into categoria (id,nome) values (20,"Cucina");
insert into categoria (id,nome) values (21,"Elettronica e componentistica");
insert into categoria (id,nome) values (22,"Hotel & Alloggi");
insert into categoria (id,nome) values (23,"Infanzia");
insert into categoria (id,nome) values (24,"Scuola, Università ed Ufficio");
insert into categoria (id,nome) values (25,"Computer & Accessori");






