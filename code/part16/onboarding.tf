module "team_onboarding" {
  source = "./modules/team-onboarding"
  
  team_name        = "team-data-science"
  tier             = "standard"
  gpu_quota        = 4
  cpu_quota        = "200"
  memory_quota     = "1Ti"
  
  mlflow_namespace  = "team-data-science"
  feast_project     = "team_data_science"
  
  approver_managers = ["manager@example.com"]
  approver_finops   = ["finops@example.com"]
}
