# Soune Capture Module 
## Desired Properties 
When you try to capture sound only.  
```
  "properties.desired": {
    "capture-spec": {
      "record-chunk": 1024,
      "record-rate": 16000,
      "record-width": 2,
      "record-start-level": 1000,
      "record-duration-msec": 500,
      "capture-channels": "1,2,3,4",
      "capture-order": false
    }
  }
```
- record-chunk - byte size of data chunk
- record-rate  - sampling rate Hz
- record-width - byte size of record (default is int32)
- record-start-level - capture sound only when the volume exceeds the specified level 
- record-duration-msec - recording milli secconds for each file
- capture-channels - specify capture channels 
- capture-order - capturing only when this value is true.

---
When you want to capture sound and runt AI on Edge.
```
  "properties.desired": {
    "capture-spec": {
      "record-chunk": 1024,
      "record-rate": 16000,
      "record-width": 2,
      "record-start-level": 1000,
      "record-duration-msec": 500,
      "capture-channels": "1,2,3,4",
      "capture-order": false
    },
    "classify-on-edge": {
      "file-format": "csv,wav",
      "upload-to-cloud": false
    }
  }
```
- classify-on-edge - when this element exists, SoundClassficationService works
- file-format - specify file formats - required
- upload-to-cloud - when this value is true, not only classifier works but also upload file to cloud blob container - optional


