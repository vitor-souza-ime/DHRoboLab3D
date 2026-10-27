"""Experimentos reprodutíveis R/P: uma variável articular por vez, gráficos e CSV."""
from __future__ import annotations

import csv
import json
import math
import re
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .kinematics import DEFAULT_ROWS, calculate, validated_rows

BASE_OUTPUT = Path(__file__).resolve().parents[1] / "outputs"


def _save_charts(run_dir: Path, values: np.ndarray, xyz: np.ndarray, joint: int, kind: str,
                 lang: str = "pt") -> None:
    texts = {
        "pt": {"deg": "graus", "position": "Posição (m)", "coords": "Coordenadas do efetuador",
               "trajectory": "Trajetória cartesiana", "start": "Início", "end": "Fim",
               "distance": "Distância à base (m)", "distance_title": "Distância do efetuador à origem",
               "increment": "Distância entre amostras (m)", "increment_title": "Deslocamento cartesiano por incremento",
               "joint": "Junta"},
        "en": {"deg": "degrees", "position": "Position (m)", "coords": "End-effector coordinates",
               "trajectory": "Cartesian trajectory", "start": "Start", "end": "End",
               "distance": "Distance from base (m)", "distance_title": "End-effector distance from origin",
               "increment": "Distance between samples (m)", "increment_title": "Cartesian displacement per increment",
               "joint": "Joint"},
    }[lang]
    param_label = f"θ{joint} ({texts['deg']})" if kind == "R" else f"d{joint} (m)"
    plt.rcParams.update({"font.size": 10, "figure.dpi": 125})
    fig, ax = plt.subplots(figsize=(9, 5))
    for k, label in enumerate(("X", "Y", "Z")):
        ax.plot(values, xyz[:, k], lw=2, label=label)
    ax.set(xlabel=param_label, ylabel=texts["position"],
           title=f"{texts['coords']} · {texts['joint']} {joint} ({kind})")
    ax.grid(alpha=.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(run_dir / "coordenadas_por_variavel.png")
    plt.close(fig)

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot(xyz[:, 0], xyz[:, 1], xyz[:, 2], lw=2.5)
    ax.scatter(*xyz[0], s=70, marker="o", label=texts["start"])
    ax.scatter(*xyz[-1], s=70, marker="x", label=texts["end"])
    ax.set(xlabel="X (m)", ylabel="Y (m)", zlabel="Z (m)",
           title=f"{texts['trajectory']} · {texts['joint']} {joint} ({kind})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(run_dir / "trajetoria_3d.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(values, np.linalg.norm(xyz, axis=1), lw=2)
    ax.set(xlabel=param_label, ylabel=texts["distance"],
           title=texts["distance_title"])
    ax.grid(alpha=.25)
    fig.tight_layout()
    fig.savefig(run_dir / "distancia_origem.png")
    plt.close(fig)

    # Linear P tende a trajetória cartesiana reta; R pode gerar arco.
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(values[1:], np.linalg.norm(np.diff(xyz, axis=0), axis=1), lw=2)
    ax.set(xlabel=param_label, ylabel=texts["increment"],
           title=texts["increment_title"])
    ax.grid(alpha=.25)
    fig.tight_layout()
    fig.savefig(run_dir / "deslocamento_incremental.png")
    plt.close(fig)


def generate(rows: list[dict] | None = None, joint: int = 2,
             start: float | None = None, end: float | None = None,
             samples: int = 91, output_root: Path | None = None,
             lang: str = "pt") -> dict:
    if lang not in ("pt", "en"):
        raise ValueError("Language must be 'pt' or 'en'.")
    rows = validated_rows(rows if rows is not None else DEFAULT_ROWS)
    if isinstance(joint, bool) or not isinstance(joint, int) or joint not in (1, 2, 3):
        raise ValueError("Articulação deve ser 1, 2 ou 3.")
    if isinstance(samples, bool) or not isinstance(samples, int) or not 5 <= samples <= 361:
        raise ValueError("Número de amostras deve estar entre 5 e 361.")
    kind = rows[joint - 1]["type"]
    variable = "theta" if kind == "R" else "d"
    unit = "graus" if kind == "R" else "m"
    if start is None:
        start = -90. if kind == "R" else 0.
    if end is None:
        end = 90. if kind == "R" else 1.2
    if not all(math.isfinite(x) for x in (start, end)) or start >= end:
        raise ValueError("Intervalo inválido: valores finitos e início inferior ao fim são necessários.")
    bound = 360 if kind == "R" else 5
    if min(start, end) < -bound or max(start, end) > bound:
        raise ValueError(f"Intervalo da junta {kind} deve estar entre {-bound} e {bound} {unit}.")

    root = Path(output_root) if output_root is not None else BASE_OUTPUT
    root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
    run_dir = root / run_id
    run_dir.mkdir()
    values = np.linspace(float(start), float(end), samples)
    xyz = np.empty((samples, 3))
    for i, value in enumerate(values):
        configured = [dict(item) for item in rows]
        configured[joint - 1][variable] = float(value)
        xyz[i, :] = calculate(configured)["end_effector"]

    with (run_dir / "dados_cinematica.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["ponto", "configuracao", "junta", "tipo_junta", "parametro_variado",
                         "unidade_variavel", "valor_variavel", "x_m", "y_m", "z_m", "distancia_m"])
        for i, (value, pos) in enumerate(zip(values, xyz, strict=True), start=1):
            writer.writerow([i, "".join(item["type"] for item in rows), joint, kind, variable, unit,
                             f"{value:.8f}", *[f"{v:.8f}" for v in pos], f"{np.linalg.norm(pos):.8f}"])
    metadata = {
        "id": run_id, "tipo": "varredura_dh_classica", "engine": "numpy-python-fk",
        "configuration": "".join(item["type"] for item in rows),
        "joint": joint, "joint_type": kind, "varied_parameter": variable,
        "parameter_unit": unit, "start": float(start), "end": float(end),
        "samples": samples, "fixed_parameters": rows, "language": lang,
        "coordinate_units": "m", "notes": ("Deterministic forward kinematics model; no educational outcome evaluation."
                   if lang == "en" else "Modelo determinístico de cinemática direta; não avalia resultados de aprendizagem."),
        "x_range_m": [float(xyz[:, 0].min()), float(xyz[:, 0].max())],
        "y_range_m": [float(xyz[:, 1].min()), float(xyz[:, 1].max())],
        "z_range_m": [float(xyz[:, 2].min()), float(xyz[:, 2].max())],
        "travel_distance_m": float(np.linalg.norm(np.diff(xyz, axis=0), axis=1).sum()),
    }
    (run_dir / "metadados.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    _save_charts(run_dir, values, xyz, joint, kind, lang=lang)
    with zipfile.ZipFile(run_dir / "resultados.zip", "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(run_dir.iterdir()):
            if path.name != "resultados.zip":
                z.write(path, arcname=path.name)
    return {**metadata, "figures": ["coordenadas_por_variavel.png", "trajetoria_3d.png",
                                   "distancia_origem.png", "deslocamento_incremental.png"]}


def validate_run_id(value: str) -> bool:
    return bool(re.fullmatch(r"\d{8}T\d{6}-[0-9a-f]{8}", value))
