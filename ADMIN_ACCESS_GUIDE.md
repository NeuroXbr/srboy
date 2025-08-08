# 🔐 Guia de Acesso Administrativo - SrBoy Platform

## 👤 **ADMINISTRADOR PRINCIPAL**
**Email:** junior.lima@srdeliveri.com
**Nível:** ADMIN COMPLETO
**Permissões:** Acesso total ao sistema

---

## 🚀 **COMO ACESSAR O PAINEL ADMINISTRATIVO**

### **Passo 1: Acesso ao Site**
```
🌐 URL: https://srdeliveri.com
📧 Email: junior.lima@srdeliveri.com
🔑 Login: Via Google OAuth
```

### **Passo 2: Processo de Login**
1. Acesse `https://srdeliveri.com`
2. Clique em **"Login com Google"**
3. Use a conta Google associada ao email `junior.lima@srdeliveri.com`
4. Sistema identificará automaticamente como **ADMIN**
5. Você será redirecionado para a tela principal

### **Passo 3: Acessar Dashboard Admin**
1. Após login, localize a aba **"Admin"** no menu superior
2. Clique na aba **"Admin"**
3. Dashboard administrativo será carregado com todas as funcionalidades

---

## 📊 **FUNCIONALIDADES DISPONÍVEIS NO PAINEL**

### **1. 📈 Visão Geral (Dashboard Principal)**
- Estatísticas gerais do sistema
- Total de usuários (motoboys, lojistas)
- Total de entregas e taxa de conclusão
- Receita total e taxas da plataforma
- Estatísticas por cidade
- Alertas de segurança

### **2. 👥 Gestão de Usuários**
- **Listar usuários** com filtros (motoboy/lojista)
- **Visualizar perfis** completos
- **Ações administrativas:**
  - Suspender usuário (com duração)
  - Reativar usuário
  - Marcar para revisão
  - Bloquear permanentemente

### **3. 🚚 Gestão de Entregas**
- **Monitorar todas as entregas** do sistema
- **Filtros avançados:**
  - Status (pendente, em andamento, entregue)
  - Período de datas
  - Cidade/região
  - Motoboy/lojista específico
- **Visualizar detalhes completos:**
  - Endereços de coleta/entrega
  - Informações do destinatário
  - Sistema PIN de confirmação
  - Valores e taxas

### **4. 💰 Relatórios Financeiros**
- **Receita por período** (7d, 30d, 90d)
- **Breakdown financeiro:**
  - Receita total
  - Taxas da plataforma
  - Ganhos dos motoboys
  - Distribuição por cidade
- **Métodos de pagamento**
- **Análise de crescimento**

### **5. 🔒 Sistema de Segurança**
- **Alertas de risco:**
  - Motoboys com score baixo
  - Tentativas de PIN falhadas
  - Atividades suspeitas
- **Sistema PIN:**
  - Estatísticas de validações
  - PINs bloqueados
  - Taxa de sucesso
- **Monitoramento comportamental**

### **6. 📈 Analytics e Métricas**
- **Performance geral:**
  - Taxa de sucesso das entregas
  - Tempo médio de entrega
  - Satisfação do cliente
- **Top performers:**
  - Melhores motoboys
  - Lojistas mais ativos
- **Análises temporais:**
  - Estatísticas diárias
  - Tendências de crescimento

### **7. 🏪 Gestão de Inventário (NOVO)**
- **Monitorar inventários** de todas as lojas
- **Relatórios de estoque:**
  - Produtos em baixo estoque
  - Categorias mais vendidas
  - Performance por lojista
- **Sistema de upload em lote** funcionando

---

## 🔐 **PERMISSÕES ADMINISTRATIVAS**

Seu email `junior.lima@srdeliveri.com` possui as seguintes permissões:

```
✅ FULL_ACCESS - Acesso completo ao sistema
✅ SECURITY - Gestão de segurança e alertas
✅ FINANCE - Relatórios financeiros completos
✅ MODERATION - Ações sobre usuários
✅ ANALYTICS - Métricas e análises
✅ INVENTORY - Gestão de inventário
✅ SYSTEM - Configurações do sistema
```

---

## 🛠️ **ENDPOINTS DA API ADMINISTRATIVA**

Caso precise integrar com sistemas externos:

```
GET /api/admin/dashboard       - Dashboard principal
GET /api/admin/users          - Gestão de usuários
GET /api/admin/deliveries     - Gestão de entregas
POST /api/admin/user/{id}/action - Ações sobre usuários
GET /api/admin/analytics      - Métricas avançadas
GET /api/admin/financial-report - Relatórios financeiros
```

**Autenticação:** Bearer Token (JWT) obtido no login Google

---

## 📱 **ACESSO MOBILE**

O painel administrativo é **responsivo** e pode ser acessado via:
- 💻 **Desktop** (recomendado)
- 📱 **Tablet** 
- 📲 **Smartphone**

---

## 🆘 **SUPORTE TÉCNICO**

Em caso de problemas de acesso:

1. **Verificar email:** Certifique-se de usar `junior.lima@srdeliveri.com`
2. **Limpar cache:** Ctrl+F5 ou limpar dados do navegador
3. **Verificar conexão:** Confirmar acesso à internet
4. **Browser:** Usar Chrome, Firefox ou Edge atualizados

---

## 🚀 **DEPLOY E ATUALIZAÇÕES**

O sistema está configurado para **deploy automatizado**:

```bash
# Deploy para produção
./deploy.sh

# Verificar status do serviço
gcloud run services describe srboy-delivery --region=us-central1
```

**URL Final do Admin:** https://srdeliveri.com (aba Admin após login)

---

**🎯 RESUMO: Faça login em https://srdeliveri.com com junior.lima@srdeliveri.com via Google OAuth e acesse a aba "Admin" para controle total da plataforma SrBoy!**