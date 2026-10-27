# Protocolo de experimentos cinemáticos — DH RoboLab 3D 3.0

## Objetivo

Validar a cinemática direta DH clássica para juntas rotacionais e prismáticas e demonstrar suas diferenças no ambiente 3D.

## Ensaios reproduzíveis

- E1 (RRR): variação de θ₂ de -90° a +90°, 91 amostras: trajetória curvilínea em geral.
- E2 (RRP): variação de d₃ de 0 a 1,2 m, 91 amostras: trajetória retilínea ao longo de z₂.
- E3 (RPP): variação de d₂ de 0 a 1,2 m, 91 amostras: trajetória retilínea ao longo de z₁.
- E4 (PPP): variação de d₁ de 0 a 1,2 m, 91 amostras: deslocamento retilíneo vertical.

## Métricas

Coordenadas x,y,z; distância do efetuador à origem; comprimento percorrido; incremento de posição entre amostras; determinante da rotação e erro de ortogonalidade. Testes matemáticos devem confirmar que uma variação Δd numa junta P desloca o efetuador em Δd no eixo z da junta anterior (com demais juntas fixas).

## Atenção metodológica

São medidas de geometria e conformidade algorítmica. Não permitem afirmar melhoria de aprendizado sem avaliação educacional. Para um artigo, apresentar a plataforma como protótipo didático acompanhado de validação computacional, sem alegar resultados com estudantes.

## Idioma dos resultados

O idioma do experimento pode ser `pt` ou `en` e é registrado em `metadados.json` como `language`. Os quatro gráficos PNG gerados no momento da varredura são legendados nesse idioma. Os cabeçalhos CSV preservam o formato padrão, independente do idioma da interface.
