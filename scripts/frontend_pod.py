import requests

url = "https://icicleai.tapis.io/v3/pods"
headers = {
    "X-Tapis-Token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IlBiZU5IU3lJVGtZRHctOWtnbjRZU21VSnk2ZVRYZTNEYWFMRDNBZnl0SDQiLCJ0eXAiOiJKV1QifQ.eyJqdGkiOiJiMTVhYTc0Ni04ZmI4LTRmZmEtODFiMi05OGU3NDI1OTk0YzQiLCJpc3MiOiJodHRwczovL2ljaWNsZWFpLnRhcGlzLmlvL3YzL3Rva2VucyIsInN1YiI6InNlaC4xQG9zdS5lZHVAaWNpY2xlYWkiLCJ0YXBpcy90ZW5hbnRfaWQiOiJpY2ljbGVhaSIsInRhcGlzL3Rva2VuX3R5cGUiOiJhY2Nlc3MiLCJ0YXBpcy9kZWxlZ2F0aW9uIjpmYWxzZSwidGFwaXMvZGVsZWdhdGlvbl9zdWIiOm51bGwsInRhcGlzL3VzZXJuYW1lIjoic2VoLjFAb3N1LmVkdSIsInRhcGlzL2FjY291bnRfdHlwZSI6InVzZXIiLCJleHAiOjE3ODY5MzQ4MjUsInRhcGlzL2NsaWVudF9pZCI6InRhcGlzdWktaW1wbGljaXQtY2xpZW50IiwidGFwaXMvZ3JhbnRfdHlwZSI6ImltcGxpY2l0IiwidGFwaXMvaWRwX2lkIjoiZ2xvYnVzIn0.L_su4ssd92c00ilVTkfuaRwSTa9RnMVFtOSru3KzWMVKvgChd8siSzNiRgrYh00XxVOp3RcEiI3aXkkK-yKCgvxqLzfVKGPy5OMjISyAmyVsHdW41IYNbrKWqcGOyDQtQj323QvCnzwQx57xCsUqll6_QdPX90ozZQm49O1TffV7B9cWEP3BlBUimSlzOKPA-tqtfVSPhGr85kSPaOFDb6Qe8C8MjJ6s4OYRZsydkMW6TESOCJa6tIbXvadpyQe3zcN8h8xtYCSLl0MhpYOmJe-tM3N0DbA5vIfbMaTJ1W19HHxuWkTvbEs_qdd01xB4zpWckS7fgNDuteWLeNnjmA",
    "Content-Type": "application/json"
}

payload = {
    "pod_id": "digitalagedu",
    "image": "nginx",
    "description": "DigitalAgEdu Curriculum Generator Web Portal",
    "volume_mounts": {
        "/usr/share/nginx/html": {
            "type": "tapisvolume",
            "source_id": "digitalagedustorage",
            "sub_path": "dist",
            "read_only": False
        }
    },
    "networking": {
        "default": {
            "protocol": "http",
            "port": 80
        }
    },
    "resources": {
        "cpu_request": 250,
        "cpu_limit": 1000,
        "mem_request": 256,
        "mem_limit": 1024
    }
}

response = requests.post(url, json=payload, headers=headers)
print("Status Code:", response.status_code)
print("Response:", response.json())