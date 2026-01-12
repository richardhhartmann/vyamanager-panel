# notificador.py (Versão Final com Funções de E-mail)

import os
import psycopg2
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from dotenv import load_dotenv

load_dotenv()

URL_VERSAO_REMOTA = "https://raw.githubusercontent.com/richardhhartmann/AutoNextt-Atualizador/main/versao.txt"
DEFAULT_EMAIL = "richardh@nexttinfo.com.br"
OFFLINE_THRESHOLD_MINUTES = 30

def get_db_connection():
    """Cria uma conexão com o banco de dados."""
    return psycopg2.connect(
        host=os.getenv('DB_HOST'), database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'), password=os.getenv('DB_PASS'),
        port=os.getenv('DB_PORT')
    )

def fetch_changelog():
    """Busca a versão e o changelog do repositório."""
    try:
        response = requests.get(URL_VERSAO_REMOTA)
        response.raise_for_status()
        content = response.text.strip().split('\n')
        versao, changelog = "N/D", "Não foi possível obter as notas da versão."
        for line in content:
            if line.startswith("version="): versao = line.split("=", 1)[1]
            elif line.startswith("changelog="): changelog = line.split("=", 1)[1].replace(";", "\n- ")
        return versao, changelog
    except Exception as e:
        print(f"Erro ao buscar changelog: {e}")
        return "N/D", f"Ocorreu um erro: {e}"

def get_config_e_emails(cursor, maquina):
    """Busca e-mails e configs. Retorna (lista_de_emails, notificacoes_pausadas)."""
    cursor.execute("SELECT email FROM autonextt.cliente_notificacoes WHERE maquina_local = %s", (maquina,))
    recipients = {row[0] for row in cursor.fetchall()}
    recipients.add(DEFAULT_EMAIL)
    
    cursor.execute("SELECT notificacoes_pausadas FROM autonextt.cliente_config WHERE maquina_local = %s", (maquina,))
    config = cursor.fetchone()
    pausado = config[0] if config else False
    
    return list(recipients), pausado

# --- NOVA FUNÇÃO DE E-MAIL DE ATUALIZAÇÃO ---
def send_update_email(nova_versao, changelog, maquina, recipients):
    """Envia um e-mail notificando sobre uma nova versão."""
    sender_email = os.getenv('EMAIL_SENDER')
    password = os.getenv('EMAIL_PASSWORD')

    message = MIMEMultipart("alternative")
    message["Subject"] = f"✅ AutoNextt Atualizado para v{nova_versao} no cliente {maquina}!"
    message["From"] = f"Monitoramento AutoNextt <{sender_email}>"
    message["To"] = ", ".join(recipients)

    html = f"""
    <html>
    <body style="font-family: sans-serif;">
        <h2>O AutoNextt foi atualizado automaticamente!</h2>
        <p><strong>Cliente:</strong> {maquina}</p>
        <p><strong>Nova Versão Instalada:</strong> {nova_versao}</p>
        <hr>
        <h3>Notas da Versão:</h3>
        <pre style="font-family: sans-serif; white-space: pre-wrap; background-color: #f4f4f4; padding: 1em; border-radius: 5px;">- {changelog}</pre>
        <p style="font-size: 0.8em; color: #777;">Este é um e-mail automático. Nenhuma ação é necessária.</p>
    </body>
    </html>
    """
    message.attach(MIMEText(html, "html"))
    try:
        with smtplib.SMTP(os.getenv('EMAIL_HOST'), int(os.getenv('EMAIL_PORT'))) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, recipients, message.as_string())
        print(f"E-mail de ATUALIZAÇÃO enviado com sucesso para {maquina}")
    except Exception as e:
        print(f"Falha ao enviar e-mail de ATUALIZAÇÃO para {maquina}: {e}")

# --- NOVA FUNÇÃO DE E-MAIL DE ALERTA OFFLINE ---
def send_offline_email(maquina, ultimo_heartbeat, recipients):
    """Envia um e-mail de alerta quando um cliente fica sem resposta."""
    sender_email = os.getenv('EMAIL_SENDER')
    password = os.getenv('EMAIL_PASSWORD')

    message = MIMEMultipart("alternative")
    message["Subject"] = f"⚠️ ALERTA: Cliente AutoNextt Sem Resposta - {maquina}"
    message["From"] = f"Monitoramento AutoNextt <{sender_email}>"
    message["To"] = ", ".join(recipients)

    heartbeat_local = ultimo_heartbeat.astimezone(datetime.timezone(datetime.timedelta(hours=-3)))
    heartbeat_br = heartbeat_local.strftime('%d/%m/%Y às %H:%M:%S')

    html = f"""
    <html>
    <body style="font-family: sans-serif;">
        <h2 style="color: #dc3545;">Alerta de Inatividade</h2>
        <p>O sistema de monitoramento detectou que o cliente abaixo parou de responder.</p>
        <p><strong>Cliente:</strong> {maquina}</p>
        <p><strong>Último Sinal de Atividade:</strong> {heartbeat_br}</p>
        <hr>
        <p><strong>Ação Recomendada:</strong> Verificar o status da aplicação ou do servidor neste cliente.</p>
        <p style="font-size: 0.8em; color: #777;">Este é um alerta automático.</p>
    </body>
    </html>
    """
    message.attach(MIMEText(html, "html"))
    try:
        with smtplib.SMTP(os.getenv('EMAIL_HOST'), int(os.getenv('EMAIL_PORT'))) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, recipients, message.as_string())
        print(f"E-mail de ALERTA OFFLINE enviado com sucesso para {maquina}")
    except Exception as e:
        print(f"Falha ao enviar e-mail de ALERTA OFFLINE para {maquina}: {e}")

def main():
    print(f"[{datetime.datetime.now()}] - Iniciando verificação de status e atualizações...")
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.maquina_local, s.versao_app, s.status_sessao, s.ultimo_heartbeat
        FROM (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY maquina_local ORDER BY inicio_sessao DESC) as rn
            FROM autonextt.sessoes_autonextt
        ) AS s WHERE s.rn = 1;
    """)
    clientes_atuais = cur.fetchall()

    ontem = datetime.date.today() - datetime.timedelta(days=1)
    cur.execute("""
        SELECT DISTINCT ON (maquina_local) maquina_local, versao_app
        FROM autonextt.sessoes_autonextt WHERE inicio_sessao::date = %s
        ORDER BY maquina_local, inicio_sessao DESC;
    """, (ontem,))
    versoes_ontem = dict(cur.fetchall())
    
    _, changelog_texto = fetch_changelog()

    for maquina, versao_hoje, status_sessao, ultimo_heartbeat in clientes_atuais:
        recipients, pausado = get_config_e_emails(cur, maquina)
        
        if pausado:
            print(f"-> Ignorando {maquina}: notificações pausadas.")
            continue

        # Lógica de Alerta de Atualização
        versao_antiga = versoes_ontem.get(maquina)
        if versao_hoje and versao_hoje != versao_antiga:
            print(f"ALERTA DE UPDATE para {maquina}: de {versao_antiga or 'N/A'} para {versao_hoje}")
            send_update_email(versao_hoje, changelog_texto, maquina, recipients)
        
        # Lógica de Alerta de Offline
        if status_sessao == 'online' and ultimo_heartbeat:
            diferenca = datetime.datetime.now(datetime.timezone.utc) - ultimo_heartbeat
            if diferenca.total_seconds() > OFFLINE_THRESHOLD_MINUTES * 60:
                print(f"ALERTA DE OFFLINE para {maquina}: último heartbeat há {int(diferenca.total_seconds() / 60)} minutos.")
                send_offline_email(maquina, ultimo_heartbeat, recipients)

    cur.close()
    conn.close()
    print(f"[{datetime.datetime.now()}] - Verificação concluída.")

if __name__ == "__main__":
    main()