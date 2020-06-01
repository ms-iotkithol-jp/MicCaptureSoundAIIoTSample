# Cloud 側で学習した CNN モデルを使って、Edge 側で音の分類を行う

このステップでは以下の構成になるよう、Step 1 で作成した IoT Edge Solution に新たに Azure IoT Edge Module を追加する。  
※ [SoundIoTEdgeSolution](/SoundIoTEdgeSolution) には既にモジュールが組み込まれている状態です。 

![Basic Architecture](/images/SoundAIonEdgeBasicArchitecture.png) 

## Buld & Deploy 
[Step 1](./step1.md) を参照のこと。  
実際に Step 2 を実習して、独自の h5 ファイルが手元にある場合は、そのファイルを [/SoundIoTEdgeSolution/modules/SoundClassiferService/model](/SoundIoTEdgeSolution/modules/SoundClassiferService/model) の <b>sound-classification-model.h5</b> を上書きしてから、Build & Deploy を行えば、各自の学習結果を反映できる。

## Sound Classification Module 機能詳細 
Step 1 で Build & Deploy した SoundCaptureModule に Module Twins の Desired Properties で指定することにより、Blob on Edge Module へのアップロードではなく、SoundClassifierService に格納した CSV ファイルの名前を IoT Edge Runtime のメッセージバスを使って通知し、そのメッセージを受信した SoundClassifierService は組み込まれた学習済みの CNN モデルを使って分類を行い、結果を Azure IoT Hub（他のモジュールが受信することも可能） に送信する。
 

### 設定  
deployment.template.json での soundcapturemodule の Desired Properties の設定において、  

```
  "soundcapturemodule":{
    "properties.desired": {
      "capture-spec":{
        "record-chunk":1024,
        "record-rate":16000,
        "record-width":2,
        "record-start-level": 1000,
        "record-duration-msec":500,
        "capture-channels":"1,2,3,4",
        "capture-order": false
      },
      "classify-on-edge": {
          ...
        }
    }
  }
```
と、classify-on-edge を true に設定することにより、Sound Capture Module が Blob on Edge にはキャプチャーしたサウンドデータをアップロードせずに、SoundClassifierServiceにキャプチャーしたデータを通知し、学習済みのAIで分類する。  
<b>classify-on-edge</b> は、Module Twins の Desired Properties なので、当然のことながら、 Azure Portal からの指示も可能である。 
詳細は、[SoundIoTEdgeSolution/modules/SoundCaptureModule](SoundIoTEdgeSolution/modules/SoundCaptureModule)を参照のこと。

Sound Classifier Service へも、 Module Twins を使って、学習済みモデルとデータ設定の値の更新を指示できる。 
詳細は、[SoundIoTEdgeSolution/modules/SoundClassifierService](SoundIoTEdgeSolution/modules/SoundClassfierService)を参照のこと。
