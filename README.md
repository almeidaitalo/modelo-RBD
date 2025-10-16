# Modelo Avançado RBD — Conexão ao site da UFS

**Resumo**  
Repositório com scripts para gerar um relatório técnico (PDF) que modela a disponibilidade da conexão fim-a-fim ao site da UFS usando um *Reliability Block Diagram* (RBD). O modelo lê automaticamente a saída de um `traceroute` (arquivo `tr.txt`), identifica blocos do caminho, atribui parâmetros de confiabilidade (λ, μ), calcula MTTF/MTTR, disponibilidade por componente, disponibilidade total e downtime anual, e gera um PDF com tabela, diagrama e gráfico de contribuição ao downtime.

---

## 📁 Conteúdo do repositório

- `rbd_ufs_avancado.py` — script principal (gera PDF e gráfico).  
- `tr.txt` — exemplo de saída de `traceroute`.  
- `rbd_ufs_avancado.pdf` — exemplo de relatório gerado.  
- `downtime_contrib.png` — gráfico auxiliar gerado pelo script.  
- `README.md` — este arquivo.

---

## ⚙️ Requisitos

- Python 3.8+ (recomendado 3.10 ou superior)  
- Bibliotecas:
  - `reportlab`
  - `matplotlib`

Instalação:
```bash
pip install reportlab matplotlib
```

Ambiente virtual (opcional):
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# ou
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

---

## ▶️ Como usar

1. Coloque o arquivo `tr.txt` com o conteúdo do seu traceroute.  
   Exemplo:
   ```
   Rastreando a rota para mosqueiro.ufs.br [200.17.141.14]
   com no máximo 30 saltos:
     1     1 ms     1 ms     1 ms  192.168.0.1
     2     9 ms     3 ms     2 ms  100.96.0.1
     ...
   ```

2. Execute o script:
   ```bash
   python rbd_ufs_avancado.py
   ```

3. O relatório será gerado automaticamente:
   - `rbd_ufs_avancado.pdf`
   - `downtime_contrib.png`

---

## 📊 O que o relatório contém

- **Tabela técnica** com λ, μ, MTTF, MTTR, disponibilidade e contribuição ao downtime.  
- **Diagrama RBD** em série mostrando a rota completa.  
- **Gráfico de barras** com a contribuição percentual de downtime.  
- **Resultados finais**: disponibilidade total, downtime anual e número de “nines”.

---

## 📈 Interpretação dos resultados

- Disponibilidade total típica: **~98.2%**  
- Downtime estimado: **~155 horas/ano (~6,5 dias)**  
- Melhorias possíveis:
  - Redundância de servidores (cluster UFS).  
  - Links redundantes (ISP ou backbone).  
  - Equipamentos com maior MTTF.

---

## 🧠 Personalização

- Ajuste os parâmetros `PARAMS` no script conforme seus dados reais.  
- Adicione novos tipos de componentes ou modelagem em paralelo.  
- Exporte resultados para CSV/JSON.  


---

## 📜 Licença

```
MIT License
Copyright (c) 2025 Ítalo
```

---

## 📚 Referências

- Parâmetros de confiabilidade baseados no artigo *“Sensitivity analysis of a hierarchical model of mobile cloud computing”* e outras fontes de engenharia de confiabilidade.
