# run this as smallest size
# allow all traffics
# max = 1 instance
# resource "google_cloud_run_v2_service" "test" {
#   name     = "cloudrun-test"
#   location = "asia-southeast1"

#   template {
#     spec {
#       containers {
#         image = "us-docker.pkg.dev/cloudrun/container/hello"

#         resources {
#           limits = {
#             cpu    = "1000m"
#             memory = "128Mi"
#           }
#         }
#       }
#     }

#     metadata {
#       annotations = {
#         "autoscaling.knative.dev/maxScale"  = "1"
#         "run.googleapis.com/cpu-throttling" = "true"
#       }
#     }
#   }

#   traffic {
#     percent         = 100
#     latest_revision = true
#   }
# }


resource "google_cloud_run_v2_service" "test" {
  name     = "cloudrun-test"
  location = "asia-southeast1"

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }

    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"
      resources {
        limits = {
          cpu    = "1000m"
          memory = "128Mi"
        }

        cpu_idle = true
      }
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_v2_service.test.name
  location = google_cloud_run_v2_service.test.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
