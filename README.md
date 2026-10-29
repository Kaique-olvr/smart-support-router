# Smart Support Router API

Microsserviço em Python e FastAPI para analisar tickets de suporte, classificar o departamento correto, priorizar o atendimento e sugerir a ação imediata com apoio de IA do Google Gemini.

---

## Por que esse projeto existe?

O objetivo principal é reduzir o tempo de triagem humana em operações de suporte ao cliente. Em vez de um atendente precisar ler cada ticket manualmente, a API recebe a mensagem do cliente, usa um modelo de linguagem para inferir o contexto e devolve uma classificação estruturada.

Isso ajuda a responder perguntas como:

- para qual área o ticket deve ir?
- qual é a urgência?
- qual ação o time deve tomar primeiro?
- o problema parece confiável ou precisa de revisão humana?

---

## Visão geral do fluxo

1. O cliente envia um payload com `ticket_id` e `customer_message`.
2. A aplicação valida os dados com Pydantic.
3. O serviço de IA monta um prompt específico para a classificação.
4. O modelo do Gemini retorna JSON estruturado.
5. A API valida esse retorno e devolve um objeto padronizado para o cliente.

---

## Tecnologias

- Python 3.11+
- FastAPI
- Pydantic
- Google GenAI SDK
- Uvicorn
- Pytest

---

## Requisitos

- Python 3.11 ou superior
- Ambiente virtual recomendado
- Chave de API do Google Gemini

---

## Configuração do ambiente

1. Clone o repositório:

```bash
git clone https://github.com/Kaique-olvr/smart-support-router.git
cd smart-support-router
```

2. Crie e ative um ambiente virtual:

No Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

No macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Configure a variável de ambiente com sua chave do Gemini.

Use um arquivo `.env` na raiz do projeto baseado em [.env.example](.env.example):

```env
GEMINI_API_KEY=sua_chave_aqui
# ou
GOOGLE_API_KEY=sua_chave_aqui
```

> Importante: nunca versionar a chave real do ambiente. O arquivo `.env` deve ficar local e fora do Git.

---

## Executando a API

Inicie o servidor com:

```bash
uvicorn app.main:app --reload
```

A API ficará disponível em:

- http://127.0.0.1:8000

Documentação automática:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc

---

## Como o código funciona

### 1) Schemas e validação
Arquivo: [app/schemas.py](app/schemas.py)

Aqui ficam os modelos de entrada e saída. O Pydantic garante que:

- apenas campos esperados chegam ao sistema
- strings tenham tamanho mínimo e máximo
- o retorno da IA se encaixe no contrato esperado
- enums como `DepartmentEnum` e `PriorityEnum` sejam consistentes

Isso é importante porque a API conversa com outra máquina: a IA produz texto, mas a aplicação precisa transformar isso em dados confiáveis.

### 2) Serviço de IA
Arquivo: [app/ai_service.py](app/ai_service.py)

Essa parte monta um prompt com o contexto do ticket e chama o Google Gemini. Ela também tenta validar a resposta da IA como JSON, usando o schema do Pydantic para manter a estrutura do retorno consistente.

Essa camada existe para isolar toda a lógica externa da IA do endpoint HTTP. Assim, a rota não precisa conhecer detalhes do SDK do Gemini.

### 3) Endpoint da API
Arquivo: [app/main.py](app/main.py)

O FastAPI expõe o endpoint `/api/v1/tickets/analyze`. Ele:

- recebe a requisição
- valida o payload
- chama o serviço de IA
- trata falhas sem vazar detalhes internos
- devolve a resposta formatada

Essa separação deixa o projeto mais fácil de testar e manter.

### 4) Testes
Arquivo: [tests/test_api.py](tests/test_api.py)

Os testes confirmam que:

- a rota de saúde funciona
- entradas muito curtas são rejeitadas
- erros internos da IA não são expostos ao cliente

Isso ajuda a evitar regressões e protege o contrato da API.

---

## Endpoint principal

### POST /api/v1/tickets/analyze

### Payload esperado

```json
{
  "ticket_id": "TCK-98421",
  "customer_message": "Meu pedido atrasou mais de 1 hora, veio tudo frio e cobrou 2 vezes no meu cartão de crédito!"
}
```

### Exemplo de resposta

```json
{
  "department": "Logística e Entregas",
  "priority": "Alta",
  "summary": "Pedido atrasado e com entrega em condições inadequadas, além de cobrança duplicada.",
  "suggested_action": "Validar a entrega, reembolsar o cliente e escalar para logística e financeiro.",
  "confidence_score": 0.93
}
```

---

## Exemplo de teste com curl

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/tickets/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TCK-98421",
    "customer_message": "Meu pedido atrasou mais de 1 hora, veio tudo frio e cobrou 2 vezes no meu cartão de crédito!"
  }'
```

---

## Testes

Para executar a suíte localmente:

```bash
pytest -q
```

---

## Segurança e boas práticas

- nunca commitar arquivos `.env`
- manter chaves sensíveis fora do controle de versão
- validar entradas antes do envio para a IA
- não expor detalhes internos da falha da IA ao cliente
- usar logs para rastrear falhas sem expor dados sensíveis

---

## Observações

Este projeto foi estruturado para servir como base para roteamento inteligente de tickets, com validação de dados e classificação automatizada usando modelo de linguagem. Ele pode ser expandido para regras de negócio, persistência em banco, fila de processamento e integração com sistemas internos de atendimento.

---

## Por que as mudanças foram importantes?

As mudanças de validação, tratamento de erro e isolamento do serviço de IA foram necessárias porque um sistema de IA em produção precisa controlar três pontos críticos:

1. entrada ruim: mensagens vazias ou irrelevantes não devem chegar para o modelo
2. falha externa: a IA pode falhar temporariamente e isso não pode quebrar a API nem expor detalhes internamente
3. consistência: o retorno da IA precisa seguir um contrato rígido para que a aplicação e os consumidores possam confiar no dado

Sem isso, o projeto para de ser um serviço robusto e vira um experimento frágil.
