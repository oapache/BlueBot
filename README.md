# BlueBot – Telegram & WhatsApp Affiliate Monitor

**BlueBot** is a Telegram group monitoring bot that filters messages according to user-defined rules, generates affiliate links for products on marketplaces (Mercado Livre, Shopee, and AliExpress), and forwards the filtered messages, including media, to Telegram and WhatsApp groups.

This bot is ideal for freelancers or companies that want to automate affiliate link sharing while ensuring only relevant content is sent.

---

## Features

- **Real-time monitoring** of Telegram groups via polling.
- **Message filtering** based on:
  - Custom user-defined filters.
  - Supported marketplaces: AliExpress, Shopee, Mercado Livre.
- **Affiliate link generation**:
  - Mercado Livre: Selenium-based browser automation.
  - AliExpress & Shopee: Official affiliate APIs.
- **Media support**: Images and documents included when forwarding messages.
- **Forwarding to multiple platforms**:
  - Telegram groups.
  - WhatsApp groups using QR code authentication.
- **Extensible**: Easy to add support for new marketplaces in the future.
- **Detailed logging** for debugging and monitoring.

---

## Technologies

- **Python 3.11+**
  - `Telethon` – Telegram integration.
  - `Selenium` + `Pyperclip` – Mercado Livre link automation.
  - `httpx` – Async HTTP requests.
  - `python-dotenv` – Environment variables.
- **Node.js + WhatsApp-web.js**
  - WhatsApp messaging automation.
- **Other dependencies**
  - `requests`, `pandas`, `numpy`, `flask`, etc. (see `requirements.txt`)

---

## Project Structure
```bash
BlueBot/
├─ Affiliates/ # Affiliate link modules
│ ├─ aliexpress_affiliate.py
│ ├─ MercadoLivre_affiliate.py
│ └─ shopee_affiliate.py
├─ Drivers/ # Webdrivers (Chrome/Brave) for Selenium
├─ Whatsapp/ # WhatsApp bot
│ ├─ server.ts # WhatsApp server
│ ├─ tsconfig.json
│ └─ node_modules/
├─ Session/ # Telegram session data
├─ bot.py # Main Telegram monitoring bot
├─ chromedriver.exe # Chrome driver for Selenium
├─ package.json # Node.js dependencies
├─ requirements.txt # Python dependencies
├─ .env # Environment variables
└─ README.md
```
---

## Installation
```
1. Clone the repository:

git clone https://github.com/SaulloGabryel/BlueBot.git
cd BlueBot
Install Python dependencies:



python -m pip install -r requirements.txt
Install Node.js dependencies:



cd Whatsapp
npm install
cd ..
Configure .env with your credentials:

ini

API_ID=...
API_HASH=...
ALIEXPRESS_APP_KEY=...
ALIEXPRESS_APP_SECRET=...
ALIEXPRESS_TRACKING_ID=...
Make sure your chromedriver matches your browser version (Chrome or Brave).

Running
Telegram Bot:


python bot.py
The bot will monitor the source Telegram group and forward filtered messages to destination groups.

WhatsApp Bot:


cd Whatsapp
npm run start
On the first run, a QR code will appear to authenticate WhatsApp Web.
```
## Notes
The bot has been running for months on a VPS and is fully operational.

node_modules/, Session/, and WhatsApp session files (.wwebjs_auth) are ignored in Git.

New marketplaces can be easily added in the Affiliates/ folder.

Contact
Developed by Saullo Gabryel
Contact: www.linkedin.com/in/saullo-gabryel-679687372 / @saullo.g.dev@gmail.com

License

MIT License © 2025


--------------------------------------------------------------------------------------------------




## **README – Versão em Português**

**BlueBot** é um bot para monitoramento de grupos do Telegram que filtra mensagens de acordo com regras definidas pelo usuário, gera links de afiliados para produtos em marketplaces (Mercado Livre, Shopee e AliExpress) e envia as mensagens filtradas, incluindo mídias, para grupos do Telegram e WhatsApp.

Ideal para freelancers ou empresas que desejam automatizar o envio de links de afiliados garantindo que apenas conteúdo relevante seja compartilhado.

---

## Funcionalidades

- **Monitoramento em tempo real** de grupos do Telegram via polling.
- **Filtragem de mensagens** baseada em:
  - Filtros personalizados pelo usuário.
  - Marketplaces suportados: AliExpress, Shopee, Mercado Livre.
- **Geração de links de afiliados**:
  - Mercado Livre: via Selenium (automação de navegador).
  - AliExpress e Shopee: via APIs oficiais de afiliados.
- **Suporte a mídia**: imagens e documentos incluídos ao enviar mensagens.
- **Envio para múltiplas plataformas**:
  - Grupos do Telegram.
  - Grupos do WhatsApp via QR code.
- **Expansível**: fácil adicionar suporte a novos marketplaces.
- **Logs detalhados** para depuração e monitoramento.

---

## Tecnologias

- **Python 3.11+**
  - `Telethon` – integração com Telegram.
  - `Selenium` + `Pyperclip` – automação de links Mercado Livre.
  - `httpx` – requisições HTTP assíncronas.
  - `python-dotenv` – variáveis de ambiente.
- **Node.js + WhatsApp-web.js**
  - Automação de envio de mensagens no WhatsApp.
- **Outras dependências**
  - `requests`, `pandas`, `numpy`, `flask`, etc. (ver `requirements.txt`)

---

## Estrutura do Projeto
```
BlueBot/
├─ Affiliates/ # Módulos de geração de links de afiliados
│ ├─ aliexpress_affiliate.py
│ ├─ MercadoLivre_affiliate.py
│ └─ shopee_affiliate.py
├─ Drivers/ # Webdrivers (Chrome/Brave) para Selenium
├─ Whatsapp/ # Bot do WhatsApp
│ ├─ server.ts # Servidor de envio
│ ├─ tsconfig.json
│ └─ node_modules/
├─ Session/ # Sessões do Telegram
├─ bot.py # Bot principal de monitoramento
├─ chromedriver.exe # Driver do Chrome para Selenium
├─ package.json # Dependências Node.js
├─ requirements.txt # Dependências Python
├─ .env # Variáveis de ambiente
└─ README.md
```
---

## Instalação

1. Clone o repositório:

```bash
git clone https://github.com/SaulloGabryel/BlueBot.git
cd BlueBot

python -m pip install -r requirements.txt

cd Whatsapp
npm install
cd ..

Configure o arquivo .env com suas credenciais:

API_ID=...
API_HASH=...
ALIEXPRESS_APP_KEY=...
ALIEXPRESS_APP_SECRET=...
ALIEXPRESS_TRACKING_ID=...

Verifique se o chromedriver é compatível com a versão do seu navegador (Chrome ou Brave).

Execução
Bot do Telegram:
  python bot.py
O bot começará a monitorar o grupo fonte e enviar mensagens filtradas para os grupos destino.

Bot do WhatsApp:
cd Whatsapp
npm run start
Na primeira execução, será gerado um QR code para autenticar o WhatsApp Web.
````
Observações

O bot já está rodando em VPS há meses, funcionando 24/7.

Pastas como node_modules/, Session/ e arquivos de sessão do WhatsApp (.wwebjs_auth) são ignorados no Git.

Suporte a novos marketplaces pode ser adicionado facilmente na pasta Affiliates/.

Contato

Desenvolvido por Saullo Gabryel
Contato: www.linkedin.com/in/saullo-gabryel-679687372 / saullo.g.dev@gmail.com

Licença MIT License © 2025
