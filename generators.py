import hashlib
import time

def utente(utente,level, token,grafico):
    res = {}
    res['id'] = utente[0]
    res['nome'] = utente[1]
    res['email'] = utente[2]
    res['fotopath'] = utente[4]
    res['data_reg'] = utente[5]
    res['attivato'] = utente[6]
    res['impostazioni'] = {}
    res['impostazioni']['NuovaRecensioneUtenteCheSeguo'] = utente[7]
    res['impostazioni']['NuovaRecensioneOggettoCheSeguo'] = utente[8]
    res['impostazioni']['NuovoVotoMiaRecensione'] = utente[9]
    res['impostazioni']['NuovaRispostaMiaDomanda'] = utente[10]
    res['impostazioni']['MiaMigliorRisposta'] = utente[11]
    res['impostazioni']['lingua'] = utente[12]
    res['level'] = level
    res['token'] = token
    res['grafico'] = grafico
    return res


def utente_red(utente,level,grafico):
    res = {}
    res['id'] = utente[0]
    res['nome'] = utente[1]
    res['fotopath'] = utente[4]
    res['data_reg'] = utente[5]
    res['level'] = level
    res['grafico'] = grafico
    return res


def elemento(elemento,rating,fotos,domande):
    res = {}
    res['id'] = elemento[0]
    res['nome'] = elemento[1]
    res['descr'] = elemento[2]
    res['categoria'] = elemento[4]
    res['fotos'] = []

    for ft in fotos:
        res['fotos'].append(foto(ft))

    res['domande'] = domande
    res['rating'] = rating
    return res


def elemento_red(elemento):
    res = {}
    res['id'] = elemento[0]
    res['nome'] = elemento[1]
    res['descr'] = elemento[2]
    res['categoria'] = elemento[4]
    return res


def foto(f):
    res = {}
    res['id'] = f[0]
    res['data'] = f[1]
    res['id_utente'] = f[2]
    res['path'] = f[4]
    res['id_elemento'] = f[5]
    return res


def recensione(rec,elemento,utente,voti):
    res = {}
    res['id'] = rec[0]
    res['voto'] = rec[1]
    res['fotopath'] = rec[2]
    res['descr'] = rec[3]
    res['titolo'] = rec[4]
    res['data'] = rec[5]
    res['id_utente'] = rec[7]
    res['id_elemento'] = rec[8]
    res['elemento'] = elemento
    res['utente'] = utente
    res['voti_positivi'] = voti[0]
    res['voti_negativi'] = voti[1]
    return res


def risposta(risp,utente):
    risposta = {}
    risposta['id'] = risp[0]
    risposta['data'] = risp[1]
    risposta['testo'] = risp[2]
    risposta['id_domanda'] = risp[3]
    risposta['utente'] = utente
    return risposta


def categoria(cat):
    res = {}
    res['id'] = cat[0]
    res['nome'] = cat[1]
    return res


def notifica(notif):
    res = {}
    res['id'] = notif[0]
    res['id_utente'] = notif[1]
    res['data'] = notif[2]
    res['tipo'] = notif[3]
    return res


def voto(v):
    res = {}
    res['id'] = v[0]
    res['data'] = v[1]
    res['id_utente'] = v[2]
    res['id_recensione'] = v[3]
    res['voto'] = v[4]
    return res

def getsha(string):
    return hashlib.sha256(string).hexdigest()

def get_now():
    return int(time.time())




