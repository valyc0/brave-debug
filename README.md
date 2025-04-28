# Brave Debug Container

Un container Docker basato su KASM che esegue il browser Brave con capacità di debugging remote abilitate.

## Descrizione

Questo progetto fornisce un ambiente containerizzato per eseguire il browser Brave con il debugging remoto abilitato sulla porta 9222. È basato sull'immagine Kasm Workspaces, che permette l'accesso al browser sia tramite interfaccia web VNC che tramite il Chrome DevTools Protocol (CDP).

È particolarmente utile per:
- Automazione dei test browser
- Debug di applicazioni web
- Simulazione di interazioni utente
- Esecuzione di browser in ambiente isolato

## Contenuto

- `Dockerfile`: Configurazione per costruire l'immagine Docker
- `build-brave-debug.sh`: Script per compilare l'immagine
- `start-brave-debug.sh`: Script per avviare il container
- `test_login.py`: Script di esempio per testare un form di login
- `login.html` e `welcome.html`: Pagine di esempio per il test di login
- `brave-install-scripts/`: Script di installazione per Brave
- `custom_startup.sh`: Script personalizzato per avviare Brave con le opzioni di debugging

## Prerequisiti

- Docker installato e funzionante
- Python 3.x (per gli script di test)
- Librerie Python: websockets, requests (per gli script di test)

## Installazione

1. Clona o copia questa directory nel tuo sistema

2. Rendi eseguibili gli script:
   ```
   chmod +x build-brave-debug.sh start-brave-debug.sh
   ```

3. Costruisci l'immagine Docker:
   ```
   ./build-brave-debug.sh
   ```

## Utilizzo

### Avvio del container

```bash
./start-brave-debug.sh
```

Questo comando:
- Ferma e rimuove eventuali container brave-debug preesistenti
- Avvia un nuovo container con:
  - Networking in modalità host (condivide lo stack di rete dell'host)
  - Autenticazione disabilitata
  - Debugging remoto abilitato sulla porta 9222

### Accesso con credenziali predefinite

Quando l'autenticazione è abilitata in Kasm ma non sono specificate credenziali personalizzate, puoi accedere usando le credenziali predefinite:

- **Username:** `kasm_user`
- **Password:** `password`

Per accedere:
1. Apri un browser sul tuo computer host
2. Naviga a `http://localhost:6901`
3. Inserisci `kasm_user` come username e `password` come password
4. Clicca su "Accedi" o "Log In"

Queste credenziali sono impostate come valori predefiniti nell'immagine Kasm di base.

### Configurazione di Autenticazione in Kasm

Nella configurazione predefinita, l'autenticazione è disabilitata per semplicità (`DISABLE_AUTHENTICATION=1`). Per abilitare l'autenticazione e specificare username e password personalizzati, modifica lo script `start-brave-debug.sh` come segue:

1. **Rimuovi** la linea:
   ```
   -e DISABLE_AUTHENTICATION=1 \
   ```

2. **Aggiungi** invece queste variabili di ambiente:
   ```
   -e KASM_USER=mio_username \
   -e KASM_PASSWORD=mia_password \
   ```

Esempio completo:
```bash
docker run -d --name brave-debug \
  --network=host \
  --shm-size=512m \
  -e KASM_PORT=6901 \
  -e KASM_USER=mio_username \
  -e KASM_PASSWORD=mia_password \
  -e ENABLE_REMOTE_DEBUGGING=true \
  -e REMOTE_DEBUGGING_PORT=9222 \
  -e REMOTE_DEBUGGING_ADDRESS=0.0.0.0 \
  -e CHROME_ARGS="--no-sandbox --remote-debugging-address=0.0.0.0 --remote-debugging-port=9222" \
  brave-debug
```

Puoi anche configurare il tipo di autenticazione usando le seguenti opzioni:

- **Standard username/password**:
  ```
  -e KASM_USER=mio_username \
  -e KASM_PASSWORD=mia_password \
  ```

- **VNC password (interfaccia grafica)**:
  ```
  -e VNC_PW=mia_password_vnc \
  ```

- **Token-based authentication**:
  ```
  -e KASM_AUTH_TOKEN=mio_token_segreto \
  ```

Dopo aver modificato lo script e aver avviato il container, accedi all'interfaccia Kasm su http://localhost:6901 e inserisci le credenziali configurate.

### Accesso al browser

- **Interfaccia browser:** https://localhost:6901
- **Endpoint debugging:** http://localhost:9222
- **Dettagli debugging:** http://localhost:9222/json/list

### Debug e automazione

Il container espone il Chrome DevTools Protocol sulla porta 9222, consentendo:

1. **Debug con Chrome DevTools:**
   - Apri Chrome/Edge sul tuo computer
   - Naviga a `http://localhost:9222`
   - Seleziona una scheda per ispezionarla

2. **Automazione via script:**
   - Usa lo script `test_login.py` come esempio
   - Comunica con il browser via WebSocket
   - Esempio: `python test_login.py`

3. **Comandi rapidi con curl:**
   ```bash
   # Elenco delle schede aperte
   curl http://localhost:9222/json/list
   
   # Apri un nuovo URL
   curl -X PUT "http://localhost:9222/json/new?http://example.com"
   ```

## Esempio di automazione

Lo script `test_login.py` dimostra come:
1. Connettersi al browser via WebSocket
2. Navigare a una pagina di login (`login.html`)
3. Compilare automaticamente i campi username e password
4. Fare clic sul pulsante di login
5. Verificare la navigazione alla pagina di benvenuto (`welcome.html`)

Per eseguirlo:
```bash
python test_login.py
```

## Struttura della rete

- Il container utilizza `--network=host`, quindi:
  - `localhost` nel container corrisponde a `localhost` sull'host
  - Un server web in esecuzione su `localhost:8080` dell'host è accessibile come `http://localhost:8080` dal browser nel container

## Risoluzione dei problemi

- **Il browser non si avvia**: Verifica eventuali errori nei log con `docker logs brave-debug`
- **Impossibile connettersi all'interfaccia**: Assicurati che le porte 6901 e 9222 non siano utilizzate da altri servizi
- **Errori negli script di test**: Verifica che le dipendenze Python siano installate (`pip install websockets requests`)

## Note di sicurezza

- Il container viene avviato con `--no-sandbox` per semplicità in ambiente di test
- Nella configurazione predefinita, l'autenticazione è disabilitata (`DISABLE_AUTHENTICATION=1`)
- Per ambienti di produzione o condivisi:
  - Abilita sempre l'autenticazione come descritto sopra
  - Considera l'utilizzo di credenziali forti e token di autenticazione
  - Valuta la possibilità di limitare l'accesso alla porta 9222 solo a indirizzi IP specifici
- NON esporre le porte 6901 e 9222 direttamente su Internet senza adeguate misure di sicurezza
