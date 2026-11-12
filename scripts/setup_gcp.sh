#!/usr/bin/env bash
# One-time GCP setup for the PR-sandbox demo. Run from a machine with gcloud, in an
# Argolis (*.altostrat.com) demo project. Prints the GitHub repo variables to set at the end.
#
#   PROJECT_ID=my-argolis-project ./scripts/setup_gcp.sh
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
REGION="${REGION:-us-central1}"
CLUSTER="${CLUSTER:-pr-sandboxes}"
AR_REPO="${AR_REPO:-insurance-qa-demo}"
GITHUB_REPO="${GITHUB_REPO:-gprothia/insurance-qa-demo}"
SA_NAME="${SA_NAME:-gh-pr-sandbox}"
POOL="${POOL:-github}"

gcloud config set project "$PROJECT_ID"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

gcloud services enable container.googleapis.com artifactregistry.googleapis.com \
  iamcredentials.googleapis.com sts.googleapis.com

# 1. Shared Autopilot cluster: each PR gets a namespace on it, not a whole cluster.
gcloud container clusters describe "$CLUSTER" --region "$REGION" >/dev/null 2>&1 \
  || gcloud container clusters create-auto "$CLUSTER" --region "$REGION"

# 2. Artifact Registry for app and test images.
gcloud artifacts repositories describe "$AR_REPO" --location "$REGION" >/dev/null 2>&1 \
  || gcloud artifacts repositories create "$AR_REPO" --repository-format=docker --location "$REGION"

# 3. CI service account: can push images and manage workloads in the cluster.
gcloud iam service-accounts describe "$SA_EMAIL" >/dev/null 2>&1 \
  || gcloud iam service-accounts create "$SA_NAME" --display-name "GitHub PR sandbox CI"

# A new service account can take up to a minute to become visible to IAM, so retry.
retry() {
  for attempt in 1 2 3 4 5 6; do
    "$@" >/dev/null 2>&1 && return 0
    echo "  waiting for IAM to see $SA_EMAIL (attempt $attempt/6)..."
    sleep 15
  done
  "$@" # final attempt: show the real error
}
for role in roles/container.developer roles/artifactregistry.writer; do
  retry gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member "serviceAccount:$SA_EMAIL" --role "$role" --condition=None
done

# 4. Workload Identity Federation: only this GitHub repo can impersonate the SA.
gcloud iam workload-identity-pools describe "$POOL" --location global >/dev/null 2>&1 \
  || gcloud iam workload-identity-pools create "$POOL" --location global --display-name "GitHub"
gcloud iam workload-identity-pools providers describe "$POOL" --location global \
  --workload-identity-pool "$POOL" >/dev/null 2>&1 \
  || gcloud iam workload-identity-pools providers create-oidc "$POOL" \
       --location global --workload-identity-pool "$POOL" \
       --issuer-uri "https://token.actions.githubusercontent.com" \
       --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository" \
       --attribute-condition "assertion.repository=='$GITHUB_REPO'"
retry gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/attribute.repository/$GITHUB_REPO"

cat <<EOF

Done. Set these GitHub repository *variables* (Settings → Secrets and variables → Actions → Variables):
  GCP_PROJECT         = $PROJECT_ID
  GCP_REGION          = $REGION
  GKE_CLUSTER         = $CLUSTER
  AR_REPO             = $AR_REPO
  CI_SERVICE_ACCOUNT  = $SA_EMAIL
  WIF_PROVIDER        = projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/providers/$POOL
EOF
