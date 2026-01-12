(1) Frontend Web UI (HTML/JS)
   - système de login & session pour chaque user
   - un seul service pour faire du dépot de fichier 
   - réception des outputs

        |
        v
(2) FastAPI backend
   - reçoit le fichier uploadé
   - valide MP4/WAV -> appeler des méthodes et classes pour parser en auto 
   - valide les outputs choisis
   - sauvegarde le fichier temporairement
   - crée une tâche Celery
        |
        v
(3) Redis
   - stocke l’état de la tâche
   - stocke l’avancement
        |
        v
(4) Celery Worker
   - extrait audio (RAM ou /tmp)
   - Whisper → transcription
   - génère outputs demandés
   - stocke outputs dans /tmp/output/<task_id>/
        |
        v
(5) FastAPI sert les résultats
   - l’UI poll régulièrement /status/<task_id>
   - quand terminé → propose les liens de download