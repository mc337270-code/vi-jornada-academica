# Etapa de integração Flask + MySQL

Este pacote adiciona a primeira camada funcional ao protótipo estático já publicado.

## O que esta etapa habilita
- Aplicação Flask servindo as páginas existentes (`index.html`, `inscricao.html`, `login.html`) e os arquivos de CSS/JS/assets.
- Conexão MySQL por SQLAlchemy/PyMySQL usando variáveis locais do `.env`.
- Criação das tabelas de usuários, participantes, eventos, dias, frequências e certificados.
- Formulário de inscrição com validação básica de e-mail/CPF e gravação no MySQL com status `pendente`.
- Estrutura de Google OpenID Connect. O login só aceita e-mail verificado que já exista como aprovado no banco.
- Proteção de rotas por perfil e uma tela administrativa inicial para aprovar participantes.
- Endpoint `/health` para testar conexão com o banco.

## Importante
O Google OAuth ainda depende da criação de `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` no Google Cloud. QR Code, operação de check-in e geração/entrega do PDF ainda serão implementados nas próximas etapas. As tabelas e relacionamentos dessas funcionalidades já estão modelados.

## Instalação local
1. Extraia o ZIP diretamente na raiz do repositório e escolha mesclar/substituir os arquivos solicitados. Mantenha `css/style.css`, `assets/` e `index.html` que já existem. O pacote substitui `inscricao.html`, `login.html`, `js/main.js`, `.gitignore` e `requirements.txt`, e adiciona os arquivos Python e templates.
2. Copie `.env.example` para `.env`.
3. Preencha `DB_PASSWORD` com a senha nova configurada para o usuário MySQL `jornada_app`, sem compartilhá-la ou publicá-la. Gere também uma chave secreta local para `SECRET_KEY` (por exemplo, `python -c "import secrets; print(secrets.token_hex(32))"`).
4. Defina `SECRET_KEY` com uma chave aleatória longa.
5. Com o ambiente virtual ativo, execute `python -m pip install -r requirements.txt`.
6. Crie as tabelas: `flask --app app init-db`.
7. Inicie o sistema: `python app.py`.
8. Abra `http://127.0.0.1:5000`.
9. Teste `http://127.0.0.1:5000/health`; a resposta esperada é `{"status":"ok","database":"connected"}`.

## Observações sobre Google
Depois de configurar as credenciais OAuth e cadastrar o URI de redirecionamento `http://127.0.0.1:5000/login/google/callback`, preencha as variáveis no `.env`. Para criar a primeira conta administrativa já autorizada, execute:

`flask --app app criar-equipe admin@instituicao.edu.br --nome "Nome do administrador" --perfil admin`

O endereço deve ser o mesmo da conta Google que será usada. Não use uma conta real de participante sem autorização da organização.

## Segurança
- `.env` nunca deve ser enviado ao GitHub.
- O certificado oficial permanece em `private_assets/`, fora dos arquivos estáticos públicos.
- CPF não é exibido em painéis públicos.
- Inscrições novas ficam pendentes até aprovação.
- Para produção, configure HTTPS e `COOKIE_SECURE=true`, reveja permissões e políticas LGPD, aplique migrações e faça testes de segurança.
