tabella_punteggi = []

punteggi = open("punteggi.csv","r")

for line in punteggi:
	line = [int(x) for x in line.split(',')]
	tmp = {}
	tmp['livello'] = line[0]
	tmp['points_down'] = line[1]
	tmp['max_rec'] = line[2]
	tmp['max_voti'] = line[3]
	tmp['max_dom'] = line[4]
	tabella_punteggi.append(tmp)

def get_livello(punteggio):
	if punteggio <= 0:
		res = tabella_punteggi[0]
		res['punteggio'] = punteggio
		res['points_up'] = tabella_punteggi[1]['points_down']
		return res

	for a in range(len(tabella_punteggi)):
		if punteggio < tabella_punteggi[a]['points_down']:
			res = tabella_punteggi[a-1]
			res['punteggio'] = punteggio
			res['points_up'] = tabella_punteggi[a]['points_down']
			return res

	res = tabella_punteggi[-1]
	res['punteggio'] = punteggio
	res['points_up'] = -1
	return res

