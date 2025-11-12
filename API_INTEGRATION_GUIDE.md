# SuperStandard PCF Agent API - Integration Guide

**Complete guide for integrating PCF agents with Business Process Management (BPM) systems**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [API Endpoints](#api-endpoints)
4. [BPM Integration Patterns](#bpm-integration-patterns)
5. [Camunda Integration Example](#camunda-integration-example)
6. [Error Handling](#error-handling)
7. [Performance Considerations](#performance-considerations)
8. [Security](#security)

---

## Overview

The SuperStandard PCF Agent API provides REST endpoints for executing APQC PCF (Process Classification Framework) agents from BPM systems like Camunda, Activiti, IBM BPM, and others.

**Key Features**:
- ✅ **RESTful API** - Standard HTTP/JSON interface
- ✅ **Async Execution** - Support for long-running processes
- ✅ **BPMN Integration** - Direct integration with service tasks
- ✅ **KPI Tracking** - Built-in performance metrics
- ✅ **OpenAPI Documentation** - Auto-generated API docs
- ✅ **Error Handling** - Comprehensive error responses

**Base URL**: `http://localhost:8000` (development)

**API Documentation**: `http://localhost:8000/docs`

---

## Quick Start

### 1. Install Dependencies

```bash
# Install API dependencies
pip install -r requirements-api.txt

# Verify installation
python -c "import fastapi; import uvicorn; print('✓ Dependencies installed')"
```

### 2. Start the API Server

```bash
# Development mode (auto-reload)
python scripts/run_api.py --reload

# Production mode
python scripts/run_api.py --host 0.0.0.0 --port 8000
```

### 3. Verify Server is Running

```bash
# Health check
curl http://localhost:8000/api/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "agents_available": 1,
  "uptime_seconds": 42,
  "dependencies": {
    "pcf_registry": "ok",
    "agent_loader": "ok"
  }
}
```

### 4. Execute First Agent

```bash
# Execute 1.1.1.1 Identify Competitors
curl -X POST http://localhost:8000/api/pcf/1.1.1.1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "market_segment": "Cloud Infrastructure",
      "geographic_scope": "North America"
    },
    "track_kpis": true
  }'
```

---

## API Endpoints

### Health Check

**GET** `/api/health`

Check API health and get service status.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "agents_available": 1,
  "uptime_seconds": 120,
  "dependencies": {
    "pcf_registry": "ok",
    "agent_loader": "ok"
  }
}
```

---

### Get Agent Metadata

**GET** `/api/pcf/{hierarchy_id}`

Retrieve metadata for a specific PCF agent.

**Parameters**:
- `hierarchy_id` (path): PCF hierarchy ID (e.g., "1.1.1.1")

**Example**:
```bash
curl http://localhost:8000/api/pcf/1.1.1.1
```

**Response**:
```json
{
  "pcf_element_id": "10022",
  "hierarchy_id": "1.1.1.1",
  "level": 4,
  "level_name": "Activity",
  "name": "Identify competitors",
  "description": "Analyze and profile competitors in the market",
  "category_id": "1.0",
  "category_name": "Develop Vision and Strategy",
  "process_id": "1.1.1",
  "process_name": "Assess the external environment",
  "inputs": [
    {
      "name": "market_segment",
      "type": "string",
      "required": true,
      "description": "Target market segment"
    },
    {
      "name": "geographic_scope",
      "type": "string",
      "required": true,
      "description": "Geographic region for analysis"
    }
  ],
  "outputs": [
    {
      "name": "competitors_list",
      "type": "array",
      "description": "List of identified competitors"
    }
  ],
  "kpis": [
    {
      "name": "competitors_identified",
      "type": "count"
    },
    {
      "name": "market_coverage",
      "type": "percentage"
    }
  ],
  "bpmn_model_available": true
}
```

---

### Execute Agent

**POST** `/api/pcf/{hierarchy_id}/execute`

Execute a PCF agent with input data.

**Parameters**:
- `hierarchy_id` (path): PCF hierarchy ID

**Request Body**:
```json
{
  "input_data": {
    "market_segment": "Cloud Infrastructure",
    "geographic_scope": "North America",
    "industry_focus": ["Technology", "SaaS"]
  },
  "delegate_to_children": true,
  "track_kpis": true,
  "timeout_seconds": 300,
  "async_execution": false,
  "correlation_id": "process-instance-12345"
}
```

**Request Fields**:
- `input_data` (object, required): Input parameters for agent
- `delegate_to_children` (boolean): Enable hierarchical execution (default: true)
- `track_kpis` (boolean): Track and return KPI metrics (default: true)
- `timeout_seconds` (integer): Execution timeout (default: 300, max: 3600)
- `async_execution` (boolean): Execute asynchronously (default: false)
- `correlation_id` (string): Correlation ID from BPM process instance

**Response** (Synchronous):
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "success": true,
  "hierarchy_id": "1.1.1.1",
  "pcf_element_id": "10022",
  "agent_name": "Identify competitors",
  "result": {
    "success": true,
    "competitors_count": 10,
    "competitors_list": [...],
    "competitive_landscape": {
      "market_structure": "Competitive",
      "hhi": 745,
      "cr4": 0.52
    },
    "threat_assessment": {
      "overall_threat_level": "Moderate"
    }
  },
  "kpis": [
    {
      "name": "competitors_identified",
      "value": 10
    },
    {
      "name": "market_coverage",
      "value": 0.85
    }
  ],
  "execution_time_ms": 342,
  "started_at": "2025-11-12T10:30:00Z",
  "completed_at": "2025-11-12T10:30:00.342Z",
  "correlation_id": "process-instance-12345"
}
```

**Response** (Async):
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "hierarchy_id": "1.1.1.1",
  "status_url": "/api/pcf/1.1.1.1/status/550e8400-e29b-41d4-a716-446655440000",
  "estimated_completion_seconds": 60,
  "correlation_id": "process-instance-12345"
}
```

---

### Check Execution Status

**GET** `/api/pcf/{hierarchy_id}/status/{execution_id}`

Check the status of an async execution.

**Parameters**:
- `hierarchy_id` (path): PCF hierarchy ID
- `execution_id` (path): Execution ID from async response

**Response**:
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "hierarchy_id": "1.1.1.1",
  "progress_percentage": 65,
  "current_step": "Analyzing competitive landscape",
  "started_at": "2025-11-12T10:30:00Z",
  "updated_at": "2025-11-12T10:30:45Z"
}
```

**Status Values**:
- `pending` - Execution queued but not started
- `running` - Currently executing
- `completed` - Successfully completed
- `failed` - Execution failed
- `timeout` - Execution timed out

---

### Search Agents

**POST** `/api/pcf/search`

Search for PCF agents by text query, level, or category.

**Request Body**:
```json
{
  "query": "competitor",
  "level": 4,
  "category_id": "1.0",
  "limit": 50,
  "offset": 0
}
```

**Response**:
```json
{
  "total": 12,
  "count": 10,
  "offset": 0,
  "results": [
    {
      "hierarchy_id": "1.1.1.1",
      "pcf_element_id": "10022",
      "name": "Identify competitors",
      "level": 4,
      "level_name": "Activity",
      "category_name": "Develop Vision and Strategy",
      "description": "Analyze and profile competitors",
      "has_bpmn": true,
      "relevance_score": 1.0
    }
  ]
}
```

---

## BPM Integration Patterns

### Pattern 1: Synchronous Service Task

**Use Case**: Quick operations (<5 seconds)

**BPMN Configuration**:
```xml
<bpmn:serviceTask id="Task_1_1_1_1"
                  name="Identify competitors"
                  camunda:asyncBefore="true"
                  camunda:delegateExpression="${pcfAgentDelegate}">
  <bpmn:extensionElements>
    <camunda:inputOutput>
      <camunda:inputParameter name="hierarchy_id">1.1.1.1</camunda:inputParameter>
      <camunda:inputParameter name="market_segment">${market_segment}</camunda:inputParameter>
      <camunda:inputParameter name="geographic_scope">${geographic_scope}</camunda:inputParameter>
    </camunda:inputOutput>
  </bpmn:extensionElements>
</bpmn:serviceTask>
```

**Java Delegate** (see [Camunda Integration Example](#camunda-integration-example)):
```java
@Component("pcfAgentDelegate")
public class PCFAgentDelegate implements JavaDelegate {
    @Override
    public void execute(DelegateExecution execution) throws Exception {
        // Get inputs from process variables
        String hierarchyId = (String) execution.getVariable("hierarchy_id");
        Map<String, Object> inputData = extractInputData(execution);

        // Call PCF Agent API
        HttpResponse<String> response = httpClient.post()
            .uri("http://api.superstandard.ai/api/pcf/" + hierarchyId + "/execute")
            .header("Content-Type", "application/json")
            .body(toJson(inputData))
            .send();

        // Parse response
        JsonNode result = objectMapper.readTree(response.body());

        // Set output variables
        execution.setVariable("competitors_list", result.get("result").get("competitors_list"));
        execution.setVariable("threat_level", result.get("result").get("threat_assessment").get("overall_threat_level"));
    }
}
```

---

### Pattern 2: Asynchronous with Callback

**Use Case**: Long-running operations (>5 seconds)

**Flow**:
1. Service task calls API with `async_execution: true`
2. API returns execution ID immediately
3. BPM creates intermediate catch event
4. Polling task checks status periodically
5. On completion, signal intermediate event

**BPMN**:
```xml
<bpmn:serviceTask id="StartAsyncTask" name="Start Analysis"
                  camunda:delegateExpression="${pcfAgentAsyncDelegate}"/>

<bpmn:intermediateCatchEvent id="WaitForCompletion"
                             name="Wait for Analysis">
  <bpmn:messageEventDefinition messageRef="AnalysisComplete"/>
</bpmn:intermediateCatchEvent>

<bpmn:serviceTask id="CheckStatus" name="Check Status"
                  camunda:delegateExpression="${pcfStatusDelegate}"/>
```

---

### Pattern 3: Parallel Execution

**Use Case**: Execute multiple agents in parallel

**BPMN**:
```xml
<bpmn:parallelGateway id="Fork"/>

<bpmn:serviceTask id="Task_1_1_1_1" name="Identify competitors"
                  camunda:delegateExpression="${pcfAgentDelegate}">
  <camunda:inputParameter name="hierarchy_id">1.1.1.1</camunda:inputParameter>
</bpmn:serviceTask>

<bpmn:serviceTask id="Task_1_1_1_2" name="Identify economic trends"
                  camunda:delegateExpression="${pcfAgentDelegate}">
  <camunda:inputParameter name="hierarchy_id">1.1.1.2</camunda:inputParameter>
</bpmn:serviceTask>

<bpmn:parallelGateway id="Join"/>
```

All agents execute in parallel, results aggregated at join gateway.

---

## Camunda Integration Example

### Complete Java Delegate Implementation

**PCFAgentDelegate.java**:
```java
package ai.superstandard.camunda;

import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;

import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import java.util.HashMap;
import java.util.Map;

/**
 * Camunda Java Delegate for PCF Agent execution.
 *
 * Integrates Camunda BPMN service tasks with SuperStandard PCF Agent API.
 *
 * Configuration in BPMN:
 * <camunda:inputOutput>
 *   <camunda:inputParameter name="hierarchy_id">1.1.1.1</camunda:inputParameter>
 *   <camunda:inputParameter name="market_segment">${market_segment}</camunda:inputParameter>
 * </camunda:inputOutput>
 */
@Component("pcfAgentDelegate")
public class PCFAgentDelegate implements JavaDelegate {

    @Value("${pcf.api.base-url:http://localhost:8000}")
    private String apiBaseUrl;

    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;

    public PCFAgentDelegate() {
        this.httpClient = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_2)
            .build();
        this.objectMapper = new ObjectMapper();
    }

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        // 1. Get hierarchy ID from input parameter
        String hierarchyId = (String) execution.getVariable("hierarchy_id");
        if (hierarchyId == null) {
            throw new IllegalArgumentException("hierarchy_id input parameter is required");
        }

        System.out.println("Executing PCF Agent: " + hierarchyId);

        // 2. Build input data from process variables
        Map<String, Object> inputData = extractInputData(execution);

        // 3. Build request body
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("input_data", inputData);
        requestBody.put("delegate_to_children", true);
        requestBody.put("track_kpis", true);
        requestBody.put("correlation_id", execution.getProcessInstanceId());

        String requestJson = objectMapper.writeValueAsString(requestBody);

        // 4. Call PCF Agent API
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(apiBaseUrl + "/api/pcf/" + hierarchyId + "/execute"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(requestJson))
            .build();

        HttpResponse<String> response = httpClient.send(
            request,
            HttpResponse.BodyHandlers.ofString()
        );

        // 5. Check response status
        if (response.statusCode() != 200) {
            throw new RuntimeException(
                "PCF Agent API returned error: " + response.statusCode() +
                " - " + response.body()
            );
        }

        // 6. Parse response
        JsonNode responseJson = objectMapper.readTree(response.body());

        // 7. Extract result and set output variables
        JsonNode result = responseJson.get("result");
        if (result != null) {
            // Set each top-level key as a process variable
            result.fields().forEachRemaining(entry -> {
                String key = entry.getKey();
                try {
                    // Convert JSON to Java object
                    Object value = objectMapper.treeToValue(
                        entry.getValue(),
                        Object.class
                    );
                    execution.setVariable(key, value);
                    System.out.println("Set variable: " + key);
                } catch (Exception e) {
                    System.err.println("Failed to set variable " + key + ": " + e.getMessage());
                }
            });
        }

        // 8. Store execution metadata
        execution.setVariable("pcf_execution_id", responseJson.get("execution_id").asText());
        execution.setVariable("pcf_execution_time_ms", responseJson.get("execution_time_ms").asInt());
        execution.setVariable("pcf_success", responseJson.get("success").asBoolean());

        // 9. Store KPIs if tracked
        JsonNode kpis = responseJson.get("kpis");
        if (kpis != null && kpis.isArray()) {
            Map<String, Object> kpiMap = new HashMap<>();
            kpis.forEach(kpi -> {
                String name = kpi.get("name").asText();
                Object value = kpi.get("value");
                kpiMap.put(name, value);
            });
            execution.setVariable("pcf_kpis", kpiMap);
            System.out.println("Stored " + kpiMap.size() + " KPIs");
        }

        System.out.println("PCF Agent execution completed successfully");
    }

    /**
     * Extract input data from process variables.
     *
     * Looks for variables that match expected inputs for the agent.
     */
    private Map<String, Object> extractInputData(DelegateExecution execution) {
        Map<String, Object> inputData = new HashMap<>();

        // Get all process variables
        Map<String, Object> variables = execution.getVariables();

        // Filter out internal Camunda variables
        variables.forEach((key, value) -> {
            if (!key.startsWith("camunda") && !key.equals("hierarchy_id")) {
                inputData.put(key, value);
            }
        });

        return inputData;
    }
}
```

### Maven Dependencies

**pom.xml**:
```xml
<dependencies>
    <!-- Camunda -->
    <dependency>
        <groupId>org.camunda.bpm</groupId>
        <artifactId>camunda-engine</artifactId>
        <version>7.20.0</version>
    </dependency>

    <!-- Jackson for JSON -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>2.16.0</version>
    </dependency>

    <!-- Spring Boot (optional) -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter</artifactId>
        <version>3.2.0</version>
    </dependency>
</dependencies>
```

---

## Error Handling

### Error Response Format

All errors return standard format:

```json
{
  "error": "Agent not found",
  "error_code": "AGENT_NOT_FOUND",
  "detail": "Agent 1.2.3.4 is not implemented yet. Available: ['1.1.1.1']",
  "hierarchy_id": "1.2.3.4",
  "timestamp": "2025-11-12T10:30:00Z",
  "request_id": "req-12345"
}
```

### Common Error Codes

| Code | HTTP Status | Description | Resolution |
|------|-------------|-------------|------------|
| `AGENT_NOT_FOUND` | 404 | Agent not implemented | Check available agents via `/api/pcf/search` |
| `EXECUTION_ERROR` | 500 | Agent execution failed | Check input data and logs |
| `VALIDATION_ERROR` | 422 | Invalid request body | Verify request schema |
| `TIMEOUT_ERROR` | 504 | Execution timeout | Increase `timeout_seconds` or use async |
| `INTERNAL_ERROR` | 500 | Server error | Check server logs |

### Retry Strategy

Recommended retry logic for BPM integrations:

```java
int maxRetries = 3;
int retryDelay = 2000; // 2 seconds

for (int attempt = 1; attempt <= maxRetries; attempt++) {
    try {
        HttpResponse response = executePCFAgent(hierarchyId, inputData);
        return response; // Success
    } catch (Exception e) {
        if (attempt == maxRetries) {
            throw e; // Give up after max retries
        }
        System.out.println("Attempt " + attempt + " failed, retrying...");
        Thread.sleep(retryDelay * attempt); // Exponential backoff
    }
}
```

---

## Performance Considerations

### Response Times

| Agent Type | Typical Response | Max Recommended Timeout |
|------------|------------------|-------------------------|
| Activity (Level 4) | 100ms - 2s | 300s (5 min) |
| Process (Level 3) | 2s - 30s | 900s (15 min) |
| Process Group (Level 2) | 30s - 5min | 3600s (1 hour) |

### Caching

Agent instances are cached by default:
- First call: ~200ms (load + execute)
- Subsequent calls: ~50ms (execute only)

Disable caching for testing:
```python
registry.get_agent(hierarchy_id, use_cache=False)
```

### Concurrent Executions

API supports concurrent execution:
- 10-50 concurrent requests: Normal performance
- 50-100 concurrent requests: May see increased latency
- 100+ concurrent requests: Consider load balancing

### Load Balancing

For production, deploy multiple API instances behind a load balancer:

```
                    ┌──────────────┐
BPM System ────────►│ Load Balancer│
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ API Instance│    │ API Instance│    │ API Instance│
│      #1     │    │      #2     │    │      #3     │
└─────────────┘    └─────────────┘    └─────────────┘
```

---

## Security

### Authentication (Future Enhancement)

Currently, API has no authentication. For production:

**Option 1: API Keys**
```bash
curl -H "X-API-Key: your-api-key" \
  http://api.superstandard.ai/api/pcf/1.1.1.1/execute
```

**Option 2: OAuth 2.0**
```bash
curl -H "Authorization: Bearer <token>" \
  http://api.superstandard.ai/api/pcf/1.1.1.1/execute
```

**Option 3: Mutual TLS**
- Client certificate authentication
- Recommended for internal BPM integration

### Network Security

**Firewall Rules**:
```
Allow: BPM Server IP → API Server:8000
Deny: Internet → API Server:8000
```

**VPC/Private Network**:
- Deploy API in private subnet
- Use VPN or AWS PrivateLink for BPM integration

### Input Validation

API automatically validates:
- Request schema (via Pydantic)
- Hierarchy ID format
- Required fields

**Prevent injection attacks**:
- Never execute user-provided code
- Sanitize all inputs
- Use parameterized queries (future DB integration)

### Rate Limiting (Future)

Planned rate limiting:
- 100 requests/minute per API key
- 1000 requests/hour per API key

---

## Testing

### Running the Test Suite

```bash
# Start API server
python scripts/run_api.py &

# Run tests
python scripts/test_api.py
```

### Manual Testing with curl

```bash
# Test 1: Health check
curl http://localhost:8000/api/health

# Test 2: Get metadata
curl http://localhost:8000/api/pcf/1.1.1.1

# Test 3: Execute agent
curl -X POST http://localhost:8000/api/pcf/1.1.1.1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "market_segment": "Cloud Infrastructure",
      "geographic_scope": "North America"
    }
  }'

# Test 4: Search agents
curl -X POST http://localhost:8000/api/pcf/search \
  -H "Content-Type: application/json" \
  -d '{"query": "competitor", "limit": 10}'
```

---

## Next Steps

1. **Deploy to Production**
   - Choose hosting (AWS, Azure, GCP)
   - Configure load balancer
   - Set up monitoring

2. **Implement Camunda Delegate**
   - Copy Java code from examples
   - Configure in Spring Boot app
   - Deploy to Camunda

3. **Create More Agents**
   - Implement activities 1.1.1.2 - 1.1.1.7
   - Expand to other processes
   - Build industry variants

4. **Add Authentication**
   - Implement API key system
   - Configure in BPM delegates
   - Set up key rotation

---

## Support

- **Documentation**: `/docs` endpoint (Swagger UI)
- **Issues**: GitHub Issues
- **Email**: support@superstandard.ai

---

**Last Updated**: 2025-11-12
**API Version**: 1.0.0
**BPMN Compatibility**: 2.0
