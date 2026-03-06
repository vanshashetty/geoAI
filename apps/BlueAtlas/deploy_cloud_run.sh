
#!/usr/bin/env bash
set -euo pipefail
SERVICE=${SERVICE:-gee-water-indices}
REGION=${REGION:-us-central1}
PROJECT=${PROJECT:?Set PROJECT=<your-project-id>}

gcloud builds submit --tag gcr.io/$PROJECT/$SERVICE .
gcloud run deploy $SERVICE  --image gcr.io/$PROJECT/$SERVICE  --region $REGION --platform managed  --allow-unauthenticated  --set-env-vars GEE_PROJECT=$PROJECT
