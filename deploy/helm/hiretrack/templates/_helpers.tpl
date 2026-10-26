{{/* Shared snippets. "include" them; each takes the root context (.) unless noted. */}}

{{- define "hiretrack.labels" -}}
app.kubernetes.io/part-of: hiretrack
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{/* Labels for one component. Call with (dict "root" . "name" "api"). */}}
{{- define "hiretrack.componentLabels" -}}
{{ include "hiretrack.labels" .root }}
{{ include "hiretrack.selectorLabels" . }}
app.kubernetes.io/version: {{ include "hiretrack.tag" .root | quote }}
{{- end }}

{{/* The stable subset used in selectors (never change these on a live Deployment). */}}
{{- define "hiretrack.selectorLabels" -}}
app.kubernetes.io/name: {{ .name }}
app: {{ .name }}
{{- end }}

{{- define "hiretrack.tag" -}}
{{ .Values.image.tag | default .Chart.AppVersion }}
{{- end }}

{{/* Full image reference. Call with (dict "root" . "repo" "hiretrack-api"). */}}
{{- define "hiretrack.image" -}}
{{- $registry := .root.Values.image.registry -}}
{{- if $registry -}}{{ $registry }}/{{ end -}}{{ .repo }}:{{ include "hiretrack.tag" .root }}
{{- end }}

{{/* Pod-level security: non-root, fixed UID, default seccomp profile. */}}
{{- define "hiretrack.podSecurityContext" -}}
{{ toYaml .Values.podSecurity }}
{{- end }}

{{/* Container-level security: read-only root FS, no privilege escalation, no capabilities. */}}
{{- define "hiretrack.containerSecurityContext" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
capabilities:
  drop: ["ALL"]
{{- end }}

{{/* One key from the app Secret as an env var. Call with (dict "root" . "key" "DB_PASSWORD"). */}}
{{- define "hiretrack.secretEnv" -}}
- name: {{ .key }}
  valueFrom:
    secretKeyRef:
      name: {{ .root.Values.existingSecret }}
      key: {{ .key }}
      {{- if .optional }}
      optional: true
      {{- end }}
{{- end }}

{{/* Shared ConfigMap env + a checksum annotation key, so pods roll when config changes. */}}
{{- define "hiretrack.envFrom" -}}
- configMapRef:
    name: {{ .Release.Name }}-env
{{- end }}

{{- define "hiretrack.configChecksum" -}}
checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
{{- end }}

{{/* Mount the optional sources/skills overrides over the files baked into the image. */}}
{{- define "hiretrack.filesVolume" -}}
{{- if or .Values.files.sourcesYaml .Values.files.skillsYaml }}
- name: config-files
  configMap:
    name: {{ .Release.Name }}-files
{{- end }}
{{- end }}

{{- define "hiretrack.filesMount" -}}
{{- if or .Values.files.sourcesYaml .Values.files.skillsYaml }}
- name: config-files
  mountPath: /app/config
  readOnly: true
{{- end }}
{{- end }}
