#!/usr/bin/env python3
import asyncio
import json
import sys
import time
import websockets
import requests

# --- Configurazione ---
LOGIN_PAGE_URL = "http://localhost:8080/login.html"
WELCOME_PAGE_URL_END = "/welcome.html"
DEBUGGER_URL = "http://localhost:9222"
USERNAME = "python_user"
PASSWORD = "python_password"
TIMEOUT = 5  # Timeout in secondi per le operazioni
# --------------------

async def connect_to_browser():
    """Ottiene il WebSocket URL del browser e si connette."""
    try:
        # Ottieni l'elenco delle schede disponibili
        response = requests.get(f"{DEBUGGER_URL}/json/list")
        response.raise_for_status()
        targets = response.json()
        
        # Cerca una scheda esistente o crea una nuova
        page_info = None
        for target in targets:
            if target["type"] == "page" and "webSocketDebuggerUrl" in target:
                page_info = target
                break
        
        if not page_info:
            print("Nessuna scheda disponibile. Creando una nuova...")
            response = requests.put(f"{DEBUGGER_URL}/json/new")
            response.raise_for_status()
            page_info = response.json()
        
        websocket_url = page_info["webSocketDebuggerUrl"]
        print(f"Connessione al WebSocket: {websocket_url}")
        
        return page_info["id"], websocket_url
    
    except Exception as e:
        print(f"Errore durante la connessione al browser: {e}", file=sys.stderr)
        return None, None

async def send_command(ws, method, params=None):
    """Invia un comando al browser tramite WebSocket CDP con timeout."""
    message_id = int(time.time() * 1000)  # Usa il timestamp come ID unico
    message = {
        "id": message_id,
        "method": method
    }
    if params:
        message["params"] = params
    
    try:
        print(f"Invio comando: {method}")
        await ws.send(json.dumps(message))
        
        # Attendi la risposta con l'ID corrispondente
        start_time = time.time()
        while True:
            if time.time() - start_time > TIMEOUT:
                print(f"TIMEOUT: Nessuna risposta ricevuta per il comando {method} dopo {TIMEOUT} secondi")
                return {"error": {"message": f"Timeout waiting for response to {method}"}}
            
            try:
                # Impostiamo un timeout anche nella ricezione
                response_text = await asyncio.wait_for(ws.recv(), timeout=TIMEOUT)
                response = json.loads(response_text)
                
                if "id" in response and response["id"] == message_id:
                    return response
                # Se ricevi un evento, scartalo e continua ad attendere la risposta
                if "method" in response:
                    print(f"Evento ricevuto: {response['method']}")
            except asyncio.TimeoutError:
                print(f"Timeout nella ricezione dei messaggi WebSocket per {method}")
                return {"error": {"message": f"WebSocket receive timeout for {method}"}}

    except Exception as e:
        print(f"Errore durante l'invio/ricezione del comando {method}: {e}", file=sys.stderr)
        return {"error": {"message": str(e)}}

async def main():
    """Funzione principale per il test di login."""
    print("Avvio del test di login...")
    
    # Verifica che il server di debug sia attivo
    try:
        response = requests.get(f"{DEBUGGER_URL}/json/version", timeout=3)
        response.raise_for_status()
        print("Server di debug raggiungibile.")
    except Exception as e:
        print(f"ERRORE: Server di debug non raggiungibile su {DEBUGGER_URL}: {e}", file=sys.stderr)
        print("Verifica che il container brave-debug sia in esecuzione.", file=sys.stderr)
        return 1
    
    # Verifica che il server web sia attivo
    try:
        response = requests.head(LOGIN_PAGE_URL, timeout=3)
        response.raise_for_status()
        print("Server web raggiungibile.")
    except Exception as e:
        print(f"ERRORE: Server web non raggiungibile su {LOGIN_PAGE_URL}: {e}", file=sys.stderr)
        print("Verifica che il server web sia in esecuzione.", file=sys.stderr)
        return 1
    
    target_id, ws_url = await connect_to_browser()
    if not ws_url:
        print("Impossibile ottenere l'URL WebSocket. Uscita.")
        return 1
    
    try:
        # Impostiamo un timeout per la connessione WebSocket
        async with websockets.connect(ws_url, close_timeout=TIMEOUT) as ws:
            print(f"WebSocket connesso. Target ID: {target_id}")
            
            # Navigazione alla pagina di login
            print(f"Navigando a: {LOGIN_PAGE_URL}")
            result = await send_command(ws, "Page.navigate", {"url": LOGIN_PAGE_URL})
            if "error" in result:
                print(f"Errore durante la navigazione: {result['error']}")
                return 1
            
            # Attendere che la pagina sia caricata completamente
            print("Attendendo il caricamento della pagina...")
            await asyncio.sleep(2)  # Attesa semplice
            
            # Verifica che la pagina sia effettivamente caricata
            load_check = await send_command(ws, "Runtime.evaluate", {"expression": "document.readyState"})
            if "error" in load_check:
                print(f"Errore nel verificare lo stato della pagina: {load_check['error']}")
                return 1
            
            if "result" in load_check and "value" in load_check["result"]["result"]:
                ready_state = load_check["result"]["result"]["value"]
                print(f"Stato della pagina: {ready_state}")
                if ready_state != "complete":
                    print(f"AVVISO: La pagina potrebbe non essere completamente caricata.")
            
            # Compila il campo username
            print(f"Compilazione username: {USERNAME}")
            js_username = f'document.getElementById("username").value = "{USERNAME}";'
            username_result = await send_command(ws, "Runtime.evaluate", {"expression": js_username})
            if "error" in username_result:
                print(f"Errore nel compilare il campo username: {username_result['error']}")
                return 1
            
            # Compila il campo password
            print(f"Compilazione password: {PASSWORD}")
            js_password = f'document.getElementById("password").value = "{PASSWORD}";'
            password_result = await send_command(ws, "Runtime.evaluate", {"expression": js_password})
            if "error" in password_result:
                print(f"Errore nel compilare il campo password: {password_result['error']}")
                return 1
            
            # Verifica i valori inseriti
            result = await send_command(ws, "Runtime.evaluate", 
                {"expression": 'document.getElementById("username").value + " / " + document.getElementById("password").value'})
            if "error" in result:
                print(f"Errore nel verificare i valori inseriti: {result['error']}")
                return 1
            
            if "result" in result and "value" in result["result"]["result"]:
                print(f"Valori inseriti: {result['result']['result']['value']}")
            
            # Clicca sul pulsante di login
            print("Clic sul pulsante login...")
            click_js = 'document.querySelector("button[onclick=\\"performLogin()\\"]").click();'
            click_result = await send_command(ws, "Runtime.evaluate", {"expression": click_js})
            if "error" in click_result:
                print(f"Errore nel cliccare il pulsante di login: {click_result['error']}")
                return 1
            
            # Attendi la navigazione
            print("Attendendo la navigazione dopo il login...")
            await asyncio.sleep(2)  # Attesa semplice
            
            # Verifica l'URL corrente
            result = await send_command(ws, "Runtime.evaluate", {"expression": "window.location.href"})
            if "error" in result:
                print(f"Errore nel verificare l'URL finale: {result['error']}")
                return 1
            
            if "result" in result and "value" in result["result"]["result"]:
                final_url = result["result"]["result"]["value"]
                print(f"URL finale: {final_url}")
                
                if WELCOME_PAGE_URL_END in final_url:
                    print("\n--- TEST SUPERATO ---")
                    print("Login simulato e navigazione alla pagina di benvenuto avvenuta con successo!")
                    return 0
                else:
                    print("\n--- TEST FALLITO ---")
                    print(f"L'URL finale '{final_url}' non contiene la pagina di benvenuto attesa ('{WELCOME_PAGE_URL_END}').")
                    return 1
            
            print("\n--- TEST FALLITO ---")
            print("Impossibile verificare l'URL finale.")
            return 1
                
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connessione WebSocket chiusa inaspettatamente: {e}", file=sys.stderr)
        return 1
    except asyncio.TimeoutError as e:
        print(f"Timeout durante l'esecuzione: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Errore imprevisto: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.get_event_loop().run_until_complete(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTest interrotto dall'utente.")
        sys.exit(130)  # 128 + SIGINT(2)
    except Exception as e:
        print(f"Errore fatale: {e}", file=sys.stderr)
        sys.exit(1)