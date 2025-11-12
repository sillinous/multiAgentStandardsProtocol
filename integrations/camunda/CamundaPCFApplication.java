package ai.superstandard.camunda;

import org.camunda.bpm.spring.boot.starter.annotation.EnableProcessApplication;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * SuperStandard PCF Camunda Integration Application.
 *
 * This Spring Boot application integrates Camunda BPM with the SuperStandard
 * PCF Agent API, enabling execution of APQC PCF business processes through
 * Camunda's workflow engine.
 *
 * <h2>Features:</h2>
 * <ul>
 *   <li>Camunda BPM 7.20+ with embedded engine</li>
 *   <li>Camunda Web Apps (Cockpit, Tasklist, Admin)</li>
 *   <li>Camunda REST API</li>
 *   <li>PCF Agent Delegate for service task execution</li>
 *   <li>Auto-deployment of BPMN models</li>
 *   <li>H2 database for development (configurable for production)</li>
 * </ul>
 *
 * <h2>Getting Started:</h2>
 * <pre>
 * # 1. Build the application
 * mvn clean package
 *
 * # 2. Start SuperStandard PCF Agent API
 * python scripts/run_api.py
 *
 * # 3. Run this application
 * java -jar target/camunda-pcf-integration-1.0.0.jar
 *
 * # 4. Access Camunda Cockpit
 * http://localhost:8080
 * Username: admin
 * Password: admin
 * </pre>
 *
 * <h2>Deploying BPMN Models:</h2>
 * <p>
 * Place BPMN files in <code>src/main/resources/bpmn/</code> and they will be
 * automatically deployed on application startup.
 * </p>
 *
 * <p>
 * Example: Copy <code>process_1_1_1_assess_external_environment.bpmn</code>
 * to <code>src/main/resources/bpmn/</code>
 * </p>
 *
 * <h2>Starting a Process Instance:</h2>
 * <pre>
 * # Via Camunda REST API
 * curl -X POST http://localhost:8080/engine-rest/process-definition/key/Process_1_1_1/start \
 *   -H "Content-Type: application/json" \
 *   -d '{
 *     "variables": {
 *       "market_segment": {"value": "Cloud Infrastructure", "type": "String"},
 *       "geographic_scope": {"value": "North America", "type": "String"}
 *     }
 *   }'
 * </pre>
 *
 * <h2>Monitoring Execution:</h2>
 * <ul>
 *   <li><strong>Cockpit</strong>: http://localhost:8080/camunda/app/cockpit/</li>
 *   <li><strong>Tasklist</strong>: http://localhost:8080/camunda/app/tasklist/</li>
 *   <li><strong>Admin</strong>: http://localhost:8080/camunda/app/admin/</li>
 *   <li><strong>REST API</strong>: http://localhost:8080/engine-rest/</li>
 *   <li><strong>H2 Console</strong>: http://localhost:8080/h2-console</li>
 * </ul>
 *
 * <h2>Configuration:</h2>
 * <p>
 * Edit <code>application.properties</code> to configure:
 * </p>
 * <ul>
 *   <li>Database connection</li>
 *   <li>PCF Agent API URL</li>
 *   <li>Camunda admin credentials</li>
 *   <li>Job executor settings</li>
 *   <li>Logging levels</li>
 * </ul>
 *
 * @author SuperStandard
 * @version 1.0.0
 * @since 2025-11-12
 */
@SpringBootApplication
@EnableProcessApplication
public class CamundaPCFApplication {

    /**
     * Main entry point for the application.
     *
     * @param args Command-line arguments
     */
    public static void main(String[] args) {
        SpringApplication.run(CamundaPCFApplication.class, args);

        System.out.println("\n" + "=".repeat(80));
        System.out.println("SuperStandard PCF Camunda Integration Started");
        System.out.println("=".repeat(80));
        System.out.println("\nCamunda Web Apps:");
        System.out.println("  - Cockpit:  http://localhost:8080/camunda/app/cockpit/");
        System.out.println("  - Tasklist: http://localhost:8080/camunda/app/tasklist/");
        System.out.println("  - Admin:    http://localhost:8080/camunda/app/admin/");
        System.out.println("\nREST API:");
        System.out.println("  - Camunda:  http://localhost:8080/engine-rest/");
        System.out.println("\nCredentials:");
        System.out.println("  - Username: admin");
        System.out.println("  - Password: admin");
        System.out.println("\nDevelopment Tools:");
        System.out.println("  - H2 Console: http://localhost:8080/h2-console");
        System.out.println("    JDBC URL: jdbc:h2:mem:camunda");
        System.out.println("\n" + "=".repeat(80));
        System.out.println();
    }
}
