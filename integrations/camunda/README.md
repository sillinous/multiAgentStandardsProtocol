# SuperStandard PCF Camunda Integration

**Complete Camunda BPM integration for SuperStandard PCF Agent API**

This example demonstrates how to integrate Camunda BPM with the SuperStandard PCF Agent API, enabling execution of APQC PCF business processes through Camunda's workflow engine.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [What's Included](#whats-included)
3. [Quick Start](#quick-start)
4. [Detailed Setup](#detailed-setup)
5. [Running Your First Process](#running-your-first-process)
6. [Project Structure](#project-structure)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [Production Deployment](#production-deployment)

---

## Overview

This integration enables:

- ✅ **Execute PCF agents from BPMN processes** - Call agents as service tasks
- ✅ **Visual process monitoring** - Watch executions in Camunda Cockpit
- ✅ **Process variable mapping** - Automatic input/output handling
- ✅ **KPI tracking** - Built-in performance metrics
- ✅ **Production-ready** - Complete Spring Boot application

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                   Camunda BPM Engine                        │
│                                                              │
│  ┌────────────────┐         ┌──────────────────┐           │
│  │  BPMN Process  │────────►│  Service Task    │           │
│  │  Instance      │         │ (PCF Agent Call) │           │
│  └────────────────┘         └─────────┬────────┘           │
│                                        │                     │
│                              ┌─────────▼────────┐           │
│                              │ PCFAgentDelegate │           │
│                              │  (Java Delegate) │           │
│                              └─────────┬────────┘           │
└────────────────────────────────────────┼─────────────────────┘
                                         │ HTTP POST
                                         ▼
┌─────────────────────────────────────────────────────────────┐
│              SuperStandard PCF Agent API                     │
│                                                              │
│  /api/pcf/{hierarchy_id}/execute                            │
│          ↓                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  PCF Agent   │───►│   Business   │───►│   Result +   │ │
│  │  (1.1.1.1)   │    │    Logic     │    │     KPIs     │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## What's Included

### 1. PCFAgentDelegate.java
Complete Java Delegate implementation for Camunda service tasks.

**Features**:
- Process variable extraction
- HTTP client for API calls
- JSON request/response handling
- Output variable mapping
- KPI extraction and storage
- Comprehensive error handling
- Detailed logging

### 2. Maven Project Configuration (pom.xml)
Complete Maven configuration with all required dependencies:
- Camunda BPM 7.20
- Spring Boot 3.2
- Camunda Web Apps (Cockpit, Tasklist, Admin)
- Camunda REST API
- Jackson for JSON
- H2 database (development)
- PostgreSQL driver (production)

### 3. Spring Boot Application
- `CamundaPCFApplication.java` - Main application class
- `application.properties` - Complete configuration
- Auto-deployment of BPMN models
- Embedded Camunda engine

### 4. Configuration Files
- **application.properties** - Development and production settings
- **Maven pom.xml** - Dependency management
- **README.md** - This comprehensive guide

---

## Quick Start

### Prerequisites

1. **Java 17+**
   ```bash
   java -version
   # Should show: openjdk version "17.x.x" or higher
   ```

2. **Maven 3.6+**
   ```bash
   mvn -version
   # Should show: Apache Maven 3.6.x or higher
   ```

3. **SuperStandard PCF Agent API**
   ```bash
   # In the main project directory
   python scripts/run_api.py --reload
   # API should be running on http://localhost:8000
   ```

### Steps

**1. Create Maven Project Structure**

```bash
# Create directories
mkdir -p integrations/camunda/src/main/java/ai/superstandard/camunda/delegate
mkdir -p integrations/camunda/src/main/resources/bpmn

# Copy the Java files
cp integrations/camunda/PCFAgentDelegate.java \
   integrations/camunda/src/main/java/ai/superstandard/camunda/delegate/

cp integrations/camunda/CamundaPCFApplication.java \
   integrations/camunda/src/main/java/ai/superstandard/camunda/

# Copy configuration files
cp integrations/camunda/application.properties \
   integrations/camunda/src/main/resources/

# Copy pom.xml to project root
cp integrations/camunda/pom.xml \
   integrations/camunda/

# Copy BPMN model
cp src/superstandard/agents/pcf/bpmn_models/process_1_1_1_assess_external_environment.bpmn \
   integrations/camunda/src/main/resources/bpmn/
```

**2. Build the Project**

```bash
cd integrations/camunda
mvn clean package

# Should see: BUILD SUCCESS
```

**3. Run the Application**

```bash
java -jar target/camunda-pcf-integration-1.0.0.jar

# Or use Maven:
mvn spring-boot:run
```

**4. Access Camunda Cockpit**

Open browser to: http://localhost:8080

Login:
- Username: `admin`
- Password: `admin`

---

## Detailed Setup

### Step 1: Verify PCF Agent API

```bash
# Test API health
curl http://localhost:8000/api/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "agents_available": 1
}

# Test agent metadata
curl http://localhost:8000/api/pcf/1.1.1.1

# Expected response: Full agent metadata
```

### Step 2: Build Camunda Application

```bash
cd integrations/camunda

# Clean build
mvn clean

# Compile
mvn compile

# Run tests (optional)
mvn test

# Package JAR
mvn package

# Result: target/camunda-pcf-integration-1.0.0.jar
```

### Step 3: Configure Application

Edit `src/main/resources/application.properties`:

```properties
# PCF Agent API Configuration
pcf.api.base-url=http://localhost:8000

# Database Configuration (H2 for development)
spring.datasource.url=jdbc:h2:mem:camunda

# Camunda Admin Credentials
camunda.bpm.admin-user.id=admin
camunda.bpm.admin-user.password=admin
```

### Step 4: Deploy BPMN Model

Copy BPMN file to resources:

```bash
cp src/superstandard/agents/pcf/bpmn_models/process_1_1_1_assess_external_environment.bpmn \
   integrations/camunda/src/main/resources/bpmn/
```

The BPMN model will be auto-deployed on application startup.

### Step 5: Start Application

```bash
java -jar target/camunda-pcf-integration-1.0.0.jar
```

You should see:
```
================================================================================
SuperStandard PCF Camunda Integration Started
================================================================================

Camunda Web Apps:
  - Cockpit:  http://localhost:8080/camunda/app/cockpit/
  - Tasklist: http://localhost:8080/camunda/app/tasklist/
  - Admin:    http://localhost:8080/camunda/app/admin/

REST API:
  - Camunda:  http://localhost:8080/engine-rest/

Credentials:
  - Username: admin
  - Password: admin
```

---

## Running Your First Process

### Method 1: Via Camunda Cockpit (Visual)

1. **Open Cockpit**: http://localhost:8080/camunda/app/cockpit/
2. **Login**: admin / admin
3. **Navigate to**: Processes → "Assess the external environment"
4. **Click**: "Start Instance"
5. **Set Variables**:
   - `market_segment`: "Cloud Infrastructure"
   - `geographic_scope`: "North America"
6. **Start**: Click "Start"
7. **Monitor**: Watch execution in real-time

### Method 2: Via REST API (Programmatic)

```bash
# Start process instance
curl -X POST http://localhost:8080/engine-rest/process-definition/key/Process_1_1_1/start \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "market_segment": {
        "value": "Cloud Infrastructure",
        "type": "String"
      },
      "geographic_scope": {
        "value": "North America",
        "type": "String"
      },
      "industry_focus": {
        "value": ["Technology", "SaaS"],
        "type": "Json"
      }
    }
  }'
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "definitionId": "Process_1_1_1:1:...",
  "businessKey": null,
  "caseInstanceId": null,
  "ended": false,
  "suspended": false,
  "links": [...]
}
```

### Method 3: Via Java API

```java
@Autowired
private RuntimeService runtimeService;

public void startProcess() {
    Map<String, Object> variables = new HashMap<>();
    variables.put("market_segment", "Cloud Infrastructure");
    variables.put("geographic_scope", "North America");

    ProcessInstance instance = runtimeService.startProcessInstanceByKey(
        "Process_1_1_1",
        variables
    );

    System.out.println("Started process: " + instance.getId());
}
```

### Viewing Results

**In Cockpit**:
1. Navigate to: Processes → Process Instances
2. Click on your instance
3. View: Variables tab
4. See results:
   - `competitors_list` - Array of competitors
   - `threat_assessment` - Threat analysis
   - `pcf_kpis` - Performance metrics

**Via REST API**:
```bash
# Get process instance variables
curl http://localhost:8080/engine-rest/process-instance/{instance-id}/variables
```

**Expected Output Variables**:
```json
{
  "competitors_list": {
    "type": "Json",
    "value": [...]
  },
  "threat_assessment": {
    "type": "Json",
    "value": {
      "overall_threat_level": "Moderate"
    }
  },
  "pcf_execution_id": {
    "type": "String",
    "value": "550e8400-..."
  },
  "pcf_kpis": {
    "type": "Json",
    "value": {
      "competitors_identified": 10,
      "market_coverage": 0.85
    }
  }
}
```

---

## Project Structure

```
integrations/camunda/
├── pom.xml                                    # Maven configuration
├── README.md                                  # This file
├── src/
│   └── main/
│       ├── java/
│       │   └── ai/
│       │       └── superstandard/
│       │           └── camunda/
│       │               ├── CamundaPCFApplication.java      # Main app
│       │               └── delegate/
│       │                   └── PCFAgentDelegate.java       # Service task delegate
│       └── resources/
│           ├── application.properties          # Configuration
│           └── bpmn/
│               └── process_1_1_1_assess_external_environment.bpmn
│
└── target/                                    # Build output
    └── camunda-pcf-integration-1.0.0.jar      # Executable JAR
```

---

## Configuration

### PCF Agent API Settings

```properties
# API base URL
pcf.api.base-url=http://localhost:8000

# Timeout for agent execution
pcf.api.timeout-seconds=300

# Enable KPI tracking
pcf.api.track-kpis=true

# Enable hierarchical delegation
pcf.api.delegate-to-children=true
```

### Database Settings

**Development (H2 in-memory)**:
```properties
spring.datasource.url=jdbc:h2:mem:camunda
spring.datasource.driver-class-name=org.h2.Driver
spring.datasource.username=sa
spring.datasource.password=
```

**Production (PostgreSQL)**:
```properties
spring.datasource.url=jdbc:postgresql://localhost:5432/camunda
spring.datasource.driver-class-name=org.postgresql.Driver
spring.datasource.username=camunda
spring.datasource.password=camunda
```

### Camunda Settings

```properties
# Auto-deploy BPMN files
camunda.bpm.auto-deployment-enabled=true

# Job executor
camunda.bpm.job-execution.enabled=true
camunda.bpm.job-execution.core-pool-size=3
camunda.bpm.job-execution.max-pool-size=10

# History level
camunda.bpm.history-level=FULL

# Admin user
camunda.bpm.admin-user.id=admin
camunda.bpm.admin-user.password=admin
```

---

## Troubleshooting

### Issue: Application won't start

**Error**: "Port 8080 already in use"

**Solution**:
```properties
# Change port in application.properties
server.port=8081
```

### Issue: PCF Agent API not reachable

**Error**: "Connection refused: http://localhost:8000"

**Solution**:
1. Start PCF Agent API first:
   ```bash
   python scripts/run_api.py
   ```
2. Verify API is running:
   ```bash
   curl http://localhost:8000/api/health
   ```

### Issue: BPMN model not deployed

**Error**: "Unknown process definition key: Process_1_1_1"

**Solution**:
1. Verify BPMN file is in `src/main/resources/bpmn/`
2. Check application logs for deployment errors
3. Restart application
4. Verify in Cockpit: http://localhost:8080/camunda/app/cockpit/

### Issue: Service task fails

**Error**: "Agent execution failed"

**Solution**:
1. Check PCFAgentDelegate logs
2. Verify input variables are set correctly
3. Test agent directly via API:
   ```bash
   curl -X POST http://localhost:8000/api/pcf/1.1.1.1/execute \
     -H "Content-Type: application/json" \
     -d '{"input_data": {"market_segment": "Test"}}'
   ```
4. Check for required input parameters in BPMN model

### Issue: Variables not set

**Error**: "Variable 'competitors_list' not found"

**Solution**:
1. Check PCFAgentDelegate is correctly mapping output variables
2. Enable debug logging:
   ```properties
   logging.level.ai.superstandard.camunda.delegate=DEBUG
   ```
3. Review logs for variable setting errors
4. Verify agent returns expected result structure

---

## Production Deployment

### Checklist

- [ ] **Database**: Switch to PostgreSQL/MySQL
- [ ] **Security**: Change admin password
- [ ] **API URL**: Update `pcf.api.base-url` to production
- [ ] **Authentication**: Enable API authentication
- [ ] **Monitoring**: Set up logging and metrics
- [ ] **Load Balancing**: Deploy multiple Camunda instances
- [ ] **Backup**: Configure database backups
- [ ] **SSL/TLS**: Enable HTTPS

### Production Configuration

```properties
# Database
spring.datasource.url=jdbc:postgresql://db.production:5432/camunda
spring.datasource.username=${DB_USERNAME}
spring.datasource.password=${DB_PASSWORD}
spring.datasource.hikari.maximum-pool-size=20
spring.datasource.hikari.minimum-idle=5

# PCF API
pcf.api.base-url=https://api.superstandard.ai
pcf.api.timeout-seconds=600

# Security
camunda.bpm.admin-user.password=${ADMIN_PASSWORD}

# Logging
logging.level.root=WARN
logging.level.ai.superstandard=INFO

# Monitoring
management.endpoints.web.exposure.include=health,metrics,prometheus
```

### Docker Deployment

**Dockerfile**:
```dockerfile
FROM openjdk:17-jdk-slim

WORKDIR /app

COPY target/camunda-pcf-integration-1.0.0.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
```

**Build and run**:
```bash
# Build image
docker build -t camunda-pcf-integration .

# Run container
docker run -d \
  -p 8080:8080 \
  -e PCF_API_BASE_URL=http://api:8000 \
  -e DB_USERNAME=camunda \
  -e DB_PASSWORD=secret \
  --name camunda \
  camunda-pcf-integration
```

---

## Next Steps

1. **Test the integration**
   - Start PCF Agent API
   - Run Camunda application
   - Execute Process 1.1.1
   - View results in Cockpit

2. **Add more processes**
   - Copy additional BPMN models
   - Deploy and test

3. **Customize**
   - Modify application.properties
   - Add custom Java delegates
   - Integrate with existing systems

4. **Deploy to production**
   - Follow production checklist
   - Configure monitoring
   - Set up backups

---

## Support

- **Documentation**: API_INTEGRATION_GUIDE.md
- **Issues**: GitHub Issues
- **Email**: support@superstandard.ai

---

**Created**: 2025-11-12
**Version**: 1.0.0
**Camunda Version**: 7.20
**Java Version**: 17+
