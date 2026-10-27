"""DH RoboLab 3D 3.0: bilingual Flask laboratory for forward kinematics."""
from flask import Flask, jsonify, render_template, request, send_from_directory
from src.experiments import BASE_OUTPUT, generate, validate_run_id
from src.kinematics import DEFAULT_ROWS, DHValidationError, PRESETS, calculate

app = Flask(__name__)
app.json.ensure_ascii = False
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/defaults")
def defaults():
    return jsonify({"presets": PRESETS, "initial": calculate(DEFAULT_ROWS), "convention": "classic-DH"})


@app.post("/api/fk")
def forward_kinematics():
    try:
        body = request.get_json(silent=True) or {}
        return jsonify(calculate(body.get("rows")))
    except (DHValidationError, ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/experiments")
def experiments():
    try:
        body = request.get_json(silent=True) or {}
        joint = int(body.get("joint", 2))
        samples = int(body.get("samples", 91))
        start = body.get("start")
        end = body.get("end")
        result = generate(rows=body.get("rows"), joint=joint, lang=body.get("lang", "pt"),
                          start=float(start) if start is not None else None,
                          end=float(end) if end is not None else None,
                          samples=samples)
        run_id = result["id"]
        result["download_url"] = f"/api/results/{run_id}/resultados.zip"
        result["figure_urls"] = [f"/api/results/{run_id}/{name}" for name in result["figures"]]
        return jsonify(result)
    except (DHValidationError, ValueError, TypeError, OverflowError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/results/<run_id>/<filename>")
def results(run_id, filename):
    allowed = {"resultados.zip", "dados_cinematica.csv", "metadados.json", "trajetoria_3d.png",
               "coordenadas_por_variavel.png", "distancia_origem.png", "deslocamento_incremental.png"}
    if not validate_run_id(run_id) or filename not in allowed:
        return jsonify({"error": "Arquivo não encontrado."}), 404
    folder = BASE_OUTPUT / run_id
    if not (folder / filename).is_file():
        return jsonify({"error": "Arquivo não encontrado."}), 404
    return send_from_directory(folder, filename, as_attachment=filename.endswith((".zip", ".csv")))


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "engine": "numpy-dh-classic", "joint_types": ["R", "P"], "languages": ["pt", "en"], "version": "3.0"})


if __name__ == "__main__":
    print("DH RoboLab 3D 3.0: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
