
import asyncio
import httpx
import json

async def test_mcp_connection():
    # URL e Token fornecidos pelo usuário
    url = "http://homeassistant.taild603b.ts.net:8000/api/mcp/sse"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhODBjMDA2NzdiNDY0MWZmOGZmYmYyNjY3MWQzZTM1ZCIsImlhdCI6MTc3Mjg1OTUwMiwiZXhwIjoyMDg4MjE5NTAyfQ.Pa16YfmvNaZJvIb1-K10sg7mnYUNPpUl7b129k-793k"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"--- Testando conexão MCP em {url} ---")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            print("1. Tentando conectar ao endpoint SSE...")
            # Simulando o início da conexão SSE
            async with client.stream("GET", url, headers=headers) as response:
                print(f"Status Code: {response.status_code}")
                
                if response.status_code != 200:
                    body = await response.aread()
                    print(f"Erro: {body.decode()}")
                    return

                print("Conectado! Aguardando evento de endpoint para mensagens...")
                
                # O primeiro evento deve ser o 'endpoint' para sabermos para onde enviar o POST
                async for line in response.iter_lines():
                    if line.startswith("event: endpoint"):
                        # Próxima linha deve ser data: ...
                        print(f"Recebido evento de endpoint: {line}")
                    elif line.startswith("data:"):
                        endpoint_url = line.replace("data:", "").strip()
                        print(f"URL de mensagens detectada: {endpoint_url}")
                        break
                else:
                    print("Erro: Não recebemos o evento 'endpoint' do SSE.")
                    return

                # Agora tentamos o handshake do MCP (Initializing)
                # O cliente envia um POST para o endpoint_url com o JSON RPC 'initialize'
                msg_url = f"http://homeassistant.taild603b.ts.net:8000{endpoint_url}"
                print(f"2. Tentando handshake MCP em {msg_url}...")
                
                init_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "TestClient", "version": "1.0.0"}
                    }
                }
                
                msg_response = await client.post(msg_url, json=init_payload, headers=headers)
                print(f"Status POST: {msg_response.status_code}")
                
                if msg_response.status_code >= 400:
                    print(f"Erro no POST: {msg_response.text}")
                    return

                print("Aguardando resposta de inicialização no stream SSE...")
                
                # Agora devemos ver no stream SSE a resposta do servidor
                async for line in response.iter_lines():
                    if line.startswith("data:"):
                        data_json = line.replace("data:", "").strip()
                        print(f"Resposta recebida: {data_json}")
                        break
                else:
                    print("Erro: Não recebemos resposta no stream SSE após o POST.")

    except Exception as e:
        print(f"Erro durante o teste: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_connection())
