@echo off
TITLE Gerando executável de servidor web VYA Manager Panel
COLOR 0A

echo ==========================================
echo Executando PyInstaller...
echo ==========================================
pyinstaller --noconfirm --onefile --windowed --name "VyaManagerPanel" --add-data "templates;templates" --add-data "static;static" --icon "static/favicon.png" main.py

echo ==========================================
echo SUCESSO - Executável gerado!
echo ==========================================