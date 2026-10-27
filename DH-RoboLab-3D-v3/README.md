# DH RoboLab 3D 3.0 — PT / EN · Juntas R/P

Aplicação bilíngue de robótica educativa para experimentar **cinemática direta Denavit–Hartenberg clássica** com 3 juntas rotacionais (R) ou prismáticas (P), em qualquer combinação.

## Executar no Windows

1. Instale Python 3.11 ou superior de 64 bits.
2. Extraia o projeto em uma pasta simples, por exemplo `C:\DH-RoboLab-3D-v3`.
3. Execute `instalar_windows.bat` (cria `.venv` e instala dependências).
4. Execute `iniciar_windows.bat`.
5. Abra `http://127.0.0.1:5000`.

Se preferir o terminal:

```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

## Escolher o idioma / Select language

Na barra superior, clique em `PT` (português) ou `EN` (English). A preferência fica salva no navegador. A troca de idioma não reinicia a pose nem os parâmetros DH. Além dos textos da interface, os novos gráficos PNG gerados pelo laboratório usam o idioma escolhido no momento de executar o experimento. Os arquivos CSV mantêm o esquema de colunas estável para permitir comparações entre experimentos.

The `PT` / `EN` switch in the header changes the interface language without resetting the current robot pose. Newly generated PNG charts use the language selected when the experiment is run; the CSV field names remain stable for reproducibility.

## Como testar

1. Escolha `RRR`, `RRP`, `RPP` ou `PPP` na lista **Configuração**.
2. Altere o **Tipo R/P** de cada linha, se quiser criar uma configuração própria.
3. Altere os controles deslizantes: em R, atua em `θ` (graus); em P, atua em `d` (metros).
4. Observe o braço, os eixos, a posição XYZ e a matriz `T₀³`.
5. Na seção **Experimentos**, selecione uma junta e clique em **Gerar experimento**.
6. Baixe o ZIP com CSV, JSON e quatro gráficos PNG.

**Importante:** Alterar `d` em R ou `θ` em P também pode alterar a pose, pois a tabela DH é editável por inteiro. Entretanto, esses parâmetros não são a variável de atuação da junta correspondente. Não confunda movimento de junta com ajuste geométrico da estrutura.

## Conceitos e limites

Tabela DH clássica de cada junta:

`A_i = RotZ(θ_i) · TransZ(d_i) · TransX(a_i) · RotX(α_i)`.

- Junta R: coordenada de atuação = `θ` (graus); `d` é parâmetro fixo daquela configuração.
- Junta P: coordenada de atuação = `d` (metros); `θ` é parâmetro fixo daquela configuração.
- `a` (metros): comprimento de elo; `α` (graus): torção.
- Um mecanismo físico R/P não muda o tipo da junta por um clique: a troca é uma ferramenta de comparação de modelos cinemáticos.
- O modelo não inclui dinâmica, torques, limites de velocidade, colisões nem desenho mecânico realista.
- As linhas no gráfico representam as transformações DH de cada elo, não um modelo CAD físico.
- O plot apresenta as partes de translação `d` (ao longo de z anterior) e `a` (ao longo do novo x), destacando a primeira para juntas P.
- Não há testes com estudantes; os gráficos são resultados matemáticos reproduzíveis, não resultados de aprendizagem.

## Arquivos principais

- `app.py`: servidor Flask e API.
- `src/kinematics.py`: cálculo NumPy, tabelas pré-configuradas e validação.
- `src/experiments.py`: varredura articular e exportação de dados/gráficos.
- `static/js/app.js`: visualização Plotly 3D e interação.
- `static/js/i18n.js`: textos da interface em português e inglês.
- `static/vendor/plotly.min.js`: Plotly distribuído localmente para funcionar offline.
- `templates/index.html`: interface do laboratório.
- `tests/`: testes matemáticos e das rotas Flask.
- `scripts/gerar_experimento.py`: experimento direto pela linha de comando.
- `exemplos/`: resultados de amostra (gerados com NumPy).

## Linha de comando e testes

```bat
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe scripts\gerar_experimento.py --preset rrp --joint 3 --start 0 --end 1 --samples 91
.venv\Scripts\python.exe scripts\gerar_experimento.py --preset ppp --joint 2 --start 0 --end 1.2 --samples 91
```

Arquivos de resultados são gravados em `outputs/<identificador>`; cada ZIP contém `dados_cinematica.csv`, `metadados.json`, `coordenadas_por_variavel.png`, `trajetoria_3d.png`, `distancia_origem.png` e `deslocamento_incremental.png`.

## Reprodutibilidade

O CSV informa o tipo de junta, o parâmetro variado, a configuração (RRR/RRP/RPP/PPP), unidades, as três posições e a distância à base. Os demais parâmetros ficam fixos e são gravados no JSON. O cálculo é determinístico.
