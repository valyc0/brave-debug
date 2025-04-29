import asyncio
import json
import aiohttp
from pyppeteer import connect
import sys
from datetime import datetime
import threading
import queue
import signal

# Coda per i messaggi di log
log_queue = queue.Queue()

def log_writer():
    """Thread che scrive i log su file"""
    with open('browser_logs.txt', 'a', encoding='utf-8') as f:
        while True:
            message = log_queue.get()
            if message is None:  # segnale di stop
                break
            f.write(f"{message}\n")
            f.flush()

async def get_ws_endpoint():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:9222/json/version') as response:
            if response.status == 200:
                data = await response.json()
                return data.get('webSocketDebuggerUrl')
            else:
                log_queue.put(f"Errore nel recupero dell'endpoint: {response.status}")
                content = await response.text()
                log_queue.put(f"Contenuto: {content}")
                return None

async def handle_console_message(msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_type = msg.type.upper()
    text = msg.text
    
    if msg.args:
        try:
            args = [await arg.jsonValue() for arg in msg.args]
            text = " ".join(str(arg) for arg in args if arg is not None)
        except:
            pass
    
    log_queue.put(f"[{timestamp}] {log_type}: {text}")
    
    if log_type in ['ERROR', 'WARNING']:
        location = msg.location
        if location:
            log_queue.put(f"Location: {location['url']}:{location['lineNumber']}")
        stack = getattr(msg, 'stackTrace', None)
        if stack:
            log_queue.put("Stack trace:")
            for frame in stack:
                log_queue.put(f"  at {frame.get('functionName', '(anonymous)')} ({frame.get('url', 'unknown')}:{frame.get('lineNumber', '?')})")

async def handle_page_error(error):
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_queue.put(f"[{timestamp}] ERRORE PAGINA:")
    log_queue.put(f"Message: {error}")
    if hasattr(error, 'stack'):
        log_queue.put("Stack trace:")
        log_queue.put(error.stack)

async def handle_request(request):
    timestamp = datetime.now().strftime('%H:%M:%S')
    method = request.method
    url = request.url
    headers = request.headers
    
    log_queue.put(f"[{timestamp}] RICHIESTA {method} {url}")
    if headers:
        log_queue.put("Headers:")
        log_queue.put(json.dumps(headers, indent=2))
    
    if request.postData:
        try:
            post_data = json.loads(request.postData)
            log_queue.put("POST Data:")
            log_queue.put(json.dumps(post_data, indent=2))
        except:
            log_queue.put(f"POST Data (raw): {request.postData}")

async def handle_response(response):
    timestamp = datetime.now().strftime('%H:%M:%S')
    status = response.status
    url = response.url
    headers = response.headers
    
    log_queue.put(f"[{timestamp}] RISPOSTA {status} {url}")
    if headers:
        log_queue.put("Headers:")
        log_queue.put(json.dumps(headers, indent=2))
    
    try:
        if 'json' in headers.get('content-type', ''):
            resp_data = await response.json()
            log_queue.put("Response Data:")
            log_queue.put(json.dumps(resp_data, indent=2))
    except:
        pass

async def monitor_browser():
    try:
        log_queue.put("Connessione al browser...")
        ws_endpoint = await get_ws_endpoint()
        if not ws_endpoint:
            return

        browser = await connect(
            browserWSEndpoint=ws_endpoint,
            ignoreHTTPSErrors=True,
        )
        log_queue.put("Browser connesso. Monitoraggio attivo...")
        
        pages = await browser.pages()
        if not pages:
            log_queue.put("Nessuna pagina trovata")
            return
            
        for page in pages:
            page.on('console', lambda msg: asyncio.create_task(handle_console_message(msg)))
            page.on('pageerror', lambda err: asyncio.create_task(handle_page_error(err)))
            page.on('request', lambda req: asyncio.create_task(handle_request(req)))
            page.on('response', lambda res: asyncio.create_task(handle_response(res)))
            
            await page.evaluateOnNewDocument('''
                window.onerror = function(message, source, lineno, colno, error) {
                    console.error({
                        message: message,
                        source: source,
                        lineno: lineno,
                        colno: colno,
                        error: error && error.stack
                    });
                    return false;
                };
                
                window.onunhandledrejection = function(event) {
                    console.error('Unhandled Promise Rejection:', event.reason);
                };
            ''')
        
        while True:
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        log_queue.put("\nMonitoraggio terminato")
    except Exception as e:
        log_queue.put(f"Errore durante il monitoraggio: {str(e)}")

def main():
    # Avvia il thread per la scrittura dei log
    log_thread = threading.Thread(target=log_writer)
    log_thread.start()
    
    print("Monitor browser avviato. I log vengono salvati in browser_logs.txt")
    print("Premi Ctrl+C per terminare")
    
    # Avvia il loop di monitoraggio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    monitor_task = None
    
    try:
        monitor_task = loop.create_task(monitor_browser())
        loop.run_forever()
    except KeyboardInterrupt:
        if monitor_task:
            monitor_task.cancel()
        log_queue.put(None)  # Segnale per terminare il thread di logging
        log_thread.join()
        print("\nMonitoraggio terminato")
    finally:
        loop.close()

if __name__ == "__main__":
    main()