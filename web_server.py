import BaseHTTPServer
import cgi
import ssl
import sqlite3 as sql
import urlparse
import hashlib
import generators as gen
import db_query as db
import json
import os
import sys
import random

HOST_NAME = '46.101.255.199' # !!!REMEMBER TO CHANGE THIS!!!
PORT_NUMBER = 5500 # Maybe set this to 5500.

foto_folder = 'foto/'

valid_tokens = db.get_token()


empty = {
    'error': 'use POST'
}

def success(x):
    res = {}
    res['status'] = 'OK'
    res['result'] = x
    print str(x)[:300], '\n'
    return res

def failed(x,m):
    res = {}
    res['status'] = 'ERROR'
    res['message'] = m
    res['result'] = x
    return res



def split_foto(fotoname):
    parts = fotoname.split('.')
    return (parts[0],parts[1])

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        
    def do_GET(s):
        s.send_response(200)
        s.send_header("Content-type", "application/json")
        s.end_headers()
        s.wfile.write("GET requests not supported")

        
    def do_POST(s):

        fields = cgi.FieldStorage(
            fp=s.rfile,
            headers=s.headers,
            environ={'REQUEST_METHOD':'POST',
                'CONTENT_TYPE':s.headers['Content-Type'],
            }
        )

        path = fields.getvalue('path')
        id_utente = -1

        print "\n\nREQUEST: %s\n" % path
        print fields, "\n"

        if path is None:
            s.send_response(200)
            s.send_header("Content-type", "application/json")
            s.end_headers()
        
            s.wfile.write(json.dumps(failed(None,"Path missing")))

        ########### SENZA TOKEN - PUBBLICO ###############
        elif path == 'login':
            try:
                username = fields.getvalue('username')
                password = fields.getvalue('password')
                print username, ": ", password
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()
                tmp = db.login(username,password)
                valid_tokens[tmp['utente']['token']] = tmp['utente']['id']
                s.wfile.write(json.dumps(success(tmp)))

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"wrong_username_password")))
            return


        elif path == 'registra':
            try:
                nome = fields.getvalue('nome')
                email = fields.getvalue('email')
                password = fields.getvalue('password')
                lang = fields.getvalue('lingua')
                
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()

                k = db.exists_utente(nome,email)

                if k > 0:
                    if k == 1:
                        s.wfile.write(json.dumps(failed(None,"nome_usato")))
                    else:
                        s.wfile.write(json.dumps(failed(None,"email_usata")))
                    return

                utente = db.register(nome,email,password,lang)
                valid_tokens[utente['utente']['token']] = utente['utente']['id']
                s.wfile.write(json.dumps(success(utente)))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"Wrong parameters")))


        elif path == 'facebook':
            try:
                nome = fields.getvalue('nome')
                email = fields.getvalue('email')
                password = fields.getvalue('password')
                lang = fields.getvalue('lingua')
                
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()

                k = db.exists_utente(nome,email)

                if k > 0:
                    if k == 1:
                        s.wfile.write(json.dumps(failed(None,"nome_usato")))
                    else:
                        s.wfile.write(json.dumps(failed(None,"email_usata")))
                    return

                tmp = db.facebook(nome,email,password,lang)
                
                tmp1 = db.login(tmp[0],tmp[1])
                valid_tokens[tmp1['utente']['token']] = tmp1['utente']['id']
                s.wfile.write(json.dumps(success(tmp1)))

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"Wrong parameters")))


        elif path == 'nuova_password':
            try:
                email = fields.getvalue('email')

                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()

                if not db.exists_utente1(email):
                    s.wfile.write(json.dumps(failed(None,"email_non_esistente")))
                else:
                    s.wfile.write(json.dumps(success(db.nuova_password(email))))
            except db.MailProblemsException as e:
                print type(e), str(e)
                s.wfile.write(json.dumps(failed(None,"mail_problems")))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


        elif path == 'foto':
            try:
                fotoname = fields.getvalue('fotoname')
            
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()
            
                with open(foto_folder + fotoname) as f:
                    res = {}
                    res['foto'] = f.read()
                    s.wfile.write(success(res))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None, "foto_not_found_or_iternal_error")))


        elif path == 'elemento':
            try:
                id_elemento = fields.getvalue('id_elemento')

                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()

                try:
                    id_utente = valid_tokens[fields.getvalue('token')]
                    db.add_view_el(id_utente,id_elemento)
                except:
                    pass

                s.wfile.write(json.dumps(success(db.elemento(id_elemento))))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))
            

        elif path == 'categorie':
            try:
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()
            
                s.wfile.write(json.dumps(success(db.categorie())))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


        elif path == 'utente':
            try:
                id_utente = fields.getvalue('id_utente')
                
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()
            
                s.wfile.write(json.dumps(success(db.utente(id_utente))))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


        elif path == 'domanda':
            try:
                id_domanda = fields.getvalue('id_domanda')
                
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()
            
                s.wfile.write(json.dumps(success(db.domanda(id_domanda))))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


        elif path == 'domande':
            try:
                id_elemento = fields.getvalue('id_elemento')
                
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()
            
                s.wfile.write(json.dumps(success(db.domande(id_elemento))))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


        elif path == 'risposte':
            try:
                id_domanda = fields.getvalue('id_domanda')
                
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()
            
                s.wfile.write(json.dumps(success(db.risposte(id_domanda))))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


        elif path == 'risposta':
            try:
                id_risposta = fields.getvalue('id_risposta')
                
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()
            
                s.wfile.write(json.dumps(success(db.risposta(id_risposta))))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


        elif path == 'recensioni_utente':
            try:
                id_utente = fields.getvalue('id_utente')
                
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()
            
                s.wfile.write(json.dumps(success(db.recensioni_utente(id_utente))))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


        elif path == 'recensioni_elemento':
            try:
                id_elemento = fields.getvalue('id_elemento')
                
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()
            
                s.wfile.write(json.dumps(success(db.recensioni_elemento(id_elemento))))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


        elif path == 'recensione':
            try:
                id_recensione = fields.getvalue('id_recensione')
                
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()
                
                try:
                    id_utente = valid_tokens[fields.getvalue('token')]
                    db.add_view_rec(id_utente,id_recensione)
                except:
                    pass
            
                s.wfile.write(json.dumps(success(db.recensione(id_recensione))))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


        elif path == 'autocomplete':
            try:
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()
            
                s.wfile.write(json.dumps(success(db.autocomplete())))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"internal_error")))    

        elif path == 'search_elemento':
            try:
                nome = fields.getvalue('nome')
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()
            
                s.wfile.write(json.dumps(success(db.search_elemento(nome))))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"internal_error")))  

        elif path == 'classifica':
            try:
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()
            
                s.wfile.write(json.dumps(success(db.classifica())))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"internal_error")))


        elif path == 'best_of':
            try:
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()
            
                s.wfile.write(json.dumps(success(db.best_of())))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


        elif path == 'most_seen':
            try:
                s.send_response(200)
                s.send_header("Content-type", "application/json")
                s.end_headers()
            
                s.wfile.write(json.dumps(success(db.most_seen())))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print str(e), exc_type, fname, exc_tb.tb_lineno
                s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


        elif fields.getvalue('token') is None or fields.getvalue('token') not in valid_tokens:
            s.send_response(200)
            s.send_header("Content-type", "text/html")
            s.end_headers()

            s.wfile.write(failed(None,"not_logged"))
            return


        ####### CON TOKEN - PRIVATE #############
        else:
            token = fields.getvalue('token')
            id_utente = valid_tokens[token]
    
            if path == 'preferiti':
                try:
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.preferiti(id_utente))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))

            elif path == 'is_preferito':
                id_elemento = fields.getvalue('id_elemento')
                try:
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.is_preferito(id_utente,id_elemento))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))

            
            elif path == 'is_seguito':
                id_utente_to = fields.getvalue('id_utente')
                try:
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.is_seguito(id_utente,id_utente_to))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


            elif path == 'add_elemento':
                try:
                    nome = fields.getvalue('nome')
                    descr = fields.getvalue('descr')
                    id_categoria = fields.getvalue('id_categoria')

                    test = db.exists_elemento(nome)
                    print nome,descr,id_categoria,test
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                    
                    if len(test) >= 1:
                        fine = failed(test[0],"element_already_exists")
                    else:
                        foto_number = int(fields.getvalue('foto_number'))

                        foto_list = []
                        print foto_number
                        for i in range(foto_number):
                            img_data = fields.getvalue('foto'+str(i))
                            print img_data[:100]
                            img_name = gen.getsha(img_data)
                            foto_list.append(img_name)

                            fh = open("foto/" + img_name, "wb")
                            fh.write(img_data)
                            fh.close()

                        fine = success(db.add_elemento(nome,descr,id_categoria,id_utente,foto_list))
                    s.wfile.write(json.dumps(fine))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


            elif path == 'notifica':
                try:
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.notifica(id_utente))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"internal_error")))
            

            elif path == 'add_foto_elem':
                try:
                    img_data = fields.getvalue('img_data')
                    id_elemento = fields.getvalue('id_elemento')

                    img_name = gen.getsha(img_data)

                    fh = open("foto/" + img_name, "wb")
                    fh.write(img_data)
                    fh.close()

                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.upload_foto_elem(id_elemento, id_utente, img_name))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"internal_error")))


            elif path == 'change_foto_utente':
                try:
                    img_data = fields.getvalue('img_data')

                    img_name = gen.getsha(img_data)

                    fh = open("foto/" + img_name, "wb")
                    fh.write(img_data)
                    fh.close()

                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.change_foto_utente(id_utente, img_name))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"internal_error")))


            elif path == 'attiva':
                try:
                    code = fields.getvalue('code')
                    
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.attiva(id_utente,code))))
                except db.IncorrectCodeException as e:
                    s.wfile.write(json.dumps(failed(None,"wrong_code")))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


            elif path == 'seguiti':
                try:
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                    
                    s.wfile.write(json.dumps(success(db.seguiti(id_utente))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


            elif path == 'suggeriti':
                try:
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.suggeriti(id_utente))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


            elif path == 'recenti':
                try:
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.recenti(id_utente))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


            elif path == 'update':
                try:
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    tmp = db.update(id_utente)
                    valid_tokens[tmp['utente']['token']] = tmp['utente']['id']
                    s.wfile.write(json.dumps(success(tmp)))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


            elif path == 'remove_foto':
                try:
                    id_foto = fields.getvalue('id_foto')
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.remove_foto(id_foto))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


            elif path == 'segnala_elemento':
                try:
                    id_elemento = fields.getvalue('id_elemento')
                    motivazione = fields.getvalue('motivazione')

                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.segnala_el(id_utente, motivazione, id_elemento))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


            elif path == 'segnala_recensione':
                try:
                    id_recensione = fields.getvalue('id_recensione')
                    motivazione = fields.getvalue('motivazione')

                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.segnala_rec(id_utente, motivazione, id_recensione))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


            elif path == 'add_preferito':
                try:
                    id_elemento = fields.getvalue('id_elemento')

                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.add_preferito(id_utente,id_elemento))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


            elif path == 'remove_preferito':
                try:
                    id_elemento = fields.getvalue('id_elemento')

                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.remove_preferito(id_utente,id_elemento))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


            elif path == 'add_domanda':
                try:
                    testo = fields.getvalue('testo')
                    id_elemento = fields.getvalue('id_elemento')

                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.add_domanda(testo, id_utente, id_elemento))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


            elif path == 'add_risposta':
                try:
                    testo = fields.getvalue('testo')
                    id_domanda = fields.getvalue('id_domanda')
                    
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.add_risposta(testo, id_utente, id_domanda))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


            elif path == 'vota_recensione':
                try:
                    voto = fields.getvalue('voto')
                    id_recensione = fields.getvalue('id_recensione')

                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.vota_recensione(voto, id_utente, id_recensione))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


            elif path == 'has_voto':
                try:
                    id_recensione = fields.getvalue('id_recensione')

                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.has_voto(id_utente, id_recensione))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))


            elif path == 'set_top_risposta':
                try:
                    id_risposta = fields.getvalue('id_risposta')

                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.set_top_risposta(id_risposta, id_utente))))
                except sql.IntegrityError:
                    s.wfile.write(json.dumps(failed(None,"cannot_change_best_response")))
                except db.NotAuthError:
                    s.wfile.write(json.dumps(failed(None,"not_answer_owner")))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"wrong_id_or_internal_error")))
                

            elif path == 'reinvio_email':
                try:
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.reinvio_email(id_utente))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"internal_error")))


            elif path == 'change_data':
                try:
                    nome = fields.getvalue('nome')
                    email = fields.getvalue('email')
                    password_new = fields.getvalue('password_new')
                    password_old = fields.getvalue('password_old')
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.change_data(id_utente, nome, email, password_new, password_old))))
                except db.WrongPasswordException as e:
                    print type(e), str(e)
                    s.wfile.write(json.dumps(failed(None,"wrong_old_password")))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"internal_error")))


            elif path == 'ticket':
                try:
                    testo = fields.getvalue('testo')
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.ticket(id_utente, testo))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"internal_error")))    


            elif path == 'notifica_from_id':
                try:
                    id_notifica = fields.getvalue('id_notifica')
                    
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.notifica_from_id(id_notifica))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"internal_error")))


            elif path == 'remove_notifica':
                try:
                    id_notifica = fields.getvalue('id_notifica')
                    
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.remove_notifica(id_notifica,id_utente))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"internal_error")))


            elif path == 'add_recensione':
                try:
                    titolo = fields.getvalue('titolo')
                    testo = fields.getvalue('testo')
                    voto = fields.getvalue('voto')
                    id_elemento = fields.getvalue('id_elemento')

                    img_data = fields.getvalue('foto')

                    if img_data != 'no_foto':
                        img_name = gen.getsha(img_data)

                        fh = open("foto/" + img_name, "wb")
                        fh.write(img_data)
                        fh.close()
                    else:
                        img_name = None
                    print img_name
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.add_recensione(titolo, testo, voto, id_elemento, id_utente, img_name))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"internal_error")))


            elif path == 'nuove_impostazioni':
                try:
                    NuovaRecensioneUtenteCheSeguo = fields.getvalue('NuovaRecensioneUtenteCheSeguo')
                    NuovaRecensioneOggettoCheSeguo = fields.getvalue('NuovaRecensioneOggettoCheSeguo')
                    NuovoVotoMiaRecensione = fields.getvalue('NuovoVotoMiaRecensione')
                    NuovaRispostaMiaDomanda = fields.getvalue('NuovaRispostaMiaDomanda')
                    MiaMigliorRisposta = fields.getvalue('MiaMigliorRisposta')

                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.nuove_impostazioni(id_utente, NuovaRecensioneUtenteCheSeguo, NuovaRecensioneOggettoCheSeguo, NuovoVotoMiaRecensione, NuovaRispostaMiaDomanda, MiaMigliorRisposta))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"internal_error")))

            
            elif path == 'modifica_elemento':
                try:
                    id_elemento = fields.getvalue('id_elemento')
                    nome = fields.getvalue('nome')    
                    descrizione = fields.getvalue('descrizione')
                    categoria = fields.getvalue('categoria')

                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.modifica_elemento(id_utente, id_elemento, nome, descrizione, categoria))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"internal_error")))


            elif path == 'add_seguito':
                try:
                    id_utente_to = fields.getvalue('id_utente')
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.add_seguito(id_utente, id_utente_to))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"internal_error")))


            elif path == 'remove_seguito':
                try:
                    id_utente_to = fields.getvalue('id_utente')
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.remove_seguito(id_utente, id_utente_to))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"internal_error")))


            elif path == 'just_recensito':
                try:
                    id_elemento = fields.getvalue('id_elemento')
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.just_recensito(id_utente, id_elemento))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"internal_error")))


            elif path == 'visita':
                try:
                    id_elemento = fields.getvalue('id_elemento')
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.visita(id_utente, id_elemento))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"internal_error")))

            elif path == 'numero_notifiche':
                try:
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                
                    s.wfile.write(json.dumps(success(db.numero_notifiche(id_utente))))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"internal_error")))


            # DEFALUT CASE - NO PATH
            else:
                try:
                    s.send_response(200)
                    s.send_header("Content-type", "application/json")
                    s.end_headers()
                    
                    s.wfile.write(json.dumps(failed("path_not_found")))
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print str(e), exc_type, fname, exc_tb.tb_lineno
                    s.wfile.write(json.dumps(failed(None,"internal_error")))



httpd = BaseHTTPServer.HTTPServer((HOST_NAME, PORT_NUMBER), MyHandler)
httpd.socket = ssl.wrap_socket (httpd.socket, certfile='server.includesprivatekey.pem', server_side=True)
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    pass
