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

    "soundcapturemodule":{
      "properties.desired": {
        "capture-spec":{
          "record-chunk":1024,
          "record-rate":16000,
          "record-width":2,
          "record-start-level": 1000,
          "record-duration-msec":500,
          "capture-channels":"1,2,3,4",
          "capture-order": false,
          "classify-on-edge": true
        }
      }
と、classify-on-edge を true に設定することにより、Sound Capture Module が Blob on Edge にはキャプチャーしたサウンドデータをアップロードせずに、マウントされたサウンドデータ格納用フォルダー（SOUND_DATA_FOLDER）にCSVファイルを格納し、IoT Edge Runtime に "output_data_file" を通じて保存したことを通知する。  
<b>classify-on-edge</b> は、Module Twins の Desired Properties なので、当然のことながら、 Azure Portal からの指示も可能である。 

Sound Classifier Service へも、 Module Twins を使って、Azure Porta から、学習済みモデルとデータチャンクの値の更新を指示できる。 

      "properties.desired": {
          "record-chunk" : 1024,
          "model-file": {
              "name": "new-sound-classification-model.h5",
              "url": "https://blob...."
          }

<b>"model-file.url"</b> で指定された URL から h5 フォーマットのファイルをダウンロードし、name で指定された名前で保存し、学習済みモデルを更新する。以前に使っていた h5 ファイルはハードウェアリソース節約のため、削除される。 
指定する URL は、[Blob への SAS 作成](https://docs.microsoft.com/ja-jp/rest/api/storageservices/create-account-sas?redirectedfrom=MSDN)を参考に、Azure Storage の Blob Container に h5 ファイルを格納して、限定アクセス用のSASを作成して利用するなどが可能である。 
