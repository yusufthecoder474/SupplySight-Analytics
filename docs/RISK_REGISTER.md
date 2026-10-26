# Risk register
Hypothetical owners describe roles, not real named stakeholders.

| Risk | Impact | Mitigation / escalation |
|---|---|---|
| Retail sales substituted for manufacturing demand | external validity low | label proxy; planner must supply real factory demand |
| Zero-filled absent transactions hide censored demand | underforecast | label zero policy; request availability/closure history |
| Duplicate lines may be legitimate | demand undercount | preserve rejected rows; data-owner review before changing policy |
| High error / negative forecast bias | unsafe ordering | manual planning only; review product errors and additional history |
| Synthetic lead and stock assumptions | flags have no operational validity | maintain separate planning_source; planner replaces with observed data |
| Independent normal safety-stock approximation | service level not assured | calibrate variability and lead-time distribution |
| Single per-product capacity | shared resource bottlenecks ignored | no factory-utilization claim |
| Desktop applications unavailable | native report validation incomplete | exact local build and acceptance instructions |
| Output overwrite/concurrent run | partial files | dedicated root, single writer; preserve release ZIP |
| Customer IDs in public raw data | unnecessary identity distribution | no customer analytics; review licensed source before publishing |
