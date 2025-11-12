package ai.superstandard.camunda.delegate;

import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Camunda Java Delegate for SuperStandard PCF Agent execution.
 *
 * Integrates Camunda BPMN service tasks with SuperStandard PCF Agent API.
 *
 * <h2>BPMN Configuration Example:</h2>
 * <pre>
 * &lt;bpmn:serviceTask id="Task_1_1_1_1"
 *                   name="Identify competitors"
 *                   camunda:asyncBefore="true"
 *                   camunda:delegateExpression="${pcfAgentDelegate}"&gt;
 *   &lt;bpmn:extensionElements&gt;
 *     &lt;camunda:inputOutput&gt;
 *       &lt;camunda:inputParameter name="hierarchy_id"&gt;1.1.1.1&lt;/camunda:inputParameter&gt;
 *       &lt;camunda:inputParameter name="market_segment"&gt;${market_segment}&lt;/camunda:inputParameter&gt;
 *       &lt;camunda:inputParameter name="geographic_scope"&gt;${geographic_scope}&lt;/camunda:inputParameter&gt;
 *     &lt;/camunda:inputOutput&gt;
 *   &lt;/bpmn:extensionElements&gt;
 * &lt;/bpmn:serviceTask&gt;
 * </pre>
 *
 * <h2>Application Properties:</h2>
 * <pre>
 * # SuperStandard PCF Agent API configuration
 * pcf.api.base-url=http://localhost:8000
 * pcf.api.timeout-seconds=300
 * pcf.api.track-kpis=true
 * pcf.api.delegate-to-children=true
 * </pre>
 *
 * <h2>Input Parameters:</h2>
 * <ul>
 *   <li><strong>hierarchy_id</strong> (required): PCF hierarchy ID (e.g., "1.1.1.1")</li>
 *   <li><strong>Any other parameters</strong>: Passed as input_data to agent</li>
 * </ul>
 *
 * <h2>Output Variables (set by delegate):</h2>
 * <ul>
 *   <li><strong>pcf_execution_id</strong>: Unique execution ID</li>
 *   <li><strong>pcf_success</strong>: Boolean indicating success</li>
 *   <li><strong>pcf_execution_time_ms</strong>: Execution time in milliseconds</li>
 *   <li><strong>pcf_kpis</strong>: Map of KPI measurements</li>
 *   <li><strong>Agent output fields</strong>: All top-level result fields as variables</li>
 * </ul>
 *
 * @author SuperStandard
 * @version 1.0.0
 * @since 2025-11-12
 */
@Component("pcfAgentDelegate")
public class PCFAgentDelegate implements JavaDelegate {

    private static final Logger logger = LoggerFactory.getLogger(PCFAgentDelegate.class);

    @Value("${pcf.api.base-url:http://localhost:8000}")
    private String apiBaseUrl;

    @Value("${pcf.api.timeout-seconds:300}")
    private int timeoutSeconds;

    @Value("${pcf.api.track-kpis:true}")
    private boolean trackKpis;

    @Value("${pcf.api.delegate-to-children:true}")
    private boolean delegateToChildren;

    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;

    /**
     * Constructor initializes HTTP client and JSON mapper.
     */
    public PCFAgentDelegate() {
        this.httpClient = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_2)
            .connectTimeout(Duration.ofSeconds(10))
            .build();

        this.objectMapper = new ObjectMapper();
        this.objectMapper.findAndRegisterModules(); // For Java 8 date/time support
    }

    /**
     * Execute the PCF agent.
     *
     * @param execution Camunda execution context
     * @throws Exception if agent execution fails
     */
    @Override
    public void execute(DelegateExecution execution) throws Exception {
        // 1. Get hierarchy ID from input parameter
        String hierarchyId = (String) execution.getVariable("hierarchy_id");
        if (hierarchyId == null || hierarchyId.trim().isEmpty()) {
            throw new IllegalArgumentException(
                "Required input parameter 'hierarchy_id' is missing or empty. " +
                "Add <camunda:inputParameter name=\"hierarchy_id\">1.1.1.1</camunda:inputParameter> " +
                "to your BPMN service task configuration."
            );
        }

        String processInstanceId = execution.getProcessInstanceId();
        String activityId = execution.getCurrentActivityId();

        logger.info(
            "PCF Agent Delegate starting: hierarchyId={}, processInstance={}, activity={}",
            hierarchyId, processInstanceId, activityId
        );

        try {
            // 2. Build input data from process variables
            Map<String, Object> inputData = extractInputData(execution);

            logger.debug("Input data for {}: {}", hierarchyId, inputData);

            // 3. Build request body
            Map<String, Object> requestBody = buildRequestBody(inputData, processInstanceId);

            String requestJson = objectMapper.writeValueAsString(requestBody);

            // 4. Call PCF Agent API
            String apiUrl = apiBaseUrl + "/api/pcf/" + hierarchyId + "/execute";

            logger.info("Calling PCF Agent API: {} (timeout={}s)", apiUrl, timeoutSeconds);

            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(apiUrl))
                .header("Content-Type", "application/json")
                .header("X-Camunda-Process-Instance-Id", processInstanceId)
                .header("X-Camunda-Activity-Id", activityId)
                .timeout(Duration.ofSeconds(timeoutSeconds))
                .POST(HttpRequest.BodyPublishers.ofString(requestJson))
                .build();

            long startTime = System.currentTimeMillis();

            HttpResponse<String> response = httpClient.send(
                request,
                HttpResponse.BodyHandlers.ofString()
            );

            long callDuration = System.currentTimeMillis() - startTime;

            // 5. Check response status
            if (response.statusCode() != 200) {
                String errorMessage = String.format(
                    "PCF Agent API returned error: HTTP %d - %s",
                    response.statusCode(),
                    response.body()
                );
                logger.error(errorMessage);
                throw new RuntimeException(errorMessage);
            }

            logger.info("PCF Agent API call completed in {}ms", callDuration);

            // 6. Parse response
            JsonNode responseJson = objectMapper.readTree(response.body());

            // 7. Check execution success
            boolean success = responseJson.get("success").asBoolean();
            if (!success) {
                String errorMsg = responseJson.has("error") ?
                    responseJson.get("error").asText() :
                    "Agent execution reported failure";

                logger.error("Agent execution failed: {}", errorMsg);
                throw new RuntimeException("PCF Agent execution failed: " + errorMsg);
            }

            // 8. Extract and set output variables
            setOutputVariables(execution, responseJson);

            // 9. Log success
            int executionTimeMs = responseJson.get("execution_time_ms").asInt();
            logger.info(
                "PCF Agent executed successfully: hierarchyId={}, executionTime={}ms, " +
                "totalCallTime={}ms, processInstance={}",
                hierarchyId, executionTimeMs, callDuration, processInstanceId
            );

        } catch (Exception e) {
            logger.error(
                "PCF Agent execution failed: hierarchyId={}, processInstance={}, error={}",
                hierarchyId, processInstanceId, e.getMessage(), e
            );

            // Set error variables
            execution.setVariable("pcf_error", e.getMessage());
            execution.setVariable("pcf_success", false);

            // Re-throw to fail the service task
            throw e;
        }
    }

    /**
     * Extract input data from process variables.
     *
     * Filters out Camunda internal variables and the hierarchy_id parameter.
     *
     * @param execution Camunda execution context
     * @return Map of input data for agent
     */
    private Map<String, Object> extractInputData(DelegateExecution execution) {
        Map<String, Object> allVariables = execution.getVariables();

        // Filter out internal/system variables
        return allVariables.entrySet().stream()
            .filter(entry -> !isSystemVariable(entry.getKey()))
            .collect(Collectors.toMap(
                Map.Entry::getKey,
                Map.Entry::getValue
            ));
    }

    /**
     * Check if variable name is a system/internal variable.
     *
     * @param variableName Variable name
     * @return true if system variable, false otherwise
     */
    private boolean isSystemVariable(String variableName) {
        // Exclude Camunda internal variables
        if (variableName.startsWith("camunda")) return true;

        // Exclude our input parameter
        if (variableName.equals("hierarchy_id")) return true;

        // Exclude our output variables (in case of retry)
        if (variableName.startsWith("pcf_")) return true;

        return false;
    }

    /**
     * Build request body for PCF Agent API.
     *
     * @param inputData Input data extracted from process variables
     * @param correlationId Correlation ID (process instance ID)
     * @return Request body map
     */
    private Map<String, Object> buildRequestBody(
        Map<String, Object> inputData,
        String correlationId
    ) {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("input_data", inputData);
        requestBody.put("delegate_to_children", delegateToChildren);
        requestBody.put("track_kpis", trackKpis);
        requestBody.put("timeout_seconds", timeoutSeconds);
        requestBody.put("async_execution", false); // Always sync for now
        requestBody.put("correlation_id", correlationId);

        return requestBody;
    }

    /**
     * Set output variables from API response.
     *
     * Extracts result data and metadata, setting them as process variables.
     *
     * @param execution Camunda execution context
     * @param responseJson API response JSON
     */
    private void setOutputVariables(DelegateExecution execution, JsonNode responseJson) {
        // Set metadata variables
        execution.setVariable("pcf_execution_id", responseJson.get("execution_id").asText());
        execution.setVariable("pcf_success", responseJson.get("success").asBoolean());
        execution.setVariable("pcf_execution_time_ms", responseJson.get("execution_time_ms").asInt());
        execution.setVariable("pcf_agent_name", responseJson.get("agent_name").asText());
        execution.setVariable("pcf_hierarchy_id", responseJson.get("hierarchy_id").asText());

        // Extract and set result data
        JsonNode result = responseJson.get("result");
        if (result != null && !result.isNull()) {
            result.fields().forEachRemaining(entry -> {
                String key = entry.getKey();
                try {
                    // Convert JSON to Java object
                    Object value = objectMapper.treeToValue(entry.getValue(), Object.class);
                    execution.setVariable(key, value);
                    logger.debug("Set output variable: {} = {}", key, value);
                } catch (Exception e) {
                    logger.warn("Failed to set variable {}: {}", key, e.getMessage());
                }
            });
        }

        // Store KPIs if tracked
        JsonNode kpis = responseJson.get("kpis");
        if (kpis != null && kpis.isArray() && kpis.size() > 0) {
            Map<String, Object> kpiMap = new HashMap<>();
            kpis.forEach(kpi -> {
                String name = kpi.get("name").asText();
                JsonNode valueNode = kpi.get("value");
                Object value = null;
                try {
                    value = objectMapper.treeToValue(valueNode, Object.class);
                } catch (Exception e) {
                    value = valueNode.asText();
                }
                kpiMap.put(name, value);
            });

            execution.setVariable("pcf_kpis", kpiMap);
            logger.info("Stored {} KPIs: {}", kpiMap.size(), kpiMap.keySet());
        }

        // Store full response for debugging (optional)
        if (logger.isDebugEnabled()) {
            try {
                execution.setVariable("pcf_full_response", objectMapper.writeValueAsString(responseJson));
            } catch (Exception e) {
                logger.warn("Failed to store full response: {}", e.getMessage());
            }
        }
    }
}
