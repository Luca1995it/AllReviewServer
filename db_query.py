import sqlite3 as sql
import hashlib
import generators as gen
import random
import mail
import string
import Levenshtein
import punteggi as pt
import datetime
from urllib2 import *
import urllib
import json
import sys


class NotAuthError(Exception):
    pass

class MailProblemsException(Exception):
    pass

class WrongPasswordException(Exception):
    pass

class IncorrectCodeException(Exception):
    pass

resolution = 12

conn = sql.connect('database.db')
conn.text_factory = str

def get_token():
    res = {}

    c = conn.cursor()

    query = "SELECT * FROM UTENTE"
    t = ()
    utente = list(c.execute(query, t))

    for u in utente:
        new_token = gen.getsha((u[3]+u[1]+u[2])[:40])
        res[new_token] = u[0]
        
    c.close()
    return res


def login(username,password):
    c = conn.cursor()
    password = gen.getsha(password)
    query = "SELECT * FROM UTENTE WHERE (email=? OR nome=?) AND password=?"
    t = (username, username, password)

    utente = list(c.execute(query, t))

    res = utente[0]
    id_utente = res[0]

    query = "SELECT A.total*5 + B.total + C.total*3 + D.total*(-2) + E.total + F.total*2 + G.total*(-15) + H.total*(-30) + I.total*(-30) FROM (select count(*) as total from recensione where id_utente = ? and data < ?) as A, (select count(*) as total from voto_rec where id_utente = ? and data < ?) as B, (select count(*) as total from recensione join voto_rec on recensione.id = voto_rec.id_recensione  where recensione.id_utente = ? and voto_rec.voto > 0 and voto_rec.data < ?) as C, (select count(*) as total from recensione join voto_rec on recensione.id = voto_rec.id_recensione  where recensione.id_utente = ? and voto_rec.voto < 0 and voto_rec.data < ?) as D, (select count(*) as total from risposta where risposta.id_utente = ? and data < ?) as E, (select count(*) as total from risposta join domanda on risposta.id = domanda.id_risposta_top and risposta.id_utente = ? and risposta.data < ?) as F, (select count(*) as total from foto where foto.id_utente = ? and foto.rimossa > 0 and foto.data < ?) as G, (select count(*) as total from modifica where modifica.id_utente = ? and modifica.rimossa > 0 and modifica.data < ?) as H, (select count(*) as total from recensione where recensione.id_utente = ? and recensione.rimossa > 0 and recensione.data < ?) as I"
    now = gen.get_now()
    t = (id_utente, now)*9

    level = list(c.execute(query,t))[0][0]

    new_token = gen.getsha((res[3]+res[1]+res[2])[:40])

    grafico = user_rating_graph(id_utente,resolution)
    utente_final = gen.utente(res,pt.get_livello(level),new_token,grafico)

    data_now = datetime.datetime.fromtimestamp(gen.get_now())
    start_of_the_day = (datetime.datetime(data_now.year,data_now.month,data_now.day)  - datetime.datetime(1970, 1, 1)).total_seconds()
    
    t = (id_utente,start_of_the_day)
   
    query = "SELECT id FROM DOMANDA WHERE id_utente=? and data>?"
    just_domanda = len(list(c.execute(query,t)))

    query = "SELECT id FROM VOTO_REC WHERE id_utente=? and data>?"
    just_voto = len(list(c.execute(query,t)))
 
    query = "SELECT id FROM RECENSIONE WHERE id_utente=? and data>?"
    just_recensione = len(list(c.execute(query,t)))
 
    utente_final['domande_counter'] = utente_final['level']['max_dom'] - just_domanda
    utente_final['recensioni_counter'] = utente_final['level']['max_rec'] - just_recensione
    utente_final['voti_counter'] = utente_final['level']['max_voti'] - just_voto

    fine = {
        'utente': utente_final
    }

    c.close()
    return fine
    

def preferiti(id_utente):
    c = conn.cursor()
    query = 'SELECT id_elemento FROM PREFERITI WHERE id_utente=?'
    t = (id_utente,)

    elementi_id = list(c.execute(query,t))

    res = []
    for id_elemento in elementi_id:
        res.append(elemento(id_elemento[0]))
    c.close()
    return res


def user_rating_graph(id_utente, resolution):
    c = conn.cursor()

    query = "SELECT data_reg FROM utente where id=?"
    t = (id_utente,)
    data_reg = list(c.execute(query,t))[0][0]
    now = gen.get_now()


    interval = (now-data_reg)/int(resolution)

    interval = interval if interval > 1 else 1

    counter = data_reg

    res = []

    while counter < now:
        query = "SELECT A.total*5 + B.total + C.total*3 + D.total*(-2) + E.total + F.total*2 + G.total*(-15) + H.total*(-30) + I.total*(-30) FROM (select count(*) as total from recensione where id_utente = ? and data < ?) as A, (select count(*) as total from voto_rec where id_utente = ? and data < ?) as B, (select count(*) as total from recensione join voto_rec on recensione.id = voto_rec.id_recensione  where recensione.id_utente = ? and voto_rec.voto > 0 and voto_rec.data < ?) as C, (select count(*) as total from recensione join voto_rec on recensione.id = voto_rec.id_recensione  where recensione.id_utente = ? and voto_rec.voto < 0 and voto_rec.data < ?) as D, (select count(*) as total from risposta where risposta.id_utente = ? and data < ?) as E, (select count(*) as total from risposta join domanda on risposta.id = domanda.id_risposta_top and risposta.id_utente = ? and risposta.data < ?) as F, (select count(*) as total from foto where foto.id_utente = ? and foto.rimossa > 0 and foto.data < ?) as G, (select count(*) as total from modifica where modifica.id_utente = ? and modifica.rimossa > 0 and modifica.data < ?) as H, (select count(*) as total from recensione where recensione.id_utente = ? and recensione.rimossa > 0 and recensione.data < ?) as I"
        t = (id_utente, counter)*9

        tmp = {}
        tmp['data'] = counter
        tmp['points'] = list(c.execute(query,t))[0][0]
        res.append(tmp)
        counter += interval
    
    c.close()
    return res


def search_elemento(nome):
    c = conn.cursor()
    query = 'SELECT nome, id FROM ELEMENTO'
    t = ()

    res = set()

    elementi = list(c.execute(query,t))
    fact = 0.0

    while(len(res) < 6 and fact < 3):
        for a in elementi:
    
            if similString(nome,a[0],fact):
                res.add(a[1])
        fact += .5
    
    res = [elemento(x) for x in res]
    c.close()
    return res


def similString(a,b,fact):
    a,b = a.lower(), b.lower()
    return a in b or b in a or Levenshtein.distance(a, b) < (((len(a) + len(b))/float(2))*0.2*fact)


def upload_foto_elem(id_elemento, id_utente, filename):
    c = conn.cursor()
    query = 'INSERT INTO FOTO (data,path,id_elemento, id_utente) VALUES (?,?,?,?)'

    tmp_time = gen.get_now()
    t = (tmp_time, filename, id_elemento, id_utente)

    c.execute(query,t)
    conn.commit()

    query = 'SELECT id FROM FOTO WHERE data=? AND path=? AND id_elemento=? AND id_utente=?'

    id_foto = list(c.execute(query, t))[0][0]
    
    c.close()
    return "foto_uploaded_succ"


def change_foto_utente(id_utente, filename):
    c = conn.cursor()
    query = 'UPDATE UTENTE SET fotopath=? WHERE id=?'

    t = (filename, id_utente)

    c.execute(query,t)
    conn.commit()

    c.close()
    return "foto_uploaded_succ"


def remove_foto(id_foto):
    c = conn.cursor()
    query = 'DELETE FROM FOTO WHERE id=?'

    t = (id_foto,)

    c.execute(query,t)
    conn.commit()
    c.close()
    return "foto_removed"


def add_elemento(nome,descr,id_categoria,id_utente,foto_list):
    c = conn.cursor()

    query = 'INSERT INTO elemento (nome,descr,id_categoria) VALUES (?,?,?)'
    t = (nome,descr,id_categoria)
    c.execute(query,t)
    conn.commit()
    
    query = 'SELECT ELEMENTO.*, CATEGORIA.nome FROM ELEMENTO JOIN CATEGORIA ON CATEGORIA.id = ELEMENTO.id_categoria WHERE ELEMENTO.nome=? and ELEMENTO.descr=?'
    t = (nome,descr)

    result = list(c.execute(query,t))

    id_elemento = result[0][0]


    for ft in foto_list:
        upload_foto_elem(id_elemento, id_utente, ft)


    query = "INSERT INTO MODIFICA (data, id_utente, id_elemento, first) VALUES (?,?,?,0)"
    data = gen.get_now()
    t = (data, id_utente, id_elemento)
    c.execute(query,t)
    conn.commit()

    c.close()
    return elemento(id_elemento)


def categorie():
    c = conn.cursor()
    query = 'SELECT * FROM CATEGORIA'
    result = list(c.execute(query))
    result = [gen.categoria(l) for l in result]
    c.close()
    return result


def utente(id_utente):
    c = conn.cursor()
    query = "SELECT * FROM UTENTE WHERE UTENTE.ID=?"
    t = (id_utente,)
    utente = list(c.execute(query, t))[0]

    query = "SELECT A.total*5 + B.total + C.total*3 + D.total*(-2) + E.total + F.total*2 + G.total*(-15) + H.total*(-30) + I.total*(-30) FROM (select count(*) as total from recensione where id_utente = ? and data < ?) as A, (select count(*) as total from voto_rec where id_utente = ? and data < ?) as B, (select count(*) as total from recensione join voto_rec on recensione.id = voto_rec.id_recensione  where recensione.id_utente = ? and voto_rec.voto > 0 and voto_rec.data < ?) as C, (select count(*) as total from recensione join voto_rec on recensione.id = voto_rec.id_recensione  where recensione.id_utente = ? and voto_rec.voto < 0 and voto_rec.data < ?) as D, (select count(*) as total from risposta where risposta.id_utente = ? and data < ?) as E, (select count(*) as total from risposta join domanda on risposta.id = domanda.id_risposta_top and risposta.id_utente = ? and risposta.data < ?) as F, (select count(*) as total from foto where foto.id_utente = ? and foto.rimossa > 0 and foto.data < ?) as G, (select count(*) as total from modifica where modifica.id_utente = ? and modifica.rimossa > 0 and modifica.data < ?) as H, (select count(*) as total from recensione where recensione.id_utente = ? and recensione.rimossa > 0 and recensione.data < ?) as I"
    now = gen.get_now()
    t = (id_utente, now)*9

    level = list(c.execute(query,t))[0][0]

    grafico = user_rating_graph(id_utente,resolution)

    res = gen.utente_red(utente,pt.get_livello(level),grafico)

    c.close()
    return res


def exists_elemento(nome):
    c = conn.cursor()
    query = "SELECT * FROM ELEMENTO WHERE NOME=? COLLATE NOCASE"
    t = (nome,)
    result = list(c.execute(query,t))
    c.close()
    return result


def exists_utente(nome,email):
    c = conn.cursor()
    query = "SELECT * FROM UTENTE WHERE nome=? COLLATE NOCASE"
    t = (nome,)
    result = list(c.execute(query,t))

    if len(result) > 0:
        return 1

    query = "SELECT * FROM UTENTE WHERE email=? COLLATE NOCASE"
    t = (email,)
    result = list(c.execute(query,t))
    c.close()

    if len(result) > 0:
        return 2
    else:
        return 0


def exists_utente1(email):
    c = conn.cursor()
    query = "SELECT * FROM UTENTE WHERE EMAIL=?"
    t = (email,)
    result = list(c.execute(query,t))
    c.close()
    return len(result) > 0


def register(nome,email,password,lang):
    c = conn.cursor()

    code = int(random.random()*999999)
    passw = gen.getsha(password)
    query = "INSERT INTO UTENTE (nome,email,data_reg,password,lingua,code) VALUES (?,?,?,?,?,?)"
    t = (nome,email,gen.get_now(),passw,lang,code)
    c.execute(query,t)
    conn.commit()

    query = "SELECT * FROM UTENTE WHERE nome=? AND email=?"
    t = (nome,email)
    result = list(c.execute(query,t))
    if len(result) is not 1:
        raise Exception

    mail.send_mail_reg(code,email)
    c.close()
    return login(email,password)


def facebook(nome,email,password,lang):
    c = conn.cursor()

    password1 = gen.getsha(password)
    query = "INSERT INTO UTENTE (nome,email,data_reg,password,lingua,code,attivato) VALUES (?,?,?,?,?,0,1)"
    t = (nome,email,gen.get_now(),password1,lang)
    c.execute(query,t)
    conn.commit()

    query = "SELECT * FROM UTENTE WHERE nome=? AND email=?"
    t = (nome,email)
    result = list(c.execute(query,t))
    if len(result) is not 1:
        raise Exception

    c.close()
    return (email,password)


def attiva(id_utente,code):
    c = conn.cursor()

    query = "SELECT CODE FROM UTENTE WHERE id=?"
    t = (id_utente,)
    codeOriginal = list(c.execute(query,t))[0][0]

    if code != codeOriginal:
        c.close()
        raise IncorrectCodeException
    else:
        query = "UPDATE UTENTE SET attivato=1 WHERE id=?"
        t = (id_utente,)
        c.execute(query,t)
        conn.commit()
        c.close()

    return "activated_successfully"


def domande(id_elemento):
    c = conn.cursor()

    query = "SELECT id FROM DOMANDA WHERE id_elemento=?"

    t = (id_elemento,)
    result = list(c.execute(query,t))
    res = []
    for r in result:
        res.append(domanda(r[0]))
    c.close()
    return res


def domanda(id_domanda):
    c = conn.cursor()

    query = "SELECT * FROM DOMANDA WHERE id=?"

    t = (id_domanda,)
    result = list(c.execute(query,t))[0]

    domanda = {}
    domanda['id'] = result[0]
    domanda['data'] = result[1]
    domanda['testo'] = result[2]
    domanda['utente'] = utente(result[3])
    try:
        domanda['risposta_top'] = risposta(result[5])
    except:
        domanda['risposta_top'] = None

    query = "SELECT id FROM RISPOSTA WHERE RISPOSTA.id_domanda=?"
    t = (result[0],)

    domanda['risposte'] = []

    risp_ids = list(c.execute(query,t))
    for i in risp_ids:
        if i[0] is not result[5]:
            domanda['risposte'].append(risposta(i[0]))

    c.close()
    return domanda


def risposte(id_domanda):
    c = conn.cursor()

    query = "SELECT id FROM RISPOSTA WHERE id_domanda=?"
    t = (id_domanda,)
    result = list(c.execute(query,t))

    res = []
    for r in result:
        res.append(risposta(r[0]))

    c.close()
    return res


def risposta(id_risposta):
    c = conn.cursor()

    query = "SELECT * FROM RISPOSTA WHERE id=?"
    t = (id_risposta,)
    result = list(c.execute(query,t))[0]

    u = utente(result[4])
    risposta = gen.risposta(result,u)

    c.close()
    return risposta


def elemento(id_elemento):
    print (id_elemento,)
    c = conn.cursor()
    query = 'SELECT ELEMENTO.*, CATEGORIA.nome FROM ELEMENTO, CATEGORIA WHERE CATEGORIA.id = ELEMENTO.id_categoria and ELEMENTO.id=?'
    t = (id_elemento,)

    elemento = list(c.execute(query,t))[0]

    #ricerca delle foto
    query = 'SELECT * FROM FOTO WHERE id_elemento=?'
    t = (elemento[0],)
    foto = list(c.execute(query, t))

    #creazione del voto on the fly
    query = 'SELECT id, id_utente, voto FROM recensione WHERE id_elemento=? and rimossa = 0'
    t = (elemento[0],)
    rec_list = list(c.execute(query, t))

    counter_gut = .0
    counter_livelli = .0
 
    query = "SELECT case voto_up.totale + voto_down.totale when 0 then 0 else (voto_up.totale - voto_down.totale)*(voto_up.totale - voto_down.totale)/(voto_up.totale + voto_down.totale) END as rap from (select count(*) as totale from recensione join voto_rec on recensione.id = voto_rec.id_recensione and recensione.id = ? and voto_rec.voto > 0) as voto_up, (select count(*) as totale from recensione join voto_rec on recensione.id = voto_rec.id_recensione and recensione.id = ? and voto_rec.voto < 0) as voto_down"
    
    for r in rec_list:
        rec_id = r[0]
        user_id = r[1]
        stelle = r[2]

        t = (rec_id,rec_id)
        rap = list(c.execute(query,t))[0][0]
        livello = utente(user_id)['level']

        lv2 = livello['livello']*(1+(rap**(1.0/2))/5)
        gut = lv2*stelle
        counter_livelli += lv2
        counter_gut += gut

    c.close()
    rating = -1 if counter_livelli == 0 else counter_gut/counter_livelli

    d = domande(elemento[0])
    res = gen.elemento(elemento,rating,foto,d)
    return res


def seguiti(id_utente):
    c = conn.cursor()

    query = "SELECT UTENTE.id FROM SEGUE JOIN UTENTE ON SEGUE.id_utente_to = UTENTE.id WHERE SEGUE.id_utente_from=?"
    t = (id_utente,)
    result = list(c.execute(query,t))

    res = []
    for r in result:
        res.append(utente(r[0]))

    c.close()
    return res


def recensioni_utente(id_utente):
    c = conn.cursor()

    query = "SELECT id FROM RECENSIONE WHERE id_utente=? and rimossa=0"
    t = (id_utente,)
    result = list(c.execute(query,t))

    res = []
    for r in result:
        res.append(recensione(r[0]))
        
    c.close()
    return res


def recensioni_elemento(id_elemento):
    c = conn.cursor()

    query = "SELECT id FROM RECENSIONE WHERE id_elemento=? and rimossa=0"
    t = (id_elemento,)
    result = list(c.execute(query,t))

    res = []
    for r in result:
        res.append(recensione(r[0]))
        
    c.close()
    return res


def recensione(id_recensione):
    c = conn.cursor()

    query = "SELECT *, (SELECT count(*) FROM VOTO_REC WHERE voto > 0 and id_recensione = RECENSIONE.id) as votoup, (SELECT count(*) FROM VOTO_REC WHERE voto < 0 and id_recensione = RECENSIONE.id) as votodown FROM RECENSIONE WHERE RECENSIONE.id=?"
    t = (id_recensione,)
    result = list(c.execute(query,t))[0]
    rec = result[0:9]
    voti = result[9:11]

    elem = elemento(result[8])

    u = utente(result[7])
    
    res = gen.recensione(rec,elem,u,voti)
        
    c.close()
    return res


def add_view_rec(id_utente, id_recensione):
    c = conn.cursor()
    t = (id_utente, id_recensione)
    query = "SELECT * FROM VISITE_REC WHERE id_utente=? AND id_recensione=?"


    if len(list(c.execute(query,t))) > 0:
        t = (gen.get_now(),id_utente, id_recensione)
        query = "UPDATE VISITE_REC SET conto = conto + 1, last = ? WHERE id_utente=? AND id_recensione=?"
        c.execute(query,t)
    else:
        t = (id_utente, gen.get_now(),id_recensione)
        query = "INSERT INTO VISITE_REC(id_utente, conto, last ,id_recensione) VALUES (?,1,?,?)"
        c.execute(query,t)
    conn.commit()
    c.close()

    return "view_added"


def add_view_el(id_utente, id_elemento):
    if id_elemento is None:
        raise Exception
    c = conn.cursor()
    t = (id_utente, id_elemento)
    query = "SELECT * FROM VISITE_EL WHERE id_utente=? AND id_elemento=?"


    if len(list(c.execute(query,t))) > 0:
        t = (gen.get_now(),id_utente, id_elemento)
        query = "UPDATE VISITE_EL SET conto = conto + 1, last = ? WHERE id_utente=? AND id_elemento=?"
        c.execute(query,t)
    else:
        t = (id_utente, gen.get_now(),id_elemento)
        query = "INSERT INTO VISITE_EL(id_utente, conto, last ,id_elemento) VALUES (?,1,?,?)"
        c.execute(query,t)
    conn.commit()
    c.close()

    return "view_added"


def suggeriti(id_utente):
    res = []
    c = conn.cursor()
    query = 'SELECT id_elemento FROM VISITE_EL WHERE id_utente=? ORDER BY conto DESC LIMIT 5'
    t = (id_utente,)

    result = list(c.execute(query,t))

    res = []
    for r in result:
        res.append(elemento(r[0]))
    c.close()
    return res


def recenti(id_utente):
    res = []
    c = conn.cursor()
    query = 'SELECT id_elemento FROM VISITE_EL WHERE id_utente=? ORDER BY last DESC LIMIT 5'
    t = (id_utente,)

    result = list(c.execute(query,t))

    res = []
    for r in result:
        res.append(elemento(r[0]))
    c.close()
    return res


def update(id_utente):
    c = conn.cursor()

    query = "SELECT * FROM UTENTE WHERE id=?"
    t = (id_utente,)

    utente = list(c.execute(query, t))
    print utente
    res = utente[0]
    id_utente = res[0]

    query = "SELECT A.total*5 + B.total + C.total*3 + D.total*(-2) + E.total + F.total*2 + G.total*(-15) + H.total*(-30) + I.total*(-30) FROM (select count(*) as total from recensione where id_utente = ? and data < ?) as A, (select count(*) as total from voto_rec where id_utente = ? and data < ?) as B, (select count(*) as total from recensione join voto_rec on recensione.id = voto_rec.id_recensione  where recensione.id_utente = ? and voto_rec.voto > 0 and voto_rec.data < ?) as C, (select count(*) as total from recensione join voto_rec on recensione.id = voto_rec.id_recensione  where recensione.id_utente = ? and voto_rec.voto < 0 and voto_rec.data < ?) as D, (select count(*) as total from risposta where risposta.id_utente = ? and data < ?) as E, (select count(*) as total from risposta join domanda on risposta.id = domanda.id_risposta_top and risposta.id_utente = ? and risposta.data < ?) as F, (select count(*) as total from foto where foto.id_utente = ? and foto.rimossa > 0 and foto.data < ?) as G, (select count(*) as total from modifica where modifica.id_utente = ? and modifica.rimossa > 0 and modifica.data < ?) as H, (select count(*) as total from recensione where recensione.id_utente = ? and recensione.rimossa > 0 and recensione.data < ?) as I"
    now = gen.get_now()
    t = (id_utente, now)*9

    level = list(c.execute(query,t))[0][0]

    new_token = gen.getsha((res[3]+res[1]+res[2])[:40])

    grafico = user_rating_graph(id_utente,resolution)
    utente_final = gen.utente(res,pt.get_livello(level),new_token,grafico)

    data_now = datetime.datetime.fromtimestamp(gen.get_now())
    start_of_the_day = (datetime.datetime(data_now.year,data_now.month,data_now.day)  - datetime.datetime(1970, 1, 1)).total_seconds()
    
    t = (id_utente,start_of_the_day)
   
    query = "SELECT id FROM DOMANDA WHERE id_utente=? and data>?"
    just_domanda = len(list(c.execute(query,t)))

    query = "SELECT id FROM VOTO_REC WHERE id_utente=? and data>?"
    just_voto = len(list(c.execute(query,t)))
 
    query = "SELECT id FROM RECENSIONE WHERE id_utente=? and data>?"
    just_recensione = len(list(c.execute(query,t)))
 
    utente_final['domande_counter'] = utente_final['level']['max_dom'] - just_domanda
    utente_final['recensioni_counter'] = utente_final['level']['max_rec'] - just_recensione
    utente_final['voti_counter'] = utente_final['level']['max_voti'] - just_voto

    fine = {
        'utente': utente_final
    }

    c.close()
    return fine


def segnala_rec(id_utente, motivazione, id_recensione):
    c = conn.cursor()
    
    query = "INSERT INTO segnala_recensione(id_utente, motivazione, id_recensione) VALUES (?,?,?)"
    t = (id_utente, motivazione, id_recensione)

    c.execute(query, t)
    conn.commit()
    c.close()

    return "segnalato_correttamente"


def segnala_el(id_utente, motivazione, id_elemento):
    c = conn.cursor()
    
    query = "INSERT INTO segnala_elemento(id_utente, motivazione, id_elemento) VALUES (?,?,?)"
    t = (id_utente, motivazione, id_elemento)

    c.execute(query, t)
    conn.commit()
    c.close()

    return "segnalato_correttamente"


def add_preferito(id_utente, id_elemento):
    c = conn.cursor()
    
    query = "INSERT INTO PREFERITI (id_utente, id_elemento) VALUES (?,?)"
    t = (id_utente, id_elemento)
    c.execute(query, t)
    conn.commit()

    c.close()
    return "aggiunto_correttamente"


def remove_preferito(id_utente, id_elemento):
    c = conn.cursor()
    
    query = "DELETE FROM PREFERITI WHERE id_utente=? AND id_elemento=?"
    t = (id_utente, id_elemento)
    c.execute(query, t)
    conn.commit()

    c.close()
    return "rimosso_correttamente"


def add_seguito(id_utente_from, id_utente_to):
    c = conn.cursor()
    
    query = "INSERT INTO SEGUE (id_utente_from, id_utente_to) VALUES (?,?)"
    t = (id_utente_from, id_utente_to)
    c.execute(query, t)
    conn.commit()

    c.close()
    return "aggiunto_correttamente"


def remove_seguito(id_utente_from, id_utente_to):
    c = conn.cursor()
    
    query = "DELETE FROM SEGUE WHERE id_utente_from=? AND id_utente_to=?"
    t = (id_utente_from, id_utente_to)
    c.execute(query, t)
    conn.commit()

    c.close()
    return "rimosso_correttamente"


def add_domanda(testo, id_utente, id_elemento):
    c = conn.cursor()
    
    query = "INSERT INTO DOMANDA (testo, data, id_utente, id_elemento) VALUES (?,?,?,?)"
    t = (testo, gen.get_now(), id_utente, id_elemento)
    c.execute(query, t)
    conn.commit()

    c.close()
    return "aggiunta_correttamente"


def add_risposta(testo, id_utente, id_domanda):
    c = conn.cursor()
    data = gen.get_now()
    
    query = "INSERT INTO RISPOSTA (testo, data, id_utente, id_domanda) VALUES (?,?,?,?)"
    t = (testo, data, id_utente, id_domanda)
    c.execute(query, t)
    conn.commit()

    query = "SELECT id FROM RISPOSTA WHERE testo=? and data=? and id_utente=? and id_domanda=?"
    t = (testo, data, id_utente, id_domanda)
    id_risposta = list(c.execute(query, t))[0][0]

    notificaNuovaRispostaMiaDomanda(id_risposta)

    c.close()
    return "aggiunta_correttamente"


def vota_recensione(voto, id_utente, id_recensione):
    c = conn.cursor()
    data = gen.get_now()

    query = "SELECT * FROM VOTO_REC WHERE id_utente = ? and id_recensione = ?"
    t = (id_utente, id_recensione)

    esiste = len(list(c.execute(query,t))) > 0
    if esiste:
        query = "UPDATE VOTO_REC SET voto = ?, data = ? where id_utente = ? and id_recensione = ?"
        t = (voto, data, id_utente, id_recensione)
        c.execute(query, t)
    else:
        query = "INSERT INTO VOTO_REC (voto, data, id_utente, id_recensione) VALUES (?,?,?,?)"
        t = (voto, data, id_utente, id_recensione)
        c.execute(query, t)
    conn.commit()

    query = "SELECT id FROM VOTO_REC WHERE voto=? and data = ? and id_utente=? and id_recensione=?"
    t = (voto, data, id_utente, id_recensione)
    id_voto = list(c.execute(query, t))[0][0]

    notificaNuovoVotoMiaRecensione(id_voto)

    c.close()
    return "voto_aggiunto_gut"


def has_voto(id_utente, id_recensione):
    c = conn.cursor()
    data = gen.get_now()

    res = 0

    query = "SELECT voto FROM VOTO_REC WHERE id_utente = ? and id_recensione = ?"
    t = (id_utente, id_recensione)

    result = list(c.execute(query,t))
    
    if len(result) > 0:
        res = result[0][0]

    c.close()
    return res

def set_top_risposta(id_risposta, id_utente):
    c = conn.cursor()
    
    query = "SELECT DOMANDA.id_utente, DOMANDA.id FROM RISPOSTA JOIN DOMANDA ON RISPOSTA.id_domanda=DOMANDA.id WHERE RISPOSTA.id=?"
    t = (id_risposta,)
    result = list(c.execute(query, t))[0]
    id_res = result[0]
    id_domanda = result[1]

    if id_res is not id_utente:
        raise NotAuthError

    query = "UPDATE DOMANDA SET id_risposta_top=? WHERE id=?"
    t = (id_risposta,id_domanda)
    c.execute(query, t)
    conn.commit()

    notificaMiaMigliorRisposta(id_risposta)
    c.close()

    return "top_settato_gut"


def reinvio_email(id_utente):
    c = conn.cursor()

    query = "SELECT code,email FROM UTENTE WHERE id=?"
    t = (id_utente,)

    result = list(c.execute(query,t))
    if len(result) is not 1:
        raise Exception

    code = result[0][0]
    email = result[0][1]
    mail.send_mail_reg(code,email)
    c.close()
    return "email_reinviata"


def nuova_password(email):
    c = conn.cursor()
    N = 10
    new_pass = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))

    encrypted_pass = gen.getsha(new_pass)

    query = "UPDATE UTENTE SET password=? WHERE email=?"

    t = (encrypted_pass,email)
    c.execute(query,t)
    conn.commit()
    c.close()

    mail.send_mail_new_pass(email, new_pass)
    return "nuova_pass_sent"


def modifica_elemento(id_utente, id_elemento, nome, descrizione, categoria):
    c = conn.cursor()

    query = "INSERT INTO MODIFICA (data, id_utente, id_elemento) VALUES (?,?,?)"
    data = gen.get_now()
    t = (data, id_utente, id_elemento)
    c.execute(query,t)

    if nome is not None:

        query = "UPDATE ELEMENTO SET nome=? WHERE id=?"
        t = (nome, id_elemento)
        c.execute(query,t)

    if descrizione is not None:

        query = "UPDATE ELEMENTO SET descr=? WHERE id=?"
        t = (descrizione, id_elemento)
        c.execute(query,t)

    if int(categoria) > 0:

        query = "UPDATE ELEMENTO SET id_categoria = ? WHERE id=?"
        t = (categoria, id_elemento)
        print t
        c.execute(query,t)

    conn.commit()
    c.close()
    return "modificato"


def change_data(id_utente, nome, email, passwordOld, passwordNew):
    c = conn.cursor()

    if nome is not None:

        query = "UPDATE UTENTE SET nome=? WHERE id=?"
        t = (nome, id_utente)

        c.execute(query,t)
        conn.commit()

    if email is not None:

        query = "UPDATE UTENTE SET email=?, attivato=0 WHERE id=?"
        t = (email, id_utente)

        c.execute(query,t)
        conn.commit()

    if passwordOld is not None and passwordNew is not None:

        passwordOld = gen.getsha(passwordOld)
        passwordNew = gen.getsha(passwordNew)

        query = "SELECT * FROM UTENTE WHERE id=? and password=?"
        t = (id_utente, passwordOld)
        if(len(list(c.execute(query,t))) == 0):
            raise WrongPasswordException

        query = "UPDATE UTENTE SET password=? WHERE id=?"
        t = (passwordNew, id_utente)

        c.execute(query,t)
        conn.commit()

    c.close()
    return "modificato"


def autocomplete():
    c = conn.cursor()

    query = "SELECT nome FROM elemento"
    t = ()

    l = list(c.execute(query,t))
    res = [a[0] for a in l]
    c.close()

    return res


def ticket(id_utente,testo):
    c = conn.cursor()

    query = "INSERT INTO assistenza (id_utente, data, testo) VALUES (?,?,?)"
    t = (id_utente, gen.get_now(), testo)
    c.execute(query,t)
    conn.commit()
    c.close()

    return "segnalazione_aggiunta"


def classifica():
    c = conn.cursor()

    query = "SELECT id FROM UTENTE"
    t = ()

    lista_id = list(c.execute(query,t))
    c.close()

    res = [utente(id_ut[0]) for id_ut in lista_id]
    res = sorted(res, key=lambda k: k['level']['punteggio'], reverse=True)
    
    return res


def add_recensione(titolo, testo, voto, id_elemento, id_utente, img_name):
    c = conn.cursor()

    data = gen.get_now()
    query = "INSERT INTO RECENSIONE (voto, fotopath, descr, titolo, data, id_utente, id_elemento) VALUES (?,?,?,?,?,?,?)"
    t = (voto,img_name,testo,titolo,data,id_utente,id_elemento)

    c.execute(query,t)

    conn.commit()

    query = "SELECT id FROM RECENSIONE WHERE voto=? and descr=? and titolo=? and data=? and id_utente=? and id_elemento=?"
    t = (voto,testo,titolo,data,id_utente,id_elemento)

    id_recensione = list(c.execute(query,t))[0][0]

    print "Recensione inserita"
    notificaNuovaRecensioneUtenteSeguo(id_recensione)
    notificaNuovaRecensioneOggettoSeguo(id_recensione)

    c.close()
    return recensione(id_recensione)


#id INTEGER PRIMARY KEY AUTOINCREMENT,
    #data INTEGER NOT NULL,
    #-- TIPI: 0->NuovaRecensioneUtenteCheSeguo, 1->NuovaRecensioneOggettoCheSeguo, 2->NuovoVotoMiaRecensione, 3->NuovaRispostaMiaDomanda, 4->MiaMigliorRisposta
    #tipo INTEGER,
    #id_rec INTEGER,
    #id_domanda INTEGER,
    #id_risposta INTEGER,
    #FOREIGN KEY(id_rec) REFERENCES recensione(id),
    #FOREIGN KEY(id_domanda) REFERENCES domanda(id),
    #FOREIGN KEY(id_risposta) REFERENCES risposta(id)


def notificaNuovaRecensioneUtenteSeguo(id_recensione):
    print "Inserimento notifica"
    c = conn.cursor()
    data = gen.get_now()

    query = "SELECT id_utente FROM RECENSIONE WHERE id=?"
    t = (id_recensione,)

    id_utente = list(c.execute(query,t))[0][0]

    query = "SELECT UTENTE.id FROM segue JOIN UTENTE ON segue.id_utente_from=UTENTE.id WHERE segue.id_utente_to=? and UTENTE.NuovaRecensioneUtenteCheSeguo > 0"
    t = (id_utente,)

    utenti_list_id = list(c.execute(query,t))
    notifiche = []

    query = "INSERT INTO notifica(id_utente,data,tipo,id_rec) VALUES (?,?,?,?)"
    query2 = "SELECT id FROM notifica WHERE id_utente = ? and data = ? and tipo = ? and id_rec = ?"
    for i in utenti_list_id:
        t = (i[0],data, 0,id_recensione)
        c.execute(query,t)
        conn.commit()
        notifiche.append(notifica_from_id(list(c.execute(query2,t))[0][0]))

    print "Notifiche inserite", len(notifiche), notifiche
    print "Inizio a spedire"
    for notif in notifiche:
        try:
            send_notification(notif)
            print "Spedita: ", notif
        except Exception as e:
            print e
    
    c.close()
    return "aggiunta_correttamente"


def notificaNuovaRecensioneOggettoSeguo(id_recensione):
    c = conn.cursor()
    data = gen.get_now()

    query = "SELECT id_elemento FROM RECENSIONE WHERE id=?"
    t = (id_recensione,)

    id_elemento = list(c.execute(query,t))[0][0]

    query = "SELECT UTENTE.id FROM PREFERITI JOIN UTENTE ON PREFERITI.id_utente=UTENTE.id WHERE PREFERITI.id_elemento=? and UTENTE.NuovaRecensioneOggettoCheSeguo > 0"
    t = (id_elemento,)

    utenti_list_id = list(c.execute(query,t))

    notifiche = []

    query = "INSERT INTO notifica(id_utente,data,tipo,id_rec) VALUES (?,?,?,?)"
    query2 = "SELECT id FROM notifica WHERE id_utente = ? and data = ? and tipo = ? and id_rec = ?"
    for i in utenti_list_id:
        t = (i[0],data, 1,id_recensione)
        c.execute(query,t)
        conn.commit()
        notifiche.append(notifica_from_id(list(c.execute(query2,t))[0][0]))

    print "Notifiche inserite"
    for notif in notifiche:
        try:
            send_notification(notif)
        except Exception as e:
            print e

    c.close()
    return "aggiunta_correttamente"


def notificaNuovoVotoMiaRecensione(id_voto):
    c = conn.cursor()
    data = gen.get_now()

    query = "SELECT id_recensione FROM VOTO_REC WHERE id=?"
    t = (id_voto,)

    id_recensione = list(c.execute(query,t))[0][0]

    query = "SELECT UTENTE.id FROM RECENSIONE JOIN UTENTE ON RECENSIONE.id_utente=UTENTE.id WHERE RECENSIONE.id=? and UTENTE.NuovoVotoMiaRecensione > 0"
    t = (id_recensione,)

    result = list(c.execute(query,t))

    if len(result) == 1:
        id_utente = result[0][0]

        query = "INSERT INTO notifica(id_utente,data,tipo,id_voto) VALUES (?,?,?,?)"
        t = (id_utente,data,2,id_voto)
        c.execute(query,t)
        conn.commit()

        query2 = "SELECT id FROM notifica WHERE id_utente = ? and data = ? and tipo = ? and id_voto = ?"
        notif = notifica_from_id(list(c.execute(query2,t))[0][0])
        try:
            send_notification(notif)
        except Exception as e:
            print e

    c.close()
    return "aggiunta_correttamente"


def notificaNuovaRispostaMiaDomanda(id_risposta):
    c = conn.cursor()
    data = gen.get_now()

    query = "SELECT id_domanda FROM RISPOSTA WHERE id=?"
    t = (id_risposta,)

    id_domanda = list(c.execute(query,t))[0][0]

    query = "SELECT UTENTE.id FROM DOMANDA JOIN UTENTE ON DOMANDA.id_utente=UTENTE.id WHERE DOMANDA.id=? and UTENTE.NuovaRispostaMiaDomanda > 0"
    t = (id_domanda,)

    result = list(c.execute(query,t))
    if len(result) == 1:
        id_utente = result[0][0]

        query = "INSERT INTO notifica(id_utente,data,tipo,id_risposta) VALUES (?,?,?,?)"
        t = (id_utente,data,3,id_risposta)
        c.execute(query,t)
        conn.commit()

        query2 = "SELECT id FROM notifica WHERE id_utente = ? and data = ? and tipo = ? and id_risposta = ?"
        notif = notifica_from_id(list(c.execute(query2,t))[0][0])
        try:
            send_notification(notif)
        except Exception as e:
            print e

    c.close()
    return "aggiunta_correttamente"


def notificaMiaMigliorRisposta(id_risposta):
    c = conn.cursor()
    data = gen.get_now()

    query = "SELECT UTENTE.id FROM RISPOSTA JOIN UTENTE ON RISPOSTA.id_utente=UTENTE.id WHERE RISPOSTA.id=? and UTENTE.MiaMigliorRisposta > 0"
    t = (id_risposta,)

    result = list(c.execute(query,t))
    if len(result) == 1:
        id_utente = result[0][0]

        query = "INSERT INTO notifica(id_utente,data,tipo,id_risposta) VALUES (?,?,?,?)"
        t = (id_utente,data,4,id_risposta)
        c.execute(query,t)
        conn.commit()

        query2 = "SELECT id FROM notifica WHERE id_utente = ? and data = ? and tipo = ? and id_risposta = ?"
        notif = notifica_from_id(list(c.execute(query2,t))[0][0])
        try:
            send_notification(notif)
        except Exception as e:
            print e

    c.close()
    return "aggiunta_correttamente"


def notifica(id_utente):
    c = conn.cursor()

    query = "SELECT * FROM NOTIFICA WHERE id_utente=?"
    t = (id_utente,)

    res = []
    
    result = list(c.execute(query,t))

    for notif in result:
        tmp = gen.notifica(notif)
        tipo = notif[3]
        if tipo <= 1:
            tmp['recensione'] = recensione(notif[4])
        elif tipo == 2:
            query = "SELECT * FROM VOTO_REC WHERE id=?"
            t = (notif[7],)
            tmp['voto'] = gen.voto(list(c.execute(query,t))[0])
            tmp['voto']['utente'] = utente(tmp['voto']['id_utente'])
            tmp['voto']['recensione'] = recensione(tmp['voto']['id_recensione'])
        else:
            tmp['risposta'] = risposta(notif[6])
            query = "SELECT DOMANDA.id_elemento FROM DOMANDA JOIN RISPOSTA ON DOMANDA.id=RISPOSTA.id_domanda WHERE RISPOSTA.id=?"
            t = (notif[6],)
            id_elemento = list(c.execute(query,t))[0][0]
            tmp['elemento'] = elemento(id_elemento)

        res.append(tmp)
    c.close()
    return res


def numero_notifiche(id_utente):
    c = conn.cursor()

    query = "SELECT * FROM NOTIFICA WHERE id_utente=?"
    t = (id_utente,)

    res = len(list(c.execute(query,t)))
    c.close()
    return res


def notifica_from_id(id_notifica):
    c = conn.cursor()

    query = "SELECT * FROM NOTIFICA WHERE id=?"
    t = (id_notifica,)
    
    notif = list(c.execute(query,t))[0]
    
    res = gen.notifica(notif)
    tipo = notif[3]
    if tipo <= 1:
        res['recensione'] = recensione(notif[4])
    elif tipo == 2:
        query = "SELECT * FROM VOTO_REC WHERE id=?"
        t = (notif[7],)
        res['voto'] = gen.voto(list(c.execute(query,t))[0])
        res['voto']['utente'] = utente(res['voto']['id_utente'])
        res['voto']['recensione'] = recensione(res['voto']['id_recensione'])
    else:
        res['risposta'] = risposta(notif[6])
        query = "SELECT DOMANDA.id_elemento FROM DOMANDA JOIN RISPOSTA ON DOMANDA.id=RISPOSTA.id_domanda WHERE RISPOSTA.id=?"
        t = (notif[6],)
        id_elemento = list(c.execute(query,t))[0][0]
        res['elemento'] = elemento(id_elemento)
    
    c.close()
    return res


def remove_notifica(id_notifica,id_utente):
    c = conn.cursor()

    query = "DELETE FROM NOTIFICA WHERE id=? and id_utente=?"
    t = (id_notifica,id_utente)

    c.execute(query,t)

    conn.commit()
    c.close()
    return "rimossa_correttamente"


def nuove_impostazioni(id_utente, NuovaRecensioneUtenteCheSeguo, NuovaRecensioneOggettoCheSeguo, NuovoVotoMiaRecensione, NuovaRispostaMiaDomanda, MiaMigliorRisposta):
    c = conn.cursor()
    print (NuovaRecensioneUtenteCheSeguo, NuovaRecensioneOggettoCheSeguo, NuovoVotoMiaRecensione, NuovaRispostaMiaDomanda, MiaMigliorRisposta)
    query = "UPDATE UTENTE SET NuovaRecensioneUtenteCheSeguo = ?, NuovaRecensioneOggettoCheSeguo = ?, NuovoVotoMiaRecensione = ?, NuovaRispostaMiaDomanda = ?, MiaMigliorRisposta = ? WHERE id = ?"
    t = (NuovaRecensioneUtenteCheSeguo, NuovaRecensioneOggettoCheSeguo, NuovoVotoMiaRecensione, NuovaRispostaMiaDomanda, MiaMigliorRisposta, id_utente)

    c.execute(query,t)
    conn.commit()
    c.close()
    return "notifiche_aggiorante"



def best_of():
    c = conn.cursor()

    query = "SELECT id FROM ELEMENTO order by RANDOM() LIMIT 15"
    t = ()

    element_list = []
    for a in list(c.execute(query,t)):
        element_list.append(elemento(a[0]))

    c.close()
    newlist = sorted(element_list, key=lambda k: k['rating'], reverse=True)

    return newlist[:5]


def most_seen():
    c = conn.cursor()

    query = "SELECT id_elemento FROM VISITE_EL GROUP BY id_elemento ORDER BY sum(conto) DESC LIMIT 5"

    element_list = []

    result = list(c.execute(query))
    print result

    for a in result:
        element_list.append(elemento(a[0]))

    c.close()

    return element_list


def is_preferito(id_utente,id_elemento):
    c = conn.cursor()

    query = "SELECT * FROM PREFERITI WHERE id_utente=? and id_elemento=?"
    t = (id_utente,id_elemento)
    
    res = len(list(c.execute(query,t)))

    if res == 0:
        return "no"
    
    return "si"


def is_seguito(id_utente_from, id_utente_to):
    c = conn.cursor()

    query = "SELECT * FROM SEGUE WHERE id_utente_from=? and id_utente_to=?"
    t = (id_utente_from,id_utente_to)
    
    res = len(list(c.execute(query,t)))

    if res == 0:
        return "no"
    
    return "si"


def just_recensito(id_utente, id_elemento):
    c = conn.cursor()

    query = "SELECT * FROM RECENSIONE WHERE id_utente=? and id_elemento=?"
    t = (id_utente, id_elemento)
    
    res = len(list(c.execute(query,t)))

    if res == 0:
        return "no"
    
    return "si"


def visita(id_utente, id_elemento):
    add_view_el(id_utente, id_elemento)
    return 'OK'


def send_notification(notifica):

    id_notifica = notifica['id']
    id_utente = notifica['id_utente']
    print "\n\nSending notifica_id: ",id_notifica , id_utente , "\n\n"

    MY_API_KEY = "AIzaSyAGRKbZdNaf4_FWOxLWCupjM7x_GmRfdYQ"
    data={
        "to" : "/topics/my_little_topic",
        "data": {
            "id_notifica" : id_notifica,
            "id_utente" : id_utente
        }
    }
    dataAsJSON = json.dumps(data)
    request = Request(
        "https://gcm-http.googleapis.com/gcm/send",
        dataAsJSON,
        {
            "Authorization" : "key="+MY_API_KEY,
            "Content-type" : "application/json"
        }
    )
    print urlopen(request).read()



