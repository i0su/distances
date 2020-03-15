# Egunean behin distantziak (eta iraupenak)

## Nola erabili

### 1. Ingurune birtuala sortu

```bash
$ python3 -m venv myenv
```

### 2. Ingurune birtuala aktibatu

```bash
$ source myenv/bin/activate
```

### 3. Dependentziak instalatu

```bash
$ pip3 install -r requirements.txt
```

### 4. Programaren exekuzioa

```bash
$ python3 distantziak.py d
```
Non d, sortu nahi diren galdera kopurua den (osokoa)

## Galderen izaera
Bi galdera mota sortzen dira: distantziei buruzkoak eta iraupenei buruzkoak.

Bietan 600x400 pixeletako mapa bat sortuko da, non bi puntu markatzen diren.

Jokalariak asmatu beharko du zein distantzia/iraupen dagoen bi puntuen artean, kotxez bide laburrena eginez. Distantziaren kasuan unitatea kilometroa izango da, eta iraupenarenean orduak eta minutuak.

## Distantziak eta iraupenak sortzeko programa