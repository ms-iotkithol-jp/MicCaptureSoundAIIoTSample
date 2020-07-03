# Sound Data Composer Function 
![overview](../../../images/DataComposerFunction.PNG)

To run this sample, please setup following environment variables.  

- AzureWebJobsStorage
- IoTHubConnectionString
- StorageConnectionString

It is OK that you use same value for both 'AzureWebJobsStorage' and 'StorageConnectionString'.
The value of 'IoTHubConnectionString' should be your IoT Hub RBAC 'service role' connection string. 

You can use this sample with [Azure Sphere Sound Capture Sample](https://github.com/ms-iotkithol-jp/azure-sphere-thief-detector) as an application on sound capturing and sending device.

At the time to debug, please make local.settings.json in your folder and edit '<- ->' part by using your connection strings.

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "<- your storage connection string ->",
    "IoTHubConnectionString":"<- your azure iot hub service role connection string ->",
    "StorageConnectionString":"<- your storage connection string ->",
    "FUNCTIONS_WORKER_RUNTIME": "dotnet"
  }
}
```

At the time deploy and run this on your Azure Funtion environment, these settings are written in Azure Function's appliation settings.

## Necessary Blob Container and Folders  
This sample use 2 folders in your blob container. please make an Azure Storage Account and make a container. 

Then make following 2 folders which are used in Azure Function logic.  
- soundfragment
- sounddata

First one is the folder for each send divided sound binary data storing.
Second one is the folder for composed sound data file storing.
