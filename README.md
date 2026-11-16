# VI Jornada Acadêmica — UNINASSAU Teresina

Protótipo da plataforma web da VI Jornada Acadêmica. O projeto foi iniciado do zero e está sendo construído por etapas, começando pela interface pública e seguindo para autenticação, banco de dados, frequência e certificação.

## Estado desta versão

Esta entrega é um **protótipo visual front-end** em HTML5, CSS3 e JavaScript puro. Não exige Python, ambiente virtual ou banco de dados para ser visualizada.

### Páginas incluídas

- `index.html`: página inicial pública da Jornada;
- `inscricao.html`: protótipo visual da captura cadastral;
- `login.html`: protótipo visual da área de acesso.

Os formulários ainda não enviam dados e o botão Google está desativado nesta versão, pois a autenticação será conectada somente na etapa de backend.

## O que aparece na página pública

- Logo original da VI Jornada Acadêmica;
- Apresentação institucional e tema;
- Eixos da marca: Ensino, Pesquisa, Extensão, Inovação e Transformação;
- Orientações gerais de participação;
- Informações gerais de inscrição;
- Navegação e rodapé institucional;
- Acesso à inscrição e à tela de login.

## O que fica restrito após autenticação

Os recursos abaixo não fazem parte da página inicial pública. Eles devem aparecer somente depois que o servidor autenticar o usuário e conferir seu cadastro e perfil:

- QR Code individual do participante;
- Dados pessoais, CPF e matrícula;
- Histórico e detalhes de frequência e carga horária;
- Painel do professor para busca e confirmação de presença;
- Painel administrativo, gerenciamento de participantes e relatórios;
- Visualização, download e validação individual de certificados.

O modelo oficial do certificado foi mantido localmente em `private_assets/certificado-oficial-referencia.png`, fora da pasta pública `assets/`. Essa pasta é ignorada pelo Git e o arquivo não é publicado no repositório. Na versão funcional, o modelo deverá permanecer no servidor e ser utilizado somente por uma rota protegida.

## Requisitos extraídos do PDF do Hackathon

- Centralizar inscrições e presença, reduzindo controles manuais paralelos;
- Capturar e validar dados cadastrais, incluindo nome, CPF, matrícula, curso e e-mail;
- Manter informações de alunos, eventos e frequência diária em estrutura relacionada;
- Registrar data/hora e check-in associado ao participante e ao evento;
- Proteger CPF e demais dados pessoais com acesso controlado, observando a LGPD;
- Permitir check-in por QR Code individual ou busca por CPF em painel autorizado;
- Permitir que professor autenticado confirme presenças;
- Calcular a frequência mínima de 75% para elegibilidade ao certificado;
- Gerar certificado em PDF com nome, CPF, curso e carga horária e encaminhá-lo após o encerramento oficial da Jornada.

Essas funcionalidades são requisitos do sistema, mas QR Code, dados individuais, painéis de equipe e certificados não devem ser exibidos publicamente.

## Tecnologias planejadas para a etapa funcional

- **Front-end:** HTML5, CSS3 e JavaScript;
- **Back-end:** Python com Flask;
- **Banco de dados:** MySQL;
- **ORM e migrações:** SQLAlchemy e Flask-Migrate;
- **Autenticação:** Google OpenID Connect com validação de cadastro e perfil no banco;
- **Certificados:** geração de PDF a partir do modelo oficial, com acesso protegido.

A autenticação Google não deve conceder acesso automaticamente. O backend deverá verificar se a identidade/e-mail autenticado corresponde a um usuário previamente cadastrado e autorizado. Esconder uma tela ou botão no navegador não substitui autorização no servidor.

## Estrutura do projeto

```text
vi-jornada-academica/
├── index.html
├── inscricao.html
├── login.html
├── css/
│   └── style.css
├── js/
│   └── main.js
├── assets/
│   └── logo-jornada-original.png
├── private_assets/                 # ignorada pelo Git
│   └── certificado-oficial-referencia.png
├── .gitignore
└── README.md
```

## Como visualizar

1. Faça o download ou clone o repositório.
2. Abra a pasta no Visual Studio Code.
3. Abra `index.html` diretamente no navegador ou use a extensão **Live Server**.
4. As alterações em HTML/CSS/JS podem ser visualizadas ao salvar e atualizar o navegador.

Não é necessário instalar Python para esta etapa.

## Próximas etapas

1. Revisar e aprovar a interface e os textos públicos;
2. Concluir o fluxo público de inscrição e as validações;
3. Modelar e criar o banco MySQL;
4. Implementar o backend Flask;
5. Integrar Google OAuth e autorização baseada no cadastro e no perfil;
6. Desenvolver as áreas restritas de participante, professor e administração;
7. Implementar QR Code, registro de presença e cálculo dos 75%;
8. Implementar geração e entrega protegida do certificado;
9. Testar regras de negócio, segurança, LGPD e responsividade antes da publicação.

## Cuidados com segurança e versionamento

- Nunca versionar `.env`, senhas, chaves OAuth ou credenciais;
- Não versionar o modelo de certificado armazenado em `private_assets/`;
- Não enviar dados reais de participantes, CPF ou matrícula para o GitHub;
- A proteção de dados deverá ser aplicada no servidor e no banco de dados.

## Publicar no GitHub

1. No GitHub, crie um repositório vazio chamado `vi-jornada-academica` na conta proprietária do projeto.
2. Não selecione a opção de criar outro README automaticamente, pois este projeto já contém `README.md`.
3. No terminal do VS Code, dentro da pasta do projeto, execute:

```bash
git init
git add .
git commit -m "chore: estrutura inicial da VI Jornada Acadêmica"
git branch -M main
git remote add origin https://github.com/mc337270-code/vi-jornada-academica.git
git push -u origin main
```

O `.gitignore` exclui `private_assets/`, `.env` e outros arquivos locais. Confira o que será enviado antes do primeiro `git push`.
