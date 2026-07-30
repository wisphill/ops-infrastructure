{{- define "base-service.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "base-service.fullname" -}}
{{- if .Values.serviceAccount.name }}
{{- .Values.serviceAccount.name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name (include "base-service.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "base-service.labels" -}}
app.kubernetes.io/name: {{ include "base-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: Helm
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{- end }}

{{- define "base-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "base-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "base-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "base-service.fullname" .) .Values.serviceAccount.name }}
{{- else }}
default
{{- end }}
{{- end }}
