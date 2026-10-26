# Business requirements
This is a hypothetical planning case. No real stakeholders were interviewed.

| ID | User need | Implemented evidence | Acceptance |
|---|---|---|---|
| BR1 | Trust sales history | Bronze metadata, Silver rejects, Gold totals | raw = accepted + rejected; units match |
| BR2 | Compare demand forecasts fairly | Three models, 3 chronological origins | same 14 targets per model and origin |
| BR3 | Review inventory exceptions | Explicit synthetic stock and capacity | each flag traceable to formula and scenario |
| BR4 | Export understandable analytics | Excel and BI-ready datasets | workbook controls match SQL; BI native review pending |
| BR5 | Trace results | Stable source row IDs, hashes, rule IDs | rejected row reasons and lineage documented |

Hypothetical planner owns replenishment decisions, analyst owns KPI definitions,
engineer owns data contracts. Escalate changing schemas to the data owner; escalate
negative stock or large forecast bias to the planner. High WAPE prevents automated
purchasing approval. Data-quality root causes are described without claiming real
customer dissatisfaction, business savings, or stakeholder satisfaction scores.
