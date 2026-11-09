import deepspeed

model, optimizer, _, _ = deepspeed.initialize(
    args=args, model=model, model_parameters=model.parameters()
)
for step in range(MAX_STEPS):
    loss = train_step(model)
    model.backward(loss)
    model.step()
    if step % 100 == 0:
        model.save_checkpoint(save_dir, tag=f"step-{step}")
