# Let's try quick deployment and execute 
## Sound Capture Module only 
Edit storage account connection string in [deployment.capture-only.arm32v7.json](deployment.capture-only.arm32v7.json) for your own.  
Prepare your Azure IoT and Azure IoT Edge Device(Raspberry pi + ReSpeaker or equivalent HW set) according to [Microsoft Docs content](https://docs.microsoft.com/ja-jp/azure/iot-edge/how-to-deploy-modules-cli).  
Then execute follow command on Powershell. 
``` 
az iot edge set-modules --device-id [device id] --hub-name [hub name] --content deployment.capture-only.arm32v7.json
```
---
## With Sound Classifer Service  
Edi storage account connection string and learned model in [deployment.with-classify.arm32v7.json](deployment.with-classify.arm32v7.json).
You can use following json description for learned model as a sample. 
```json
    "soundclassifierservice": {
      "properties.desired": {
        "model-file": {
            "url": "https://egstorageiotkitvol5.blob.core.windows.net/egsoundaioutput/sound-classification-csv-model.pkl.tar.gz",
            "name": "sound-classification-csv-model.pkl.tar.gz"
          },
        "data-def-file": {
            "url": "https://egstorageiotkitvol5.blob.core.windows.net/egsoundaioutput/sounddata-csv.yml",
            "name": "sounddata-csv.yml"
          }
      }
    }
```
