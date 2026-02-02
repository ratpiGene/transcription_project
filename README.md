# Projet fil rouge – Subtitle application

## 1) Architecture logique

**Composants & responsabilités**
- **Web UI** : page utilisateur (upload, choix sortie, run, suivi, résultat) + page admin (métriques, jobs, logs).
- **API Backend (FastAPI)** : orchestration des jobs, validation des entrées/sorties, endpoints JSON pour UI, admin et download.
- **Queue Redis + RQ** : file d’exécution asynchrone pour absorber la concurrence.
- **Workers** : traitement asynchrone (extraction audio, appel au serveur d’inférence, génération SRT, rendu vidéo).
- **Serveur d’inférence** (service dédié) : héberge les modèles de transcription, expose une API stable `/infer`.
- **Stockage local** : `storage/uploads` (sources) et `storage/results` (résultats).
- **DB PostgreSQL** : suivi des jobs, événements, métriques d’usage.
- **Observabilité** : Prometheus + Grafana (dashboard prêt).

**Flux principal**
1. `POST /api/upload` → upload fichier + création job en DB (`PENDING`).
2. `POST /api/jobs/{job_id}/run` → validation sortie + enfilement dans la queue (`QUEUED`).
3. Worker → extraction audio → appel `/infer` → génération SRT → rendu vidéo si demandé → `SUCCEEDED`/`FAILED`.
4. `GET /api/jobs/{job_id}/status` + `GET /api/jobs/{job_id}/result` pour le client.
5. Admin → métriques + liste jobs + logs.

## 2) Architecture technique (conteneurs / ports)
- **api** : FastAPI (port 8000)
- **inference** : FastAPI (port 9000)
- **worker** : RQ worker
- **redis** : queue (port 6379)
- **postgres** : DB (port 5432)
- **prometheus** : métriques (port 9090)
- **grafana** : dashboard (port 3000)

## 3) Arborescence principale
```
api/
  app.py
  db.py
  models.py
  queue.py
  settings.py
  storage.py
inference/
  app.py
  registry.py
worker/
  tasks.py
  worker.py
transcription/
  models/
    base.py
    dummy.py
    whisper_model.py
  audio.py
  srt_generator.py
  video_renderer.py
web/templates/
  index.html
  admin.html
observability/
  prometheus.yml
  grafana/
    dashboards/api-dashboard.json
    provisioning/
storage/ (généré)
Dockerfile
docker-compose.yml
```

## 4) MANUEL D’INSTALLATION

### Prérequis
- Docker + Docker Compose

### Commandes
```bash
# Configurer les identifiants admin (exemple)
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=change_me

# Lancer la stack
docker compose up --build -d

# Stop
docker compose down
```

## 5) MANUEL D’EXPLOITATION

```bash
# Logs API
docker compose logs -f api

# Logs worker
docker compose logs -f worker

# Logs inference
docker compose logs -f inference

# Redémarrage d’un service
docker compose restart api

# Scale workers (concurrence)
docker compose up -d --scale worker=10
```

**Accès**
- UI utilisateur : http://localhost:8000
- UI admin : http://localhost:8000/admin (auth Basic)
- Prometheus : http://localhost:9090
- Grafana : http://localhost:3000 (admin/admin)

## 6) SCÉNARIO DE DÉMONSTRATION (3–5 min)
1. **Upload**
```bash
curl -F "file=@inputs/input.mp4" http://localhost:8000/api/upload
```
2. **Run**
```bash
curl -X POST http://localhost:8000/api/jobs/<job_id>/run \
  -H "Content-Type: application/json" \
  -d '{"output_type":"subtitle"}'
```
3. **Status**
```bash
curl http://localhost:8000/api/jobs/<job_id>/status
```
4. **Résultat**
```bash
curl -O http://localhost:8000/api/jobs/<job_id>/result
```
5. **Admin**
```bash
curl -u admin:change_me http://localhost:8000/api/admin/metrics
```

## 7) API Backend (endpoints requis)
- `POST /api/upload`
- `POST /api/jobs/{job_id}/run`
- `GET /api/jobs/{job_id}/status`
- `GET /api/jobs/{job_id}/result`
- `GET /api/jobs/{job_id}/preview`
- `GET /api/admin/metrics` (auth)
- `GET /api/admin/jobs` (auth)
- `GET /api/admin/jobs/{job_id}/logs` (auth)

## 8) Modèles & extensibilité
- Le serveur d’inférence expose `/infer` et gère le **versioning** via `model_name` + `model_version`.
- Ajouter un modèle :
  1. Implémenter `BaseTranscriptionModel`.
  2. Ajouter dans `inference/registry.py` avec un tuple `(name, version)`.

**Évolution Speaker ID** (futur) :
- Étendre la réponse `/infer` pour inclure des segments `speaker_id`.
- Adapter `generate_srt` pour inclure tags speaker.

## 9) Performance, charge, budget
- **< durée échantillon** : mesure automatique de `duration_seconds` en DB, à comparer avec la durée audio (extraction possible via ffmpeg).
- **Charge** : `--scale worker=10` pour 10 traitements parallèles.
- **Budget** :
  - CPU : VM 8 vCPU / 32 Go (≈ 4–6k €/an)
  - GPU : VM GPU moyen (≈ 8–10k €/an)

## 10) TESTS
```bash
pytest -q
```
- `tests/test_api.py` : upload + status.
- `tests/test_worker.py` : pipeline dummy (mock inference).
