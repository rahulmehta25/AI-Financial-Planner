{{/*
Expand the name of the chart.
*/}}
{{- define "financial-planning.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "financial-planning.fullname" -}}
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
{{- define "financial-planning.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "financial-planning.labels" -}}
helm.sh/chart: {{ include "financial-planning.chart" . }}
{{ include "financial-planning.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: financial-planning
app.kubernetes.io/component: backend
{{- end }}

{{/*
Selector labels
*/}}
{{- define "financial-planning.selectorLabels" -}}
app.kubernetes.io/name: {{ include "financial-planning.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "financial-planning.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "financial-planning.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Return the proper image name
*/}}
{{- define "financial-planning.image" -}}
{{- $registryName := .Values.image.registry -}}
{{- $repositoryName := .Values.image.repository -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion | toString -}}
{{- if .Values.global }}
    {{- if .Values.global.imageRegistry }}
     {{- $registryName = .Values.global.imageRegistry -}}
    {{- end -}}
{{- end -}}
{{- if $registryName }}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- else -}}
{{- printf "%s:%s" $repositoryName $tag -}}
{{- end -}}
{{- end -}}

{{/*
Return the proper Docker Image Registry Secret Names
*/}}
{{- define "financial-planning.imagePullSecrets" -}}
{{- include "common.images.pullSecrets" (dict "images" (list .Values.image) "global" .Values.global) -}}
{{- end -}}

{{/*
Create the name of the ConfigMap
*/}}
{{- define "financial-planning.configMapName" -}}
{{- printf "%s-config" (include "financial-planning.fullname" .) -}}
{{- end -}}

{{/*
Create the name of the Secret
*/}}
{{- define "financial-planning.secretName" -}}
{{- printf "%s-secrets" (include "financial-planning.fullname" .) -}}
{{- end -}}

{{/*
Generate backend secret key
*/}}
{{- define "financial-planning.secretKey" -}}
{{- if .Values.secrets.secretKey -}}
{{- .Values.secrets.secretKey -}}
{{- else -}}
{{- randAlphaNum 64 -}}
{{- end -}}
{{- end -}}

{{/*
Generate database URL
*/}}
{{- define "financial-planning.databaseUrl" -}}
{{- if .Values.secrets.databaseUrl -}}
{{- .Values.secrets.databaseUrl -}}
{{- else if .Values.postgresql.enabled -}}
{{- printf "postgresql://%s:%s@%s-postgresql:5432/%s" .Values.postgresql.auth.username .Values.postgresql.auth.password .Release.Name .Values.postgresql.auth.database -}}
{{- else -}}
{{- required "Database URL is required when PostgreSQL is not enabled" .Values.secrets.databaseUrl -}}
{{- end -}}
{{- end -}}

{{/*
Generate Redis URL
*/}}
{{- define "financial-planning.redisUrl" -}}
{{- if .Values.secrets.redisUrl -}}
{{- .Values.secrets.redisUrl -}}
{{- else if .Values.redis.enabled -}}
{{- if .Values.redis.auth.enabled -}}
{{- printf "redis://:%s@%s-redis-master:6379/0" .Values.redis.auth.password .Release.Name -}}
{{- else -}}
{{- printf "redis://%s-redis-master:6379/0" .Release.Name -}}
{{- end -}}
{{- else -}}
{{- required "Redis URL is required when Redis is not enabled" .Values.secrets.redisUrl -}}
{{- end -}}
{{- end -}}

{{/*
Validate configuration
*/}}
{{- define "financial-planning.validateConfig" -}}
{{- if not .Values.secrets.secretKey -}}
{{- fail "secrets.secretKey is required" -}}
{{- end -}}
{{- if and (not .Values.postgresql.enabled) (not .Values.secrets.databaseUrl) -}}
{{- fail "secrets.databaseUrl is required when postgresql.enabled is false" -}}
{{- end -}}
{{- if and (not .Values.redis.enabled) (not .Values.secrets.redisUrl) -}}
{{- fail "secrets.redisUrl is required when redis.enabled is false" -}}
{{- end -}}
{{- end -}}

{{/*
Blue-Green deployment helpers
*/}}
{{- define "financial-planning.blueGreenSlot" -}}
{{- if .Values.blueGreen.enabled -}}
{{- .Values.blueGreen.activeSlot | default "blue" -}}
{{- else -}}
v1
{{- end -}}
{{- end -}}

{{- define "financial-planning.inactiveSlot" -}}
{{- if eq (include "financial-planning.blueGreenSlot" .) "blue" -}}
green
{{- else -}}
blue
{{- end -}}
{{- end -}}

{{/*
Canary deployment helpers
*/}}
{{- define "financial-planning.canaryWeight" -}}
{{- if .Values.canary.enabled -}}
{{- .Values.canary.weight | default 10 -}}
{{- else -}}
0
{{- end -}}
{{- end -}}

{{/*
Environment-specific configurations
*/}}
{{- define "financial-planning.environment" -}}
{{- .Values.app.environment | default "production" -}}
{{- end -}}

{{/*
Resource limits based on environment
*/}}
{{- define "financial-planning.resources" -}}
{{- if eq (include "financial-planning.environment" .) "production" -}}
requests:
  cpu: 500m
  memory: 1Gi
limits:
  cpu: 2000m
  memory: 2Gi
{{- else -}}
{{- toYaml .Values.resources -}}
{{- end -}}
{{- end -}}