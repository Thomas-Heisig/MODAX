{{/*
Expand the name of the chart.
*/}}
{{- define "modax.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "modax.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "modax.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "modax.labels" -}}
helm.sh/chart: {{ include "modax.chart" . }}
{{ include "modax.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "modax.selectorLabels" -}}
app.kubernetes.io/name: {{ include "modax.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "modax.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "modax.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Control Layer labels
*/}}
{{- define "modax.controlLayer.labels" -}}
{{ include "modax.labels" . }}
app.kubernetes.io/component: control-layer
{{- end }}

{{/*
AI Layer labels
*/}}
{{- define "modax.aiLayer.labels" -}}
{{ include "modax.labels" . }}
app.kubernetes.io/component: ai-layer
{{- end }}

{{/*
MQTT Broker labels
*/}}
{{- define "modax.mqtt.labels" -}}
{{ include "modax.labels" . }}
app.kubernetes.io/component: mqtt-broker
{{- end }}

{{/*
TimescaleDB labels
*/}}
{{- define "modax.timescaledb.labels" -}}
{{ include "modax.labels" . }}
app.kubernetes.io/component: database
{{- end }}
