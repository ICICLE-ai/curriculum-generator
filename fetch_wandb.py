import wandb
api = wandb.Api()
run = api.run("/jassehxia-the-ohio-state-university/skin-cancer-diagnostics/runs/3pbsi5ha")

print(run.history())