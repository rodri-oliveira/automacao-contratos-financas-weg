# Guia de Migração para Web - Automação Contratos Financas

## Índice
1. [Arquitetura Proposta](#arquitetura-proposta)
2. [Stack Tecnológica](#stack-tecnológica)
3. [Principais Mudanças](#principais-mudanças)
4. [Benefícios da Migração](#benefícios-da-migração)
5. [Considerações de Implementação](#considerações-de-implementação)
6. [Plano de Migração](#plano-de-migração)

## Arquitetura Proposta

```
automacao-contratos-financas/
├── backend/
│   ├── app/
│   │   ├── api/                    # Endpoints da API
│   │   ├── application/            # Lógica de negócio atual (mantida)
│   │   ├── domain/                 # Domínio atual (mantido)
│   │   └── services/               # Serviços de integração
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/             # Componentes React
│   │   ├── pages/                  # Páginas da aplicação
│   │   └── services/               # Serviços de API
│   └── package.json
```

## Stack Tecnológica

### Backend
- **FastAPI**: Framework web Python moderno e rápido
  - Alta performance
  - Documentação automática (Swagger/OpenAPI)
  - Suporte nativo a async/await
  - Validação de dados integrada
  
- **Pydantic**: Validação de dados e configurações
- **SQLAlchemy**: ORM para persistência de dados
- **Uvicorn**: Servidor ASGI para Python

### Frontend
- **React**: Biblioteca para construção de interfaces
- **Material-UI (MUI)**: Componentes React prontos
- **React Query**: Gerenciamento de estado e cache
- **Axios**: Cliente HTTP

## Principais Mudanças

### Backend

#### 1. Estrutura de API
```python
# backend/app/api/routes/reports.py
from fastapi import APIRouter, UploadFile
from app.application.reports.divergence_report_nfserv_r189 import DivergenceReportNFSERVR189

router = APIRouter()

@router.post("/reports/divergence/nfserv-r189")
async def generate_nfserv_r189_report(
    nfserv_file: UploadFile,
    r189_file: UploadFile
):
    report = DivergenceReportNFSERVR189()
    result = await report.generate_report(
        nfserv_file.file,
        r189_file.file
    )
    return result
```

#### 2. Autenticação
```python
# backend/app/api/auth.py
from fastapi_security import OAuth2PasswordBearer
from app.services.sharepoint import SharePointAuth

async def get_current_user(token: str):
    auth = SharePointAuth()
    return await auth.validate_token(token)
```

### Frontend

#### 1. Interface Principal
```jsx
// frontend/src/pages/Reports.jsx
import { useState } from 'react';
import { 
    Button, 
    Grid, 
    Paper, 
    Typography 
} from '@mui/material';
import { FileUpload } from '../components';
import { generateReport } from '../services/api';

export const Reports = () => {
    const [files, setFiles] = useState({
        nfserv: null,
        r189: null
    });

    const handleGenerate = async () => {
        const result = await generateReport(files.nfserv, files.r189);
        // Tratar resultado
    };

    return (
        <Grid container spacing={3}>
            <Grid item xs={12}>
                <Typography variant="h4">
                    Relatório de Divergências
                </Typography>
            </Grid>
            
            <Grid item xs={6}>
                <FileUpload
                    label="Arquivo NFSERV"
                    onChange={(file) => setFiles({...files, nfserv: file})}
                />
            </Grid>
            
            <Grid item xs={6}>
                <FileUpload
                    label="Arquivo R189"
                    onChange={(file) => setFiles({...files, r189: file})}
                />
            </Grid>

            <Grid item xs={12}>
                <Button 
                    variant="contained" 
                    onClick={handleGenerate}
                >
                    Gerar Relatório
                </Button>
            </Grid>
        </Grid>
    );
};
```

## Benefícios da Migração

1. **Manutenção da Lógica**
   - Lógica de negócio atual mantida quase intacta
   - Apenas adaptações para trabalhar com streams via HTTP
   - Reutilização de código existente

2. **Melhor Experiência do Usuário**
   - Interface mais responsiva e moderna
   - Feedback em tempo real das operações
   - Possibilidade de processamento em background
   - Acesso via browser sem necessidade de instalação

3. **Escalabilidade**
   - Separação clara entre frontend e backend
   - Possibilidade de hospedar em serviços cloud
   - Mais fácil de adicionar novas funcionalidades
   - Melhor gerenciamento de dependências

## Considerações de Implementação

### 1. Tratamento de Arquivos
- Implementar upload em chunks para arquivos grandes
- Validação de tipos de arquivo no frontend
- Armazenamento temporário de arquivos no servidor

### 2. Segurança
- Implementar autenticação OAuth2 com SharePoint
- Validação de CSRF
- Rate limiting para APIs
- Sanitização de dados de entrada

### 3. Performance
- Implementar cache de resultados
- Compressão de respostas
- Lazy loading de componentes React
- Otimização de queries ao SharePoint

## Plano de Migração

### Fase 1: Preparação (2-3 semanas)
- [ ] Setup do ambiente de desenvolvimento
- [ ] Criação da estrutura do projeto
- [ ] Definição de padrões de API
- [ ] Configuração de CI/CD

### Fase 2: Backend (3-4 semanas)
- [ ] Migração da lógica atual para endpoints REST
- [ ] Implementação de autenticação
- [ ] Desenvolvimento de novos serviços
- [ ] Testes de integração

### Fase 3: Frontend (3-4 semanas)
- [ ] Desenvolvimento da interface com React
- [ ] Implementação do fluxo de upload
- [ ] Criação de componentes reutilizáveis
- [ ] Testes de unidade

### Fase 4: Integração (2-3 semanas)
- [ ] Testes end-to-end
- [ ] Otimização de performance
- [ ] Documentação
- [ ] Deploy em ambiente de homologação

### Fase 5: Deploy (1-2 semanas)
- [ ] Validação em produção
- [ ] Treinamento de usuários
- [ ] Monitoramento
- [ ] Suporte inicial

## Conclusão

A migração para web permitirá maior acessibilidade e escalabilidade da aplicação, mantendo a lógica de negócio existente. A escolha do FastAPI e React oferece um equilíbrio entre facilidade de desenvolvimento e performance, com uma curva de aprendizado razoável para a equipe.
