@echo off
echo Limpando builds anteriores...
rmdir /s /q build dist
del /f /q *.spec

echo Ativando ambiente virtual...
call v_app\Scripts\activate.bat

echo Garantindo que todas dependencias estejam instaladas...
pip install pandas numpy tkcalendar openpyxl pyinstaller

echo Criando pasta de distribuicao...
mkdir dist

echo Gerando executavel otimizado...
cd app
pyinstaller --noconfirm ^
            --onefile ^
            --windowed ^
            --paths "..\v_app\Lib\site-packages" ^
            --hidden-import tkcalendar ^
            --hidden-import babel.numbers ^
            --hidden-import numpy ^
            --hidden-import pandas ^
            --hidden-import openpyxl ^
            --collect-submodules tkinter ^
            --clean ^
            app.py

echo Movendo executavel para pasta dist...
move dist\app.exe ..\dist\KBL_REST_GYN.exe

echo Criando estrutura de pastas...
mkdir ..\dist\app

echo Copiando banco de dados...
if exist app_rest_gyn.db (
    copy app_rest_gyn.db ..\dist\app\app_rest_gyn.db
) else (
    echo Banco de dados nao encontrado, sera criado na primeira execucao
)

cd ..

echo Limpando arquivos temporarios...
rmdir /s /q app\build app\dist
del /f /q app\*.spec

echo Processo concluido!
echo Arquivos gerados na pasta 'dist':
dir dist

pause