terraform {
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.0" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_storage_bucket" "lake" {
  name                        = "${var.project_id}-transparencia-lake"
  location                    = var.bq_location
  uniform_bucket_level_access = true
  force_destroy               = false
}

resource "google_bigquery_dataset" "camadas" {
  for_each   = toset(["bronze", "transparencia_silver", "transparencia_gold", "audit"])
  dataset_id = each.key
  location   = var.bq_location
}

# Tabelas externas da bronze: lêem o Parquet direto do GCS, com partições hive (ano=/mes=).
resource "google_bigquery_table" "bronze" {
  for_each            = toset(["bolsa_familia_municipio", "despesas_por_orgao"])
  dataset_id          = google_bigquery_dataset.camadas["bronze"].dataset_id
  table_id            = each.key
  deletion_protection = false

  external_data_configuration {
    source_format = "PARQUET"
    autodetect    = true
    source_uris   = ["gs://${google_storage_bucket.lake.name}/bronze/${each.key}/*"]
    hive_partitioning_options {
      mode              = "AUTO"
      source_uri_prefix = "gs://${google_storage_bucket.lake.name}/bronze/${each.key}/"
    }
  }
}

resource "google_service_account" "pipeline" {
  account_id   = "transparencia-pipeline"
  display_name = "Pipeline Portal da Transparência"
}

resource "google_storage_bucket_iam_member" "pipeline_gcs" {
  bucket = google_storage_bucket.lake.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_project_iam_member" "pipeline_bq" {
  for_each = toset(["roles/bigquery.dataEditor", "roles/bigquery.jobUser"])
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.pipeline.email}"
}
