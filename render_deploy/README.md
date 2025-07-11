# FitManager - Sistema de Gestão de Clientes

Sistema completo de gestão de clientes para estabelecimentos de Pilates, musculação, aulas funcionais, tratamentos estéticos e outros serviços personalizados.

## 🚀 Funcionalidades

### 📇 Gestão de Clientes
- Cadastro completo com informações pessoais
- Upload de foto do cliente
- Histórico médico e observações específicas
- CRUD completo (criar, ler, atualizar, deletar)

### 💳 Gestão de Pacotes
- Pacotes mensais, por sessão ou procedimento
- Controle de preços e descrições
- Configuração de duração e número de sessões

### 📅 Sistema de Agendamentos
- Calendário para marcação de aulas/sessões
- Diferentes tipos de serviços (Pilates, Musculação, etc.)
- Controle de status (Agendado, Concluído, Cancelado)
- Vinculação de instrutor responsável

### 📊 Dashboard Inteligente
- Estatísticas em tempo real
- Visão geral do negócio
- Resumo de agendamentos e atividades

## 🛠️ Tecnologias

- **Backend:** FastAPI (Python)
- **Frontend:** React + Tailwind CSS
- **Banco de Dados:** PostgreSQL
- **Deploy:** Render (gratuito)

## 📦 Deploy no Render

Este projeto está configurado para deploy automático no Render.

### Estrutura do Projeto:
```
fitmanager/
├── server.py              # Backend FastAPI
├── requirements.txt       # Dependências Python
├── render.yaml           # Configuração do Render
└── frontend/             # Aplicação React
    ├── src/
    ├── public/
    └── package.json
```

### Como fazer deploy:

1. **Fork/Clone este repositório**
2. **Conecte no Render:**
   - Acesse https://render.com
   - Conecte sua conta GitHub
   - Selecione este repositório
3. **Configure automaticamente:**
   - O arquivo `render.yaml` configura tudo automaticamente
   - Banco PostgreSQL será criado gratuitamente
   - Deploy do backend + frontend juntos

## 🎯 Como usar após deploy:

1. **Acesse sua URL do Render** (ex: https://fitmanager.onrender.com)
2. **Cadastre seus primeiros clientes**
3. **Crie pacotes de serviços**
4. **Comece a agendar sessões**

## 💡 Recursos Inclusos:

- ✅ Interface moderna e responsiva
- ✅ Formulários intuitivos
- ✅ Upload de fotos (base64)
- ✅ Validação de dados
- ✅ Feedback visual para usuário
- ✅ Sistema completo de CRUD

## 🔄 Desenvolvimento Local:

### Backend:
```bash
pip install -r requirements.txt
uvicorn server:app --reload
```

### Frontend:
```bash
cd frontend
npm install
npm start
```

## 📞 Suporte

Sistema desenvolvido para gestão eficiente de clientes em estabelecimentos de fitness e bem-estar.

---

**Hospedagem gratuita no Render - Tudo em um lugar! 🚀**