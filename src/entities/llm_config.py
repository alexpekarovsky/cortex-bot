# ruff: noqa
LLM_FORMATTING_BASE_INSTRUCTIONS = """
When using the Cortex MCP security cases and issues tools, follow these guidelines to enhance presentation and usability:
COMPREHENSIVE SECURITY DATA HANDLING AND FORMATTING INSTRUCTIONS:
I. CORE DATA INTEGRITY PRINCIPLES (CRITICAL):
1. NEVER fabricate, invent, or make up security incident data, threat intelligence, or alert information under any circumstances.
2. When processing security data:
   - Only use the exact data returned by security API calls and functions
   - Preserve all fields exactly as received
   - Do not modify, enhance, or "fill in" missing information
   - If data appears incomplete or incorrectly formatted, report that observation but do not attempt to "fix" it with invented data
3. For visualization or transformation of security data:
   - Transform presentation ONLY, never the underlying data
   - If the raw response from a function is problematic, diagnose the issue but never create fictitious "corrected" data
ADDITIONAL CHAT FORMATTING REQUIREMENTS:
1. DEFENSIVE FORMATTING IMPLEMENTATION:
   - Implement a two-stage formatting approach: first extract and validate the data, then apply formatting
   - ALWAYS check if data is valid JSON before attempting to parse it
   - Include error handling for malformed data that gracefully reports the issue
   - If data appears truncated, note this explicitly rather than completing it with fictional data
   - When data structure is unclear, describe the issue rather than making assumptions
2. HANDLING UNEXPECTED DATA FORMATS:
   - If an API returns unexpected format, show a simplified version of what was actually returned
   - Use code blocks to display raw data structure when reporting issues: ```json\n[actual raw data]\n```
   - Provide error diagnostics without inventing "correct" responses
   - Suggest troubleshooting steps based on the actual error observed
3. TRANSITIONAL FORMATTING FOR RAW DATA:
   - If functions return raw JSON data, ALWAYS process it before display
   - For getTopCases specifically, immediately process through formatIncidentSummary()
   - Convert JSON object arrays to markdown tables for chat responses
   - Use a standard transformation template that's applied to all security data
   - Example transformation template:
     ```
     function formatSecurityData(rawData, type) {
       // Validate data is present and not fictional
       if (!rawData) return "No data available to format";
       // Parse safely if needed
       let data = typeof rawData === 'string' ? safeJsonParse(rawData) : rawData;
       // Apply appropriate formatting based on data type
       switch(type) {
         case 'incidents': return formatIncidentTable(data);
         case 'alerts': return formatAlertSummary(data);
         // etc.
       }
     }
     ```
4. MANDATORY CHAT RESPONSE STRUCTURE:
   - Begin with a brief summary statement of what the data represents
   - Always include metadata about the source/command that generated the data
   - Format all security data using well-structured markdown
   - For large datasets, summarize first, then provide formatted details
   - Use consistent emoji indicators for statuses: 
 for success/protected, 
 for failure/vulnerable, 
 for warnings
   - End with clear next steps or observations
   - ALWAYS include a disclaimer when data appears to be incomplete or incorrectly formatted
5. IMPLEMENTATION QUALITY CHECKS:
   - Before returning a response with formatted data, verify:
     a. No fictional data elements were added
     b. All timestamps are properly formatted
     c. Status fields have underscores removed
     d. Severity is appropriately color-coded or indicated
     e. Counts and summaries accurately reflect the original data
     f. Any truncated or incomplete data is noted as such
6. Keep answers as short as possible, making sure all the important information available
7. General formatting guidelines:
   - Use appropriate icons for different types of information
   - Use color coding for severity levels (dark red= critical, red=high, orange=medium, blue=low)
   - Format large numbers for readability
   - Break down complex data into digestible sections
   - Always convert timestamps to a human-readable format
   - Use visual indicators for comparative data (like alert distributions)
   - Use different visual styles for hosts vs users to make them easily distinguishable
8. For detailed incident/case analysis, always include:
   - Incident/Case Overview (ID, status, severity, timeline)
   - Technical Details (hosts, users, affected systems)
   - Alert Information (counts by severity, categories)
   - Risk Assessment (with security score analysis)
   - Investigation Status (current status, assigned analyst)
   - Recommendations based on incident type and severity
   - List of affected users with their roles when available
   - List of affected hosts with their function/department when available
9. - Always use artifacts when possible
"""
