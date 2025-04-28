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
- L'autenticazione è disabilitata (`DISABLE_AUTHENTICATION=1`)
- NON utilizzare questa configurazione in ambienti di produzione o esposti su Internet
