# Enterprise Application UI and Functionality Issues

**Confluence URL:** https://agnishpaul2002.atlassian.net/wiki/spaces/SELFHELP/pages/1343750
**Page ID:** 1343750

## Content

### Overview
This article provides diagnostic procedures and escalation guidelines for Enterprise Application functionality issues, such as product dropdowns not populating, invoice checkboxes not getting ticked, form submission errors, and portal rendering defects.

### Common Symptoms & Diagnostics
1. **Dropdown Not Showing Products**:
   - Newly requested or unconfigured products (such as 4K Webcam Pro or peripheral accessories) do not appear in the invoice or procurement dropdown.
   - Root Cause: Product is disabled in master catalog configuration (`backend/catalog_config.json`) or catalog synchronization is pending.
   - Resolution: Must be enabled in master catalog configuration (`show_in_invoice_dropdown: true`) by Support Engineering. Client-side browser refresh or cache clear will not resolve this.

2. **Invoice Checkbox Not Getting Ticked**:
   - Checkbox controls (e.g., compliance confirmation, bulk selection, invoice certification) do not respond to clicks or fail to toggle state.
   - Root Cause: Frontend UI event-handling defect or form validation state locking in `employee_portal.html`.
   - Resolution: Requires frontend code patch by Support Engineering.

3. **Application Crashes & Un-operational Functionality**:
   - Calculation errors (such as Currency Tax Aggregation crash) or non-operational workflow buttons.
   - Root Cause: Backend API calculation error or missing database normalization schema.
   - SLA & Timeline: See SOP-ENG-004 for multi-file architectural defect estimation.

### Escalation Protocol
- When an employee reports an application-level defect or un-operational functionality:
  1. The Self Help Agent scans Confluence knowledge base articles.
  2. The agent explains with empathy that this is an enterprise application defect that cannot be fixed through client-side settings.
  3. The issue is escalated to Level 2 Support Engineer Alex Turner.
  4. The escalation attaches the live conversation chat link so the engineer can review the context and chat with the employee.
  5. Remote desktop access (MeshCentral) is NOT required for enterprise application bugs.
  6. The Support Engineer asks the Code Analysis Agent to investigate the application GitHub repository, apply the code change, and execute the CI/CD pipeline for deployment to AWS ECS Fargate.

