#pyinstaller --noconfirm --onefile --windowed --name "VyaManagerPanel" --add-data "templates;templates" --add-data "static;static" --icon "static/favicon.png" main.py

import sys
import os
import psycopg2
import datetime
import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv

def resource_path(relative_path):
    """ Retorna o caminho absoluto, seja rodando como script ou como .exe """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

if hasattr(sys, '_MEIPASS'):
    app = Flask(__name__, 
                template_folder=os.path.join(sys._MEIPASS, 'templates'),
                static_folder=os.path.join(sys._MEIPASS, 'static'))
else:
    app = Flask(__name__)

app.secret_key = 'chave_super_secreta'

USUARIOS_PERMITIDOS = ["vanderlei", "brunog", "erison"]

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "richardnextt@gmail.com"
SMTP_PASS = "ldsh xxcg jtco laab"
EMAIL_DESTINO = "richardhartmann2@gmail.com"

AGENT_PORT = 5002
URL_VERSAO_REMOTA = "https://raw.githubusercontent.com/richardhhartmann/AutoNextt-Atualizador/main/versao.txt"

DOMAIN_MAP = {
    "104.234.235.107": "https://emporioalex.vyamanager.com.br",
    "14.102.230.87": "https://casado.vyamanager.com.br",
    "14.102.230.224": "https://ludique.vyamanager.com.br",
    "172.22.2.125": "https://narducci.vyamanager.com.br",
    "14.102.230.46": "https://poderosotimao.vyamanager.com.br",
    "14.102.230.30": "https://rossi.vyamanager.com.br",
    "104.234.235.5": "https://soccer.vyamanager.com.br",
    "14.102.230.171": "https://sunika.vyamanager.com.br",
    "104.234.235.2": "https://tunoda.vyamanager.com.br",
    "104.234.235.106": "https://victoraces.vyamanager.com.br"
}

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

NICKNAMES_FILE = os.path.join(BASE_DIR, 'apelidos.json')
DOTENV_PATH = os.path.join(BASE_DIR, '.env')

load_dotenv(DOTENV_PATH)

def get_db_connection():
    """Cria uma conexão com o banco de dados PRINCIPAL."""
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'), database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'), password=os.getenv('DB_PASS'),
        port=os.getenv('DB_PORT')
    )
    return conn

def conectar_feedback_db():
    """Cria uma conexão com o banco de dados de FEEDBACK PostgreSQL em nuvem."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('FEEDBACK_DB_HOST'),
            database=os.getenv('FEEDBACK_DB_NAME'),
            user=os.getenv('FEEDBACK_DB_USER'),
            password=os.getenv('FEEDBACK_DB_PASS'),
            port=os.getenv('FEEDBACK_DB_PORT')
        )
        return conn
    except Exception as e:
        app.logger.error(f"Falha ao conectar ao DB de feedback: {e}")
        return None

def load_nicknames():
    """Lê o arquivo JSON de apelidos. Retorna um dict vazio se não existir."""
    if not os.path.exists(NICKNAMES_FILE):
        return {}
    try:
        with open(NICKNAMES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao ler apelidos: {e}")
        return {}

def save_nickname(maquina, novo_nome):
    """Salva ou atualiza um apelido no JSON."""
    data = load_nicknames()
    
    if novo_nome and novo_nome.strip():
        data[maquina] = novo_nome.strip()
    else:
        if maquina in data:
            del data[maquina]
            
    with open(NICKNAMES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    usuario_input = data.get('email')
    senha_input = data.get('password')

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Erro de conexão com banco'}), 500
    
    try:
        cur = conn.cursor()
        
        cur.execute("SELECT id, usu_login, usu_senha FROM autonextt.usuarios_dashboard WHERE usu_login = %s", (usuario_input,))
        user_db = cur.fetchone()
        
        if user_db:
            user_id, login_db, senha_db = user_db
            
            if senha_db == senha_input:
                session['logged_in'] = True
                session['user'] = login_db
                return jsonify({'success': True, 'redirect': url_for('dashboard')})
            else:
                return jsonify({'success': False, 'error': 'Senha incorreta'}), 401

        elif usuario_input in USUARIOS_PERMITIDOS:
            if not senha_input:
                return jsonify({
                    'success': False, 
                    'require_setup': True, 
                    'message': 'Criação de senha necessária'
                })
            else:
                return jsonify({'success': False, 'error': 'Usuário reconhecido. Deixe a senha em branco para iniciar.'}), 401

        else:
            if usuario_input == 'richard' and senha_input == '1105':
                session['logged_in'] = True
                session['user'] = usuario_input
                return jsonify({'success': True, 'redirect': url_for('dashboard')})
            
            return jsonify({'success': False, 'error': 'Usuário não encontrado'}), 401

    except Exception as e:
        print(f"Erro login: {e}")
        return jsonify({'success': False, 'error': 'Erro interno'}), 500
    finally:
        if conn: conn.close()

@app.route('/api/criar-senha', methods=['POST'])
def criar_senha():
    data = request.get_json()
    usuario = data.get('email')
    nova_senha = data.get('new_password')
    
    if not usuario or not nova_senha:
        return jsonify({'success': False, 'error': 'Dados incompletos'}), 400
        
    if usuario not in USUARIOS_PERMITIDOS:
        return jsonify({'success': False, 'error': 'Não autorizado.'}), 403

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        cur.execute("SELECT 1 FROM autonextt.usuarios_dashboard WHERE usu_login = %s", (usuario,))
        if cur.fetchone():
            return jsonify({'success': False, 'error': 'Usuário já cadastrado.'}), 400

        cur.execute("""
            INSERT INTO autonextt.usuarios_dashboard (usu_login, usu_senha, usu_altera_senha)
            VALUES (%s, %s, FALSE)
        """, (usuario, nova_senha))
        
        conn.commit()
        
        session['logged_in'] = True
        session['user'] = usuario
        
        return jsonify({'success': True, 'redirect': url_for('dashboard')})

    except Exception as e:
        if conn: conn.rollback()
        print(f"Erro ao criar senha: {e}")
        return jsonify({'success': False, 'error': 'Erro ao salvar no banco'}), 500
    finally:
        if conn: conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/agendar-demo', methods=['POST'])
def agendar_demo():
    data = request.json
    empresa = data.get('empresa')
    email_cliente = data.get('usuario')

    if not empresa or not email_cliente:
        return jsonify({'error': 'Preencha todos os campos'}), 400

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = EMAIL_DESTINO
        msg['Subject'] = f"🚀 Novo Lead VYA Manager: {empresa}"

        corpo = f"""
        <h2>Novo Pedido de Demonstração</h2>
        <p><strong>Empresa:</strong> {empresa}</p>
        <p><strong>Email:</strong> {email_cliente}</p>
        <p><em>Origem: Landing Page</em></p>
        """
        msg.attach(MIMEText(corpo, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, EMAIL_DESTINO, msg.as_string())
        server.quit()

        return jsonify({'message': 'Email enviado!'}), 200
    except Exception as e:
        print(f"Erro email: {e}")
        return jsonify({'error': 'Erro ao enviar email'}), 500

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('index'))

    conn = get_db_connection()
    if not conn:
        return render_template('dashboard.html', error="Erro de Conexão com Banco", total_online=0, total_clientes=0), 500

    try:
        cur = conn.cursor()

        apelidos = {}

        if os.path.exists(NICKNAMES_FILE): # Usa a variável global corrigida
            try:
                with open(NICKNAMES_FILE, 'r', encoding='utf-8') as f:
                    apelidos = json.load(f)
            except Exception as e:
                print(f"Erro ao ler apelidos: {e}")

        caminho_apelidos = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apelidos.json')
        if os.path.exists(caminho_apelidos):
            try:
                with open(caminho_apelidos, 'r', encoding='utf-8') as f:
                    apelidos = json.load(f)
            except Exception as e:
                print(f"Erro ao ler apelidos: {e}")

        cur.execute("""
            SELECT DISTINCT ON (s.maquina_local) 
                s.maquina_local as maquina, 
                s.ip_local,
                s.status_sessao, 
                s.inicio_sessao, 
                s.versao_app, 
                s.ultimo_heartbeat,
                (SELECT COUNT(*) FROM autonextt.comandos_remotos c WHERE c.alvo_maquina = s.maquina_local AND c.status = 'PENDING') as comandos_pendentes
            FROM autonextt.sessoes_autonextt s
            WHERE s.inicio_sessao >= NOW() - INTERVAL '24 hours'
            ORDER BY s.maquina_local, s.inicio_sessao DESC;
        """)
        
        colunas = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        
        clientes_processados = []
        
        for row in rows:
            cliente = dict(zip(colunas, row))
            
            maquina_id = cliente['maquina']
            ip_local = cliente.get('ip_local')
            
            display_name = apelidos.get(maquina_id, maquina_id)
            cliente['display_name'] = display_name
            cliente['empresa_display'] = display_name 
            cliente['servidor'] = display_name # Preenche o campo 'Servidor' no card

            domain_url = None
            if ip_local and ip_local in DOMAIN_MAP:
                domain_url = DOMAIN_MAP[ip_local]
            
            if domain_url:
                cliente['link_sistema'] = domain_url
                cliente['domain'] = domain_url
            else:
                cliente['link_sistema'] = f"http://{ip_local}:8000" if ip_local else "#"
                cliente['domain'] = None

            cliente['ip'] = ip_local 
            cliente['ip_local'] = ip_local

            cliente['versao'] = cliente.get('versao_app') or 'v0.0.0'

            if cliente.get('inicio_sessao'):
                dt = cliente['inicio_sessao'] - datetime.timedelta(hours=3)
                cliente['inicio_sessao_fmt'] = dt.strftime('%d/%m %H:%M')
            else:
                cliente['inicio_sessao_fmt'] = "-"

            if cliente.get('ultimo_heartbeat'):
                dt_hb = cliente['ultimo_heartbeat'] - datetime.timedelta(hours=3)
                cliente['ultimo_heartbeat'] = dt_hb.strftime('%d/%m %H:%M:%S')
            else:
                cliente['ultimo_heartbeat'] = "S/ Inf."

            status_banco = cliente.get('status_sessao', 'offline')
            cliente['status_class'] = 'online' if status_banco == 'online' else 'offline'
            cliente['status_text'] = status_banco.upper()
            
            clientes_processados.append(cliente)

        clientes_processados.sort(key=lambda x: (x['comandos_pendentes'] > 0, x['status_sessao'] == 'online'), reverse=True)

        total_online = sum(1 for c in clientes_processados if c['status_sessao'] == 'online')
        total_clientes = len(clientes_processados)

        cur.close()

        return render_template('dashboard.html', 
                             clientes=clientes_processados, 
                             total_online=total_online,
                             total_clientes=total_clientes,
                             versoes_disponiveis=[], 
                             agora=datetime.datetime.now().strftime('%H:%M'))

    except Exception as e:
        print(f"Erro dashboard: {e}")
        return render_template('dashboard.html', error=str(e), clientes=[], total_online=0, total_clientes=0), 500
        
    finally:
        if conn: conn.close()

@app.route('/api/renomear', methods=['POST'])
def api_renomear():
    data = request.get_json()
    maquina = data.get('maquina')
    novo_nome = data.get('novo_nome')
    
    if not maquina:
        return jsonify({'status': 'error', 'message': 'Máquina não informada'}), 400
        
    try:
        save_nickname(maquina, novo_nome)
        return jsonify({'status': 'success', 'novo_nome': novo_nome})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/feedback/check', methods=['POST'])
def check_feedback():
    """Verifica se há novos feedbacks para uma lista de clientes."""
    data = request.get_json()
    client_names = data.get('clients', [])
    last_check_timestamp = data.get('last_check') 

    if not client_names:
        return jsonify({})

    conn = None
    try:
        conn = conectar_feedback_db()
        if not conn:
            return jsonify({"error": "Falha na conexão com o serviço de feedback"}), 500

        cur = conn.cursor()
        
        sql = """
            SELECT DISTINCT ON (nome_empresa)
                nome_empresa, rating, comentario, data_envio, placeholders_selecionados
            FROM autonextt.feedback_avaliacoes
            WHERE nome_empresa = ANY(%s)
            ORDER BY nome_empresa, data_envio DESC;
        """
        
        cur.execute(sql, (client_names,))
        
        new_feedbacks = {}
        for row in cur.fetchall():
            nome_empresa, rating, comentario, data_envio, placeholders_json = row
            
            placeholders = placeholders_json if isinstance(placeholders_json, list) else []

            new_feedbacks[nome_empresa] = {
                'rating': rating,
                'comment': comentario or '',
                'timestamp': data_envio.isoformat(),
                'placeholders': placeholders # Adiciona os placeholders ao retorno
            }
            
        cur.close()
        return jsonify(new_feedbacks)

    except Exception as e:
        app.logger.error(f"Erro ao verificar feedbacks: {e}")
        return jsonify({"error": "Erro interno ao processar feedbacks"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/feedback/history/<maquina>')
def feedback_history(maquina):
    """Retorna o histórico completo de feedbacks para um cliente específico."""
    conn = None
    try:
        conn = conectar_feedback_db()
        if not conn:
            return jsonify({"error": "Falha na conexão com o serviço de feedback"}), 500
        
        cur = conn.cursor()
        sql = """
            SELECT rating, comentario, data_envio, placeholders_selecionados, nome_usuario
            FROM autonextt.feedback_avaliacoes
            WHERE nome_empresa = %s
            ORDER BY data_envio DESC;
        """
        cur.execute(sql, (maquina,))
        
        history = []
        for row in cur.fetchall():
            rating, comentario, data_envio, placeholders_json, nome_usuario = row
            
            placeholders = placeholders_json if isinstance(placeholders_json, list) else []

            history.append({
                'rating': rating,
                'comment': comentario or '',
                'timestamp': data_envio.isoformat(),
                'placeholders': placeholders,
                'user': nome_usuario or 'Usuário desconhecido' # Adiciona o nome do usuário
            })
        
        cur.close()
        return jsonify(history)

    except Exception as e:
        app.logger.error(f"Erro ao buscar histórico de feedback para {maquina}: {e}")
        return jsonify({"error": "Erro interno ao processar histórico"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/historico/<empresa>')
def historico_cliente(empresa):
    """Página para mostrar o histórico de um cliente."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT inicio_sessao, fim_sessao, duracao_segundos, status_calculado, versao_app
        FROM autonextt.vw_sessoes_autonextt_status
        WHERE empresa = %s
        ORDER BY inicio_sessao DESC
        LIMIT 20;
    """, (empresa,))
    sessoes_raw = cur.fetchall()
    cur.close()
    conn.close()
    
    sessoes = []
    for row in sessoes_raw:
        inicio, fim, duracao, status, versao = row
        sessoes.append({
            'inicio': inicio.astimezone(datetime.timezone(datetime.timedelta(hours=-3))).strftime('%d/%m/%y %H:%M'),
            'fim': fim.astimezone(datetime.timezone(datetime.timedelta(hours=-3))).strftime('%d/%m/%y %H:%M') if fim else 'Ativa',
            'duracao': str(datetime.timedelta(seconds=int(duracao or 0))),
            'status': status,
            'versao': versao or 'N/A'
        })
    return render_template('historico.html', maquina=empresa, sessoes=sessoes)


@app.route('/api/update/check_latest_version', methods=['GET'])
def check_latest_version():
    """Busca a versão mais recente do arquivo de versão no repositório."""
    try:
        response = requests.get(URL_VERSAO_REMOTA, timeout=10)
        response.raise_for_status()
        content = response.text.strip().split('\\n')
        versao_linha = next((line.split("=", 1)[1].strip() for line in content if line.startswith("version=")), "N/D")
        versao = versao_linha.split()[0]
        if versao == "N/D":
            raise ValueError("Formato do arquivo de versão inválido.")
        return jsonify({'latest_version': versao})
    except requests.RequestException as e:
        app.logger.error(f"Erro ao buscar versão remota: {e}")
        return jsonify({'error': str(e)}), 503

@app.route('/api/update/<empresa>/trigger', methods=['POST'])
def trigger_update(empresa):
    """Envia o comando de atualização para o agente de um cliente específico."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT ip_local FROM autonextt.sessoes_autonextt WHERE empresa = %s ORDER BY ultimo_heartbeat DESC LIMIT 1", (empresa,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if not result or not result[0]:
        return jsonify({'status': 'error', 'message': 'IP do cliente não encontrado.'}), 404
    client_ip = result[0]
    agent_url = f"http://{client_ip}:{AGENT_PORT}/update/start"
    try:
        response = requests.post(agent_url, timeout=15)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'error', 'message': f'Falha ao conectar com o agente: {e}'}), 503

@app.route('/api/service/<empresa>/<action>', methods=['POST'])
def control_service_request(empresa, action):
    """Recebe a requisição do frontend e a repassa para o agente no cliente."""
    if action not in ['start', 'stop', 'restart']:
        return jsonify({'status': 'error', 'message': 'Ação inválida.'}), 400
        
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT ip_local FROM autonextt.sessoes_autonextt WHERE empresa = %s ORDER BY ultimo_heartbeat DESC LIMIT 1", (empresa,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if not result or not result[0]:
        return jsonify({'status': 'error', 'message': 'IP do cliente não encontrado.'}), 404
        
    client_ip = result[0]
    agent_url = f"http://{client_ip}:{AGENT_PORT}/app/control"
    
    try:
        response = requests.post(agent_url, json={'action': action}, timeout=10)
        response.raise_for_status()

        if action == 'stop' and response.status_code == 200:
            conn_update = None
            try:
                conn_update = get_db_connection()
                cur_update = conn_update.cursor()
                cur_update.execute("""
                    UPDATE autonextt.sessoes_autonextt
                    SET status_sessao = 'offline', fim_sessao = %s
                    WHERE id_sessao = (
                        SELECT id_sessao FROM autonextt.sessoes_autonextt
                        WHERE empresa = %s AND status_sessao = 'online'
                        ORDER BY inicio_sessao DESC
                        LIMIT 1
                    )
                """, (datetime.datetime.now(datetime.timezone.utc), empresa))
                conn_update.commit()
                cur_update.close()
            except Exception as e:
                app.logger.error(f"Falha ao atualizar o status para offline para {empresa}: {e}")
            finally:
                if conn_update:
                    conn_update.close()

        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'error', 'message': f'Falha ao conectar com o agente no cliente: {e}'}), 503

@app.route('/api/cliente/<empresa>/delete', methods=['POST'])
def delete_cliente(empresa):
    """Exclui todos os registros de um cliente (empresa)."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM autonextt.sessoes_autonextt WHERE empresa = %s", (empresa,))
        conn.commit()
        deleted_count = cur.rowcount
        cur.close()
        if deleted_count > 0:
            return jsonify({'status': 'success', 'message': f'Cliente {empresa} e todo o seu histórico foram excluídos.'})
        else:
            return jsonify({'status': 'error', 'message': 'Nenhum cliente encontrado com esse nome.'}), 404
    except Exception as e:
        if conn:
            conn.rollback()
        app.logger.error(f"Erro ao excluir cliente {empresa}: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/comando_remoto', methods=['POST'])
def enviar_comando_remoto():
    """
    Recebe um comando do painel e insere na fila do banco de dados para o Watchdog ler.
    Esperado JSON: { "maquina": "NOME_DA_MAQUINA", "comando": "PAUSE" | "RESUME" | "RESTART" }
    """
    data = request.get_json()
    maquina = data.get('maquina')
    comando = data.get('comando')

    if not maquina or not comando:
        return jsonify({'status': 'error', 'message': 'Dados incompletos.'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO autonextt.comandos_remotos (comando, alvo_maquina, status)
            VALUES (%s, %s, 'PENDING')
        """, (comando, maquina))
        
        conn.commit()
        cur.close()
        
        return jsonify({
            'status': 'success', 
            'message': f'Comando {comando} enviado com sucesso para {maquina}.'
        })

    except Exception as e:
        app.logger.error(f"Erro ao enviar comando remoto: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
    