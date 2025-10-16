"""
Modelo avançado RBD - Conexão ao site da UFS

"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.charts.textlabels import Label
import matplotlib.pyplot as plt
import math
import re
import os

# ----------------------------
# Parâmetros padrão (λ e μ)
# ----------------------------
PARAMS = {
    "terminal":   {"lambda": 0.00004452, "mu": 0.6},       # Dispositivo local
    "node":       {"lambda": 0.003678,   "mu": 1.1367382}, # Roteadores/servidores
    "link":       {"lambda": 0.0001,     "mu": 0.6},       # Link de acesso
    "fw":         {"lambda": 0.00005,    "mu": 0.9},       # Firewall / load balancer
}

# ----------------------------
# Funções auxiliares
# ----------------------------
def disponibilidade(lmb, mu):
    """Calcula disponibilidade A = μ / (λ + μ)."""
    return mu / (lmb + mu)

def parse_traceroute(arquivo):
    """Extrai IPs ou '*' do traceroute."""
    hops = []
    with open(arquivo, "r", encoding="utf-8", errors="ignore") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.lower().startswith(("rastreando", "com ", "trace", "over")):
                continue
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)", linha)
            if m:
                hops.append(m.group(1))
            elif "*" in linha:
                hops.append("*")
    return hops

def identificar_tipo(ip):
    """Classifica tipo do hop."""
    if ip.startswith(("192.168.", "10.")):
        return "node"
    elif ip.startswith("100."):
        return "link"
    elif ip == "*":
        return "fw"
    elif ip.startswith("200.17."):
        return "node"  # servidor final (UFS)
    else:
        return "link"

def construir_blocos(hops):
    """Cria lista de blocos RBD."""
    blocos = [("Dispositivo_Local", "terminal")]
    if not hops:
        return blocos

    for i, ip in enumerate(hops):
        tipo = identificar_tipo(ip)
        nome = f"Hop{i+1}_{ip}" if ip != "*" else f"Hop{i+1}_oculto"
        blocos.append((nome, tipo))

    blocos.append(("Servidor_Web_UFS", "node"))
    return blocos

def gerar_blocos_com_parametros(arquivo_tr):
    """Combina blocos com λ, μ, MTTF, MTTR e A."""
    hops = parse_traceroute(arquivo_tr)
    blocos = construir_blocos(hops)
    resultado = []
    for nome, tipo in blocos:
        lmb = PARAMS.get(tipo, PARAMS["node"])["lambda"]
        mu = PARAMS.get(tipo, PARAMS["node"])["mu"]
        A = disponibilidade(lmb, mu)
        MTTF = 1 / lmb
        MTTR = 1 / mu
        resultado.append((nome, tipo, lmb, mu, MTTF, MTTR, A))
    return resultado

# ----------------------------
# Desenho do diagrama RBD 
# ----------------------------
def draw_rbd(blocks, width=26*cm, height=12*cm): 
    d = Drawing(width, height)
    
    # --- Parâmetros de Layout ---
    box_w = 3.5*cm
    box_h = 1.5*cm
    gap = 0.7*cm  # Espaço horizontal entre caixas
    row_gap = 2.0*cm # Espaço vertical entre linhas
    margin_x = 1*cm
    margin_y = 1*cm

    # Calcula quantos blocos cabem em uma linha
    available_width = width - 2 * margin_x
    blocks_per_row = int(available_width / (box_w + gap))
    
    # Ponto inicial do desenho (canto superior esquerdo)
    x_start = margin_x
    y_start = height - margin_y - box_h

    for i, (name, _, _, _, _, _, A) in enumerate(blocks):
        # Calcula a linha e coluna atual
        row = i // blocks_per_row
        col = i % blocks_per_row
        
        # Calcula as coordenadas x e y da caixa
        x = x_start + col * (box_w + gap)
        y = y_start - row * (box_h + row_gap)
        
        # --- Desenha a caixa e os textos ---
        d.add(Rect(x, y, box_w, box_h, strokeColor=colors.black, fillColor=None))
        
        label = name.replace("_", "\n")
        # Ajusta a posição do texto para centralizar melhor
        d.add(String(x + box_w/2, y + box_h - 0.6*cm, label[:30], textAnchor='middle', fontSize=6))
        d.add(String(x + box_w/2, y + 0.3*cm, f"A={A:.4f}", textAnchor='middle', fontSize=6))
        
        # --- Desenha as linhas de conexão ---
        if i < len(blocks) - 1:
            is_last_in_row = (i + 1) % blocks_per_row == 0
            
            # Ponto de saída da caixa atual (meio da lateral direita)
            from_x, from_y = x + box_w, y + box_h / 2
            
            if not is_last_in_row:
                # Conexão simples para o próximo bloco na mesma linha
                to_x = from_x + gap
                d.add(Line(from_x, from_y, to_x, from_y, strokeColor=colors.black))
            else:
                # Conexão de quebra de linha
                # 1. Linha curta para a direita
                d.add(Line(from_x, from_y, from_x + gap/2, from_y, strokeColor=colors.black))
                # 2. Linha para baixo
                to_y = from_y - (box_h + row_gap)
                d.add(Line(from_x + gap/2, from_y, from_x + gap/2, to_y, strokeColor=colors.black))
                # 3. Linha longa para a esquerda, alinhando com o início da próxima linha
                to_x = x_start - gap/2
                d.add(Line(from_x + gap/2, to_y, to_x, to_y, strokeColor=colors.black))
                # 4. Linha final para conectar ao próximo bloco
                d.add(Line(to_x, to_y, x_start, to_y, strokeColor=colors.black))

    return d
# ----------------------------
# Gráfico de contribuição de downtime
# ----------------------------
def gerar_grafico_downtime(blocks):
    nomes = [n for n, *_ in blocks]
    contribs = [(1 - A) * 100 for *_, A in blocks]

    plt.figure(figsize=(8, 4))
    plt.barh(nomes, contribs)
    plt.xlabel("Contribuição para Downtime (%)")
    plt.tight_layout()
    plt.savefig("downtime_contrib.png", dpi=150)
    plt.close()

# ----------------------------
# Geração do PDF
# ----------------------------
def gerar_pdf(arquivo_tr="tr.txt", saida_pdf="rbd_ufs_avancado.pdf"):
    if not os.path.exists(arquivo_tr):
        print(f"❌ Arquivo '{arquivo_tr}' não encontrado.")
        return

    blocks = gerar_blocos_com_parametros(arquivo_tr)
    gerar_grafico_downtime(blocks)

    # Disponibilidade total
    A_total = 1.0
    for *_, A in blocks:
        A_total *= A
    downtime = (1 - A_total) * 8760
    n9 = -math.log10(1 - A_total)

    doc = SimpleDocTemplate(saida_pdf, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []

    # Cabeçalho
    elements.append(Paragraph("<b>Modelo Avançado RBD - Conexão ao site da UFS</b>", styles["Title"]))
    elements.append(Spacer(1, 0.5*cm))

    # Tabela detalhada
    data = [["Componente", "Tipo", "λ (/h)", "μ (/h)", "MTTF (h)", "MTTR (h)", "Disponibilidade", "Contrib. Downtime (%)"]]
    for nome, tipo, l, m, MTTF, MTTR, A in blocks:
        contrib = (1 - A) * 100
        data.append([nome, tipo, f"{l:.6e}", f"{m:.3f}", f"{MTTF:.1f}", f"{MTTR:.2f}", f"{A:.6f}", f"{contrib:.3f}"])
    table = Table(data, colWidths=[5*cm, 2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.8*cm, 3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('GRID',(0,0),(-1,-1),0.25,colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 1*cm))

    # Diagrama RBD
    elements.append(Paragraph("<b>Diagrama RBD (estrutura em série)</b>", styles['Heading2']))
    elements.append(draw_rbd(blocks))
    elements.append(Spacer(1, 1*cm))

    # Gráfico de contribuição
    if os.path.exists("downtime_contrib.png"):
        elements.append(Paragraph("<b>Contribuição ao Downtime (%)</b>", styles['Heading2']))
        elements.append(Image("downtime_contrib.png", width=18*cm, height=7*cm))
        elements.append(Spacer(1, 1*cm))

    # Resultados finais
    texto = f"""
    <b>Resultados do modelo:</b><br/>
    Disponibilidade total: <b>{A_total:.10f}</b> ({A_total*100:.4f}%)<br/>
    Downtime anual estimado: <b>{downtime:.2f} horas</b> (~{downtime/24:.2f} dias)<br/>
    Número de 'nines': <b>{n9:.3f}</b>
    """
    elements.append(Paragraph(texto, styles['Normal']))

    # Gera PDF
    doc.build(elements)
    print(f"✅ Arquivo '{saida_pdf}' gerado com sucesso!")

# ----------------------------
# Execução principal
# ----------------------------
if __name__ == "__main__":
    gerar_pdf("tr.txt")
