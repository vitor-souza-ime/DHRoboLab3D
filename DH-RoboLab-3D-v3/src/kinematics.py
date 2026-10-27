"""Cinemática direta de três juntas R/P pela convenção Denavit–Hartenberg CLÁSSICA.

A_i = Rot_z(theta_i) Trans_z(d_i) Trans_x(a_i) Rot_x(alpha_i).
R: theta_i é coordenada da junta; d_i é constante geométrica editável.
P: d_i é coordenada da junta; theta_i é constante geométrica editável.

Todos os cálculos são feitos em Python/NumPy.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
import numpy as np


def row(kind: str, theta: float, d: float, a: float, alpha: float) -> dict:
    return {"type": kind, "theta": theta, "d": d, "a": a, "alpha": alpha}


PRESETS: dict[str, list[dict]] = {
    "rrr": [row("R", 45, .20, 0, 90), row("R", 30, 0, .60, 0), row("R", 45, 0, .40, 0)],
    "rrp": [row("R", 45, .20, 0, 90), row("R", 30, 0, .60, -90), row("P", 0, .35, .12, 0)],
    "rpp": [row("R", 45, .20, 0, 90), row("P", 0, .40, .36, 90), row("P", 0, .30, 0, 0)],
    # Três direções prismáticas independentes (eixos z0, z1 e z2 mutuamente ortogonais).
    "ppp": [row("P", 0, .40, 0, 90), row("P", 90, .40, 0, 90), row("P", 0, .40, 0, 0)],
    "extended": [row("R", 0, .20, 0, 90), row("R", 0, 0, .60, 0), row("R", 0, 0, .40, 0)],
    "folded": [row("R", 30, .20, 0, 90), row("R", 70, 0, .60, 0), row("R", -120, 0, .40, 0)],
}
DEFAULT_ROWS = PRESETS["rrr"]


class DHValidationError(ValueError):
    pass


def validated_rows(rows: Sequence[dict]) -> list[dict]:
    if not isinstance(rows, (list, tuple)) or len(rows) != 3:
        raise DHValidationError("Informe exatamente 3 linhas DH (juntas R ou P).")
    clean = []
    for index, item in enumerate(rows, start=1):
        if not isinstance(item, dict):
            raise DHValidationError(f"Linha {index}: objeto inválido.")
        kind = item.get("type", "R")  # Compatibilidade com tabelas da versão 1 (somente R).
        if kind not in ("R", "P"):
            raise DHValidationError(f"Linha {index}: tipo deve ser 'R' ou 'P'.")
        vals = {"type": kind}
        for key in ("theta", "d", "a", "alpha"):
            try:
                raw = item[key]
                if isinstance(raw, (bool, list, dict)) or raw is None:
                    raise TypeError
                vals[key] = float(raw)
            except (ValueError, TypeError, OverflowError, KeyError) as err:
                raise DHValidationError(f"Linha {index}: '{key}' precisa ser numérico.") from err
            if not math.isfinite(vals[key]):
                raise DHValidationError(f"Linha {index}: '{key}' precisa ser finito.")
        if abs(vals["theta"]) > 360 or abs(vals["alpha"]) > 360:
            raise DHValidationError(f"Linha {index}: ângulos devem estar entre -360° e 360°.")
        if abs(vals["d"]) > 5 or abs(vals["a"]) > 5:
            raise DHValidationError(f"Linha {index}: distâncias devem estar entre -5 e 5 metros.")
        clean.append(vals)
    return clean


def dh_matrix(theta_degrees: float, d: float, a: float, alpha_degrees: float) -> np.ndarray:
    """A_i = Rz(theta) Tz(d) Tx(a) Rx(alpha) (DH clássica)."""
    theta, alpha = np.deg2rad([theta_degrees, alpha_degrees])
    ct, st, ca, sa = np.cos(theta), np.sin(theta), np.cos(alpha), np.sin(alpha)
    return np.array([
        [ct, -st * ca, st * sa, a * ct],
        [st, ct * ca, -ct * sa, a * st],
        [0., sa, ca, d],
        [0., 0., 0., 1.],
    ], dtype=float)


def calculate(rows: Sequence[dict]) -> dict:
    params = validated_rows(rows)
    accumulated = np.eye(4)
    transforms, individual = [], []
    origins = [[0., 0., 0.]]
    frames = [{"origin": [0., 0., 0.], "rotation": np.eye(3).tolist()}]
    links = []
    for joint_index, item in enumerate(params, 1):
        initial = accumulated.copy()
        # DH: Tz(d) é aplicado no eixo z_(i-1). O trecho de extensão é explicitado
        # para representar a junta prismática como um segmento linear no gráfico.
        intermediate = (initial @ np.array([0., 0., item["d"], 1.]))[:3]
        A = dh_matrix(item["theta"], item["d"], item["a"], item["alpha"])
        accumulated = accumulated @ A
        end = accumulated[:3, 3].copy()
        individual.append(A.tolist())
        transforms.append(accumulated.tolist())
        origins.append(end.tolist())
        frames.append({"origin": end.tolist(), "rotation": accumulated[:3, :3].tolist()})
        links.append({
            "joint": joint_index,
            "type": item["type"],
            "start": initial[:3, 3].tolist(),
            "after_d": intermediate.tolist(),
            "end": end.tolist(),
            "axis_z": initial[:3, 2].tolist(),
            "active_parameter": "theta" if item["type"] == "R" else "d",
        })
    R = accumulated[:3, :3]
    return {
        "params": params,
        "configuration": "".join(item["type"] for item in params),
        "active_coordinates": [item["theta"] if item["type"] == "R" else item["d"] for item in params],
        "active_units": ["deg" if item["type"] == "R" else "m" for item in params],
        "A_matrices": individual,
        "T_matrices": transforms,
        "T_final": accumulated.tolist(),
        "positions": origins,
        "links": links,
        "frames": frames,
        "end_effector": accumulated[:3, 3].tolist(),
        "rotation_determinant": float(np.linalg.det(R)),
        "orthogonality_error": float(np.linalg.norm(R.T @ R - np.eye(3))),
    }
