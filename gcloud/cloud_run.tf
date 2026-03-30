resource "google_cloud_run_service" "test" {
  name     = "cloudrun-test"
  location = "asia-southeast1"

  template {
    spec {
      containers {
        image = "us-docker.pkg.dev/cloudrun/container/hello"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}


resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_service.test.name
  location = google_cloud_run_service.test.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
