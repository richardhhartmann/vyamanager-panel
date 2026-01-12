@echo off
TITLE Atualizando VYA Manager Panel
COLOR 0A

echo ==========================================
echo 1. Parando o Servico VyaManagerPanel...
echo ==========================================
nssm stop VyaManagerPanel

echo.
echo ==========================================
echo 2. Baixando atualizacoes do Git...
echo ==========================================
cd /d "C:\Users\stk\Desktop\dev\painel_de_controle"
git pull origin main

:: Opcional: Atualizar bibliotecas se houver mudanças no requirements.txt
:: echo Atualizando bibliotecas Python...
:: pip install -r requirements.txt

echo.
echo ==========================================
echo 3. Reiniciando o Servico...
echo ==========================================
nssm start VyaManagerPanel

echo.
echo ==========================================
echo [SUCESSO] Sistema Atualizado!
echo ==========================================
timeout /t 5