# Análise de Sobrevida (Survival Analysis App)

Uma aplicação desktop com interface gráfica (GUI) desenvolvida em Python para a realização de **Análise de Sobrevida Avançada**. O software foi projetado para ambiente acadêmico e de pesquisa, permitindo análises rápidas de curvas de Kaplan-Meier e Modelos de Riscos Proporcionais de Cox de forma automatizada e intuitiva.

## 🛠️ Funcionalidades
* **Carregamento Simples:** Suporte direto para arquivos do Microsoft Excel (`.xlsx`).
* **Análise de Kaplan-Meier:** Geração automática das curvas brutas e cálculo do teste de *Log-rank* para comparação de grupos.
* **Modelo de Regressão de Cox:** Ajuste multivariável com cálculo de Hazard Ratios (HR), Intervalos de Confiança (IC95%) e p-valores.
* **Validação de Premissas Estatísticas:**
  * Teste de Colinearidade através do Fator de Inflação da Variância (**VIF**).
  * Avaliação da premissa de riscos proporcionais usando os **Resíduos de Schoenfeld**.
  * Métrica de acurácia global pelo *Integrated Brier Score* (**IBS**) e Índice de Concordância (**C-index**).
* **Visualização Gráfica Integrada:** Gráficos de Kaplan-Meier, Sobrevida Ajustada, *Forest Plot* de HRs e gráficos de diagnóstico de resíduos.
* **Exportação Completa:** Exportação do relatório textual descritivo e salvamento de todas as figuras em alta resolução (300 DPI).

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
Certifique-se de ter o Python 3.8+ instalado em sua máquina.

### 1. Clonar o Repositório
```bash
git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
cd seu-repositorio

2. Instalar as Dependências

Instale as bibliotecas necessárias utilizando o gerenciador de pacotes pip:
Bash

pip install pandas numpy matplotlib customtkinter lifelines statsmodels openpyxl

3. Rodar a Aplicação

Bash

python NOME_DO_ARQUIVO.py

📊 Estrutura e Métricas Utilizadas

    💡 Nota metodológica: O software calcula de forma automatizada o Evento por Variável (EPV) para alertar o pesquisador sobre o risco de superajuste (overfitting) do modelo caso o EPV seja inferior a 10.

📄 Como Citar Este Software 

Se este software for útil para o desenvolvimento da sua pesquisa, por favor, utilize as referências abaixo para citação:

ABNT
NEVES, Eduardo Borba. Software Estatístico para Análise de Sobrevida. Versão 1.0. [S.l.]: Zenodo, 2026. Software. DOI: 10.5281/zenodo.20858301

APA
Neves, E. B. (2026). Software Estatístico para Análise de Sobrevida (Versão 1.0) [Software]. Zenodo. https://doi.org/10.5281/zenodo.20858301

IEEE
E. B. Neves, "Software Estatístico para Análise de Sobrevida," ver. 1.0, Zenodo, 2026. [Software]. Available: https://doi.org/10.5281/zenodo.20858301

VANCOUVER
Neves EB. Software Estatístico para Análise de Sobrevida [Software]. Versão 1.0. [S.l.]: Zenodo; 2026. Disponível em: https://doi.org/10.5281/zenodo.20858301

