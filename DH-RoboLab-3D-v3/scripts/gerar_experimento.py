"""CLI: python scripts/gerar_experimento.py --preset ppp --joint 2 --start 0 --end 1.2"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.experiments import generate
from src.kinematics import PRESETS

p = argparse.ArgumentParser(description="Varredura DH clássica R/P e exportação de gráficos")
p.add_argument("--preset", choices=sorted(PRESETS), default="rrr")
p.add_argument("--joint", type=int, choices=[1,2,3], default=2)
p.add_argument("--start", type=float, default=None)
p.add_argument("--end", type=float, default=None)
p.add_argument("--samples", type=int, default=91)
a = p.parse_args()
r = generate(rows=PRESETS[a.preset], joint=a.joint, start=a.start, end=a.end, samples=a.samples)
print(f"Configuração: {r['configuration']}")
print(f"Junta: {r['joint']} ({r['joint_type']}) | variável: {r['varied_parameter']} ({r['parameter_unit']})")
print(f"Pontos: {r['samples']}")
print(f"ZIP com CSV e gráficos: outputs/{r['id']}/resultados.zip")
