# Projet Fil rouge – Subtitle application

## 1) Architecture cible (composants + responsabilités + flux)

**Composants**
- **API FastAPI** : réception des fichiers, orchestration des jobs, endpoints d’état, résultats, métriques admin, exposition Prometheus.
- **Queue Redis + RQ** : file de traitement asynchrone pour absorber jusqu’à 10 utilisateurs en parallèle.
- **Workers** : exécution CPU/GPU de la transcription, génération SRT et rendu vidéo.
- **Stockage local** : `storage/uploads` (fichiers) et `storage/results` (résultats).
- **DB SQLite** : suivi des jobs, statut, durée, erreurs, contenu des réponses, métriques d’usage.
- **Observabilité** : Prometheus + Grafana (dashboard prêt), logs structurés.

**Flux**
1. `POST /upload` → stockage local + création job DB.
2. `POST /jobs/{job_id}/run` → enfile le job en queue RQ + statut `queued`.
3. Worker → statut `processing` → transcription → génération outputs → statut `completed` ou `failed`.
4. `GET /jobs/{job_id}/status` → état + métadonnées.
5. `GET /jobs/{job_id}/result` → download (ou texte si `text`).
6. `GET /admin/metrics` → agrégats de pilotage.
7. Prometheus scrappe `/metrics` → Grafana dashboard.

## 2) Arborescence (squelette du repo)
```
api/
  app.py
  db.py
  models.py
  queue.py
  settings.py
  storage.py
worker/
  tasks.py
  worker.py
transcription/
  models/
    base.py
    dummy.py
    registry.py
    whisper_model.py
  audio.py
  srt_generator.py
  video_renderer.py
observability/
  prometheus.yml
  grafana/
    dashboards/
      api-dashboard.json
    provisioning/
      datasources/
        datasource.yml
      dashboards/
        dashboard.yml
storage/ (généré)
Dockerfile
Docker-compose.yml
```

## 3) MANUEL D’INSTALLATION

### Prérequis
- Docker + Docker Compose
- CPU récent (GPU optionnel)

### Commandes
```bash
# build + run
docker compose up --build -d

# logs API
docker compose logs -f api

# logs worker
docker compose logs -f worker

# arrêt
docker compose down
```

## 4) DEMO SCRIPT (3 minutes)
1. **Upload**
```bash
curl -F "file=@inputs/input.mp4" http://localhost:8000/upload
```
2. **Lancer job (ex: sous-titres)**
```bash
curl -X POST http://localhost:8000/jobs/<job_id>/run \
  -H "Content-Type: application/json" \
  -d '{"output_type":"subtitle"}'
```
3. **Status**
```bash
curl http://localhost:8000/jobs/<job_id>/status
```
4. **Résultat**
```bash
curl -O http://localhost:8000/jobs/<job_id>/result
```
5. **Admin Metrics**
```bash
curl http://localhost:8000/admin/metrics
```
6. **Observabilité**
- Prometheus : http://localhost:9090
- Grafana : http://localhost:3000 (login par défaut admin/admin)

## 5) TESTS
```bash
pytest -q
```
- Test API : upload + status.
- Test worker : exécution de job `dummy`.

## 6) API (Endpoints requis)
- `POST /upload` : mp4/wav → retourne `job_id`.
- `POST /jobs/{job_id}/run` : lance le traitement (choix de sortie).
- `GET /jobs/{job_id}/status` : état courant.
- `GET /jobs/{job_id}/result` : download.
- `GET /jobs/{job_id}/preview` : aperçu simple (optionnel).
- `GET /admin/metrics` : stats d’usage.
- `GET /metrics` : Prometheus.

## 7) Plugin system (ajout de modèle)
- Contrat : implémenter `BaseTranscriptionModel` avec `transcribe(audio_path)`.
- Enregistrer la classe dans `transcription/models/registry.py`.
- Choisir le modèle via env `TRANSCRIPTION_MODEL` ou via payload `model_name`.

Exemple :
```python
class MyModel(BaseTranscriptionModel):
    name = "my-model"
    def transcribe(self, audio_path: Path):
        return {"text": "...", "chunks": [...]}
```

## 8) Performance & charge
- Queue RQ + workers → parallélisation jusqu’à 10 jobs simultanés.
- Le traitement < durée échantillon :
  - utiliser un modèle optimisé (ex: `whisper-base` ou `faster-whisper`),
  - activer GPU si dispo,
  - mesurer `duration_seconds` vs durée audio en DB.

## 9) Budget infra (< 10k €/an)
- **Option CPU** : 1 VM 8 vCPU / 32 Go RAM (≈ 4–6k €/an).
- **Option GPU** : 1 VM GPU moyen + stockage local (≈ 8–10k €/an).
- Docker + stockage local : coûts stables, pas de services managés.
