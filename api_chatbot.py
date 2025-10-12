from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from ml_predictor import predictor
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
import uuid
from datetime import datetime
from fastapi.responses import FileResponse

from crewai import Crew, Task, Process
from agentes_chatbot import (
    agente_analista_dados,
    agente_especialista_clinico,
    agente_gestor_administrativo,
    agente_assistente_pesquisa
)
from memory_manager import ConversationMemory


from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from auth_jwt import authenticate_user, create_access_token, verify_token
from datetime import timedelta


app = FastAPI(title="Chatbot Inteligente para Gestão de Saúde", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    agent_used: str

class SessionInfo(BaseModel):
    session_id: str
    created_at: str
    message_count: int

# ============================================================================
# GERENCIAMENTO DE SESSÕES
# ============================================================================

sessions: Dict[str, ConversationMemory] = {}

def get_or_create_session(session_id: Optional[str] = None) -> tuple[str, ConversationMemory]:
    """Retorna ou cria uma sessão"""
    if session_id and session_id in sessions:
        return session_id, sessions[session_id]
    
    # Criar nova sessão
    new_id = session_id or str(uuid.uuid4())
    sessions[new_id] = ConversationMemory()
    return new_id, sessions[new_id]

# ============================================================================
# ROTEADOR INTELIGENTE DE AGENTES
# ============================================================================

def route_to_agent(message: str, context: str) -> tuple[Any, str]:
    """
    Decide qual agente é mais adequado para responder
    
    Returns:
        (agente, nome_agente)
    """
    message_lower = message.lower()
    
    # Palavras-chave para cada agente
    keywords_map = {
        'dados': ['quantos', 'estatística', 'média', 'total', 'percentual', 'análise', 'gráfico', 'dados'],
        'clinico': ['protocolo', 'tratamento', 'diagnóstico', 'guideline', 'medicamento', 'clínico', 'paciente'],
        'administrativo': ['custo', 'orçamento', 'gestão', 'processo', 'eficiência', 'otimizar', 'recurso'],
        'pesquisa': ['documento', 'relatório', 'buscar', 'encontrar', 'onde está', 'informação sobre']
    }
    
    # Contar matches
    scores = {}
    for agent_type, keywords in keywords_map.items():
        score = sum(1 for kw in keywords if kw in message_lower)
        scores[agent_type] = score
    
    # Selecionar agente com maior score
    best_agent = max(scores, key=scores.get)
    
    if scores[best_agent] == 0:
        # Padrão: assistente de pesquisa
        best_agent = 'pesquisa'
    
    agent_map = {
        'dados': (agente_analista_dados, "Analista de Dados"),
        'clinico': (agente_especialista_clinico, "Especialista Clínico"),
        'administrativo': (agente_gestor_administrativo, "Gestor Administrativo"),
        'pesquisa': (agente_assistente_pesquisa, "Assistente de Pesquisa")
    }
    
    return agent_map[best_agent]

# ============================================================================
# ENDPOINTS
# ============================================================================
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint that returns a JWT token.
    Username: admin
    Password: admin
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")

    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage, username: str = Depends(verify_token)):
    """
    Endpoint principal do chatbot
    
    Fluxo:
    1. Identifica/cria sessão
    2. Adiciona mensagem ao histórico
    3. Seleciona agente apropriado
    4. Cria tarefa para o agente
    5. Executa e retorna resposta
    """
    try:
        # Gerenciar sessão
        session_id, memory = get_or_create_session(chat_message.session_id)
        
        # Adicionar mensagem do usuário ao histórico
        memory.add_message("user", chat_message.message)
        
        # Obter contexto
        context = memory.get_context(last_n=5)
        
        # Selecionar agente
        agent, agent_name = route_to_agent(chat_message.message, context)
        
        print(f"[Chat] Mensagem: {chat_message.message}")
        print(f"[Chat] Agente selecionado: {agent_name}")
        
        # Criar tarefa específica
        task = Task(
            description=(
                f"CONTEXTO DA CONVERSA:\n{context}\n\n"
                f"MENSAGEM ATUAL DO USUÁRIO:\n{chat_message.message}\n\n"
                f"INSTRUÇÕES:\n"
                f"1. Responda de forma conversacional e amigável\n"
                f"2. Use suas ferramentas quando necessário\n"
                f"3. Se precisar de dados, use 'consultar_banco_dados'\n"
                f"4. Se precisar de documentos, use 'ler_documentos'\n"
                f"5. Seja específico e cite fontes\n"
                f"6. Mantenha respostas concisas (máximo 300 palavras)\n"
            ),
            expected_output=(
                "Resposta conversacional, clara e objetiva, com no máximo 300 palavras. "
                "Se usar dados ou documentos, cite as fontes."
            ),
            agent=agent
        )
        
        # Criar crew com um único agente
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False
        )
        
        # Executar
        result = crew.kickoff()
        
        # Extrair resposta
        if hasattr(result, 'raw'):
            response_text = result.raw
        elif hasattr(result, 'output'):
            response_text = result.output
        else:
            response_text = str(result)
        
        # Adicionar resposta ao histórico
        memory.add_message("assistant", response_text, {'agent': agent_name})
        
        # Salvar sessão
        memory.save_session(session_id)
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            agent_used=agent_name
        )
        
    except Exception as e:
        print(f"[Chat] Erro: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")


@app.get("/sessions", response_model=List[SessionInfo])
async def list_sessions(username: str = Depends(verify_token)):
    """Lista todas as sessões ativas"""
    return [
        SessionInfo(
            session_id=sid,
            created_at=memory.current_session[0]['timestamp'] if memory.current_session else "N/A",
            message_count=len(memory.current_session)
        )
        for sid, memory in sessions.items()
    ]


@app.get("/session/{session_id}/history")
async def get_session_history(session_id: str, username: str = Depends(verify_token)):
    """Retorna histórico de uma sessão"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    memory = sessions[session_id]
    return {
        "session_id": session_id,
        "messages": memory.current_session
    }


@app.delete("/session/{session_id}")
async def delete_session(session_id: str, username: str = Depends(verify_token)):
    """Deleta uma sessão"""
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "Sessão deletada com sucesso"}
    raise HTTPException(status_code=404, detail="Sessão não encontrada")


@app.post("/session/{session_id}/clear")
async def clear_session(session_id: str, username: str = Depends(verify_token)):
    """Limpa o histórico de uma sessão mas mantém a sessão"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    sessions[session_id].current_session = []
    return {"message": "Histórico limpo com sucesso"}


# ============================================================================
# ENDPOINT DE TESTE RÁPIDO
# ============================================================================

@app.post("/quick_query")
async def quick_query(query: str, username: str = Depends(verify_token)):
    """
    Endpoint para testes rápidos sem gerenciar sessões
    """
    try:
        # Selecionar agente
        agent, agent_name = route_to_agent(query, "")
        
        # Criar tarefa
        task = Task(
            description=f"Responda de forma breve e direta: {query}",
            expected_output="Resposta direta em até 100 palavras",
            agent=agent
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False
        )
        
        result = crew.kickoff()
        
        response_text = result.raw if hasattr(result, 'raw') else str(result)
        
        return {
            "query": query,
            "response": response_text,
            "agent": agent_name
        }
        
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# HEALTH CHECK E INFO
# ============================================================================

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "active_sessions": len(sessions),
        "agents": [
            "Analista de Dados",
            "Especialista Clínico",
            "Gestor Administrativo",
            "Assistente de Pesquisa"
        ]
    }


@app.get("/")
async def root():
    """Informações da API"""
    return FileResponse('index.html')


@app.get("/predict_noshow/{patient_id}")
async def predict_noshow_individual(patient_id: int, username: str = Depends(verify_token)):
    """
    Prediz probabilidade de no-show para um paciente específico
    """
    try:
        result = predictor.predict_individual(patient_id)
        
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predict_noshow_batch")
async def predict_noshow_batch(date_start: str, date_end: str, username: str = Depends(verify_token)):
    """
    Prediz no-show para todos pacientes em um período
    
    Args:
        date_start: Data inicial no formato YYYY-MM-DD
        date_end: Data final no formato YYYY-MM-DD
    """
    try:
        # Validar formato das datas
        start = datetime.strptime(date_start, '%Y-%m-%d')
        end = datetime.strptime(date_end, '%Y-%m-%d')
        
        if end < start:
            raise HTTPException(status_code=400, detail="Data final deve ser posterior à data inicial")
        
        # Calcular número de dias
        dias = (end - start).days + 1
        
        # Agregar predições para todo o período
        result = predictor.predict_batch_range(date_start, date_end)
        
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return result
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page(username: str = Depends(verify_token)):
    """
    Serve a página do chatbot
    """
    try:
        # Tentar ler o arquivo chatbot_completo.html
        chatbot_file = Path("chatbot.html")
        
        if not chatbot_file.exists():
            # Se não existir, retornar erro amigável
            return HTMLResponse(
                content="""
                <html>
                <head>
                    <title>Erro</title>
                    <style>
                        body { 
                            font-family: Arial; 
                            text-align: center; 
                            padding: 50px;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                        }
                        .error-box {
                            background: white;
                            color: #333;
                            padding: 40px;
                            border-radius: 20px;
                            max-width: 600px;
                            margin: 0 auto;
                        }
                    </style>
                </head>
                <body>
                    <div class="error-box">
                        <h1>❌ Arquivo não encontrado</h1>
                        <p>O arquivo <code>chatbot_completo.html</code> não foi encontrado.</p>
                        <p>Certifique-se de que o arquivo está na mesma pasta que <code>api_chatbot.py</code></p>
                        <br>
                        <a href="/" style="color: #667eea; text-decoration: none; font-weight: bold;">← Voltar ao Menu</a>
                    </div>
                </body>
                </html>
                """,
                status_code=404
            )
        
        # Ler e retornar o conteúdo do arquivo
        with open(chatbot_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content)
    
    except Exception as e:
        return HTMLResponse(
            content=f"""
            <html>
            <head><title>Erro</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>❌ Erro ao carregar chatbot</h1>
                <p>{str(e)}</p>
                <a href="/">← Voltar ao Menu</a>
            </body>
            </html>
            """,
            status_code=500
        )
