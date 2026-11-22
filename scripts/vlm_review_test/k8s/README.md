# Slide-review test on NRP Kubernetes

Same test as the Expanse `vlm_test` Tapis job (same image, V100 only, `vllm<0.19`, fp16, Qwen3-VL-8B); only the
queue differs. Push first: the job pulls `jassehxia/digital-age-edu:latest`. Set `NS` to your namespace.

```bash
NS=<your-namespace>

# Once: the volume, then the 50 screenshots onto it
kubectl -n $NS apply -f scripts/vlm_review_test/k8s/pvc.yaml
kubectl -n $NS apply -f scripts/vlm_review_test/k8s/access-pod.yaml
kubectl -n $NS wait --for=condition=Ready pod/scd-vlm-access --timeout=300s
kubectl -n $NS cp outputs/vlm_review_test/shots scd-vlm-access:/data/shots
kubectl -n $NS delete pod scd-vlm-access

# Each run (delete the previous Job first: Job names are unique)
kubectl -n $NS delete job scd-vlm-review-test --ignore-not-found
kubectl -n $NS apply -f scripts/vlm_review_test/k8s/job.yaml
kubectl -n $NS logs -f job/scd-vlm-review-test

# Results: /data/results/<timestamp>/ (summary.md, results.json, vllm_server.log)
kubectl -n $NS apply -f scripts/vlm_review_test/k8s/access-pod.yaml
kubectl -n $NS wait --for=condition=Ready pod/scd-vlm-access --timeout=300s
kubectl -n $NS exec scd-vlm-access -- ls /data/results
kubectl -n $NS cp scd-vlm-access:/data/results/<timestamp> outputs/vlm_review_test/nrp_<timestamp>
kubectl -n $NS delete pod scd-vlm-access
```

The first run installs vLLM and downloads the model onto the volume (~25 min, as on Expanse); later runs reuse them.
If the job stays Pending, `kubectl -n $NS describe pod -l job-name=scd-vlm-review-test` says why (often no free V100).
