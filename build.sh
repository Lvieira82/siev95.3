#!/usr/bin/env bash

set -o errexit

echo "======================================"
echo "Instalando dependências Python"
echo "======================================"

pip install -r requirements.txt


echo "======================================"
echo "Baixando pacotes do Tesseract OCR"
echo "======================================"

mkdir -p .apt-packages
cd .apt-packages

apt-get download \
    tesseract-ocr \
    tesseract-ocr-por \
    libtesseract5

echo "======================================"
echo "Extraindo pacotes"
echo "======================================"

for arquivo in *.deb; do
    dpkg-deb -x "$arquivo" .
done

cd ..


echo "======================================"
echo "Configurando Tesseract"
echo "======================================"

export PATH="$PWD/.apt-packages/usr/bin:$PATH"

export LD_LIBRARY_PATH="$PWD/.apt-packages/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"

export TESSDATA_PREFIX="$PWD/.apt-packages/usr/share/tesseract-ocr/5/tessdata"


echo "======================================"
echo "Testando Tesseract"
echo "======================================"

which tesseract

tesseract --version

tesseract --list-langs


echo "======================================"
echo "Executando migrations"
echo "======================================"

python manage.py migrate


echo "======================================"
echo "Coletando arquivos estáticos"
echo "======================================"

python manage.py collectstatic --noinput


echo "======================================"
echo "BUILD CONCLUÍDO COM SUCESSO"
echo "======================================"
