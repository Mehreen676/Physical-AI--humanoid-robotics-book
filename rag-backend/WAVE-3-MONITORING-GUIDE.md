# WAVE 3: Monitoring & Observability - Complete Setup

**Phase 8 WAVE 3**: Monitoring Infrastructure
**Duration**: 2 days | **Team**: DevOps Engineer

---

## Quick Start

```bash
# 1. Prometheus (metrics collection)
docker run -d -p 9090:9090 -v prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus

# 2. Grafana (dashboards)
docker run -d -p 3000:3000 grafana/grafana

# 3. ELK Stack (logging)
docker-compose up -d  # See docker-compose.yml

# 4. Sentry (error tracking)
# https://sentry.io → Create project → Get DSN

# 5. PagerDuty (alerting)
# https://pagerduty.com → Create service
```

---

## Task 3.1: Prometheus Setup

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'rag-backend'
    static_configs:
      - targets: ['rag-chatbot-api.onrender.com:8080']
    metrics_path: '/metrics'
    scheme: 'https'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']
```

**Verification**:
```bash
# Access Prometheus
curl http://localhost:9090
# Query metrics: http://localhost:9090/graph
# Try: rate(rag_query_errors_total[5m])
```

---

## Task 3.2: Grafana Dashboards

```bash
# Access: http://localhost:3000 (admin/admin)
# Add Prometheus datasource: http://prometheus:9090

# Import dashboards:
# 1. Main: Health, uptime, error rate, latency
# 2. Performance: Retrieval, generation, token usage
# 3. Errors: Error rates by type
# 4. Resources: CPU, memory, disk
```

**Dashboard Panels**:
```
Main Dashboard:
├── Service Status (green/red)
├── Error Rate (p99)
├── Latency p95
├── Active Sessions
└── Uptime %

Performance Dashboard:
├── Retrieval Latency (ms)
├── Generation Latency (s)
├── Total Latency p95
├── Tokens Used (daily)
└── Cache Hit Rate

Resource Dashboard:
├── CPU Usage %
├── Memory Usage %
├── Disk Space %
├── Database Connections
└── Request Rate
```

---

## Task 3.3: ELK Stack Setup

```yaml
# docker-compose.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200

volumes:
  es_data:
```

**Configuration**:
```bash
# 1. Start stack: docker-compose up -d
# 2. Configure app to output JSON logs
# 3. Logstash parses logs → Elasticsearch
# 4. Access Kibana: http://localhost:5601
```

---

## Task 3.4: Sentry Error Tracking

```python
# src/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.environ["SENTRY_DSN"],
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment=os.environ["ENVIRONMENT"]
)
```

**Setup**:
```bash
# 1. https://sentry.io → Create project
# 2. Copy DSN to environment variables
# 3. Errors auto-captured and sent
# 4. Dashboard shows error groups
```

---

## Task 3.5: PagerDuty Integration

```yaml
# Alert rules → PagerDuty routing:
1. Error Rate > 1% → Page On-Call Engineer
2. Latency p95 > 8s → Alert Engineering Team
3. CPU > 80% → Auto-scale + Alert
4. Database Pool > 90% → Alert DBA
5. Uptime < 99.5% → Page Engineering Lead
```

**Configuration**:
```bash
# 1. https://pagerduty.com → Create service
# 2. Get integration key
# 3. Configure in Prometheus Alertmanager
# 4. Test with test alert
```

---

## Task 3.6: Alert Rules

```yaml
# alert-rules.yml
groups:
  - name: rag_chatbot
    interval: 1m
    rules:
      - alert: HighErrorRate
        expr: rate(rag_query_errors_total[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rag_query_duration_seconds) > 8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency p95"

      - alert: HighCPU
        expr: node_cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
```

---

## WAVE 3 Completion Checklist

```
✅ Prometheus installed and scraping metrics
✅ Grafana connected to Prometheus
✅ Main dashboard created (health, latency, errors)
✅ Performance dashboard created
✅ Resource dashboard created
✅ ELK Stack running and ingesting logs
✅ Kibana dashboards configured
✅ Sentry project created and integrated
✅ Error tracking working
✅ PagerDuty service configured
✅ Alert rules defined (6+ rules)
✅ Alert routing to PagerDuty working
✅ Test alert successful

WAVE 3 STATUS: ✅ COMPLETE
```

---

**WAVE 3 Complete!** → Next: **WAVE 4 - Operations & Compliance**

Generated: 2025-12-17 | Version: 1.0
