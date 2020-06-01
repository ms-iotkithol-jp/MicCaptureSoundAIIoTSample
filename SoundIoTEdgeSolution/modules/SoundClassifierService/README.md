# Sound Classifier Service IoT Edge Module 

This module use deliverables from [Sound AI Tutorial](../../../SoundAI/notebook).  
When you want to use your own sound data and learned model, please update following files by using them before you start to build this module.

- try [ai-sound-major-miner-classification-part1.ipynb](../../../SOundAI/notebook/ai-sound-major-miner-classification-part1.ipynb)(CSV format - Raspberry Pi) or [ai-sound-major-miner-classification-part1-wav.ipynb](../../../SoundAI/notebook/ai-sound-major-miner-classification-part1-wav.ipynb)(WAV format)
- model/sound-classfication-<b><i>format</i></b>-model.pkl or h5
- sounddata-<b><i>format</i></b>.yml 
- loadwavsounds.py(WAV format) or loadsounds.py(CSV format)  
※ <i>format</i> is <b>csv</b> or <b>wav</b>


When you want to try this just now, you can try current file set as is.
- [sound-classification-wav-model.h5](https://egstorageiotkitvol5.blob.core.windows.net/egsoundaioutput/sound-classification-wav-model.h5)
- [sound-classification-csv-model.pkl.tar.gz](https://egstorageiotkitvol5.blob.core.windows.net/egsoundaioutput/sound-classification-csv-model.pkl.tar.gz)
- [sounddata-wav.yml](https://egstorageiotkitvol5.blob.core.windows.net/egsoundaioutput/sounddata-wav.yml)
- [https://egstorageiotkitvol5.blob.core.windows.net/egsoundaioutput/sounddata-csv.yml](https://egstorageiotkitvol5.blob.core.windows.net/egsoundaioutput/sounddata-csv.yml)
- [loadwavsounds.py](./loadwavsounds.py)
- [loadsounds.py](./loadsounds.py)

## Desired Properties  
```
  "properties.desired": {
    "model-file": {
      "url": "< your learned model url >",
      "name": "< your learned model file name >"
    },
    "data-def-file": {
      "url": "< your data define file url >",
      "name": "< > your data define file name >"
    }
  }
```
Please set url and name values in [deployment.with-classify.arm32v7.json](../../../utils/quick-deployments/deployment.with-classify.arm32v7.json) or on Azure Portal using above learned model and sound-data-csv|wav.yml.

Example:  
```
  "properties.desired": {
    "model-file": {
      "url": "https://egstorageiotkitvol5.blob.core.windows.net/egsoundaioutput/sound-classification-csv-model.pkl.tar.gz",
      "name": "sound-classification-csv.model.pkl"
    },
    "data-def-file": {
      "url": "https://egstorageiotkitvol5.blob.core.windows.net/egsoundaioutput/sounddata-csv.yml",
      "name": "sounddata-csv.yml"
    }
  }
```
