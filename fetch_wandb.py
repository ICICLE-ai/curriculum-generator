import wandb
api = wandb.Api()
run = api.run("/jassehxia-the-ohio-state-university/skin-cancer-diagnostics/runs/uue24jc7")

print(run.history())