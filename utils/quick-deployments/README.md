# Let's try quick deployment and execute 
## Sound Capture Module only 
Edit storage account connection string in [deployment.capture-only.arm32v7.json](deployment.capture-only.arm32v7.json) for your own.  
Prepare your Azure IoT and Azure IoT Edge Device(Raspberry pi + ReSpeaker or equivalent HW set) according to [Microsoft Docs content](https://docs.microsoft.com/ja-jp/azure/iot-edge/how-to-deploy-modules-cli).  
Then execute follow command on Powershell. 
``` 
az iot edge set-modules --device-id [device id] --hub-name [hub name] --content deployment.capture-only.arm32v7.json
```