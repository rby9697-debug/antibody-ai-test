# Project health rule matrix

| Scenario | Missing required master fields | Expired samples | Milestone complete + empty actual_finish | Expected status | Expected issue types |
|---|---:|---:|---:|---|---|
| Healthy project | No | No | No | ok | none |
| Master fields missing | Yes | No | No | warning | missing_master_fields |
| Expired samples only | No | Yes | No | warning | expired_samples |
| Milestone mismatch only | No | No | Yes | error | milestone_completion_mismatch |
| Warning + error mixed | Yes | Yes | Yes | error | missing_master_fields, expired_samples, milestone_completion_mismatch |
