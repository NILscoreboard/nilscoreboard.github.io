# Schema
schools.json: {generated, schools:[{slug,name,conference,state,unitid(IPEDS/EADA),eada_institution_name,control(Public|Private),metrics:{<metric>:{value(int USD|null),fiscal_year,source,source_url,as_of(date accessed),confidence(Audited|Official filing|Reported|Estimate|null)}}}]}
Metrics: eada_total_revenue/expenses (GRND_TOTAL_*), eada_football_revenue/expenses (TOTAL_REVENUE_ALL_Football/TOTAL_EXPENSE_ALL_Football), eada_mbb_revenue/expenses (REV_MEN_Bskball/EXP_MEN_Bskball), kn_total_revenue/kn_total_expenses/kn_contributions (null: license), mfrs_contributions, revenue_share_budget_fy26 (null until records arrive).
schools.csv: flat, one row per school, value + <metric>_confidence columns. values_long.csv: one row per school x metric with provenance.
