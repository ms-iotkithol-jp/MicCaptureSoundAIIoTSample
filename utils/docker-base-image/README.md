# Base Docker image for Azure IoT Edge based AI on Edge module

## For Raspbain  
[https://hub.docker.com/repository/docker/embeddedgeorge/tf2.1.0-raspbian](https://hub.docker.com/repository/docker/embeddedgeorge/tf2.1.0-raspbian) 

### How to build

```
sudo docker build -t tf2.1.0-raspbian -f Docker.tf2.1.0-raspbian .
```
Need more than 16 GB micro SD card (but 32GB is recomennded size)  
Build work is available both Windows and Raspbian 

### Test 
```
sudo docker create --name soundml -it embeddedgeorge/tf2.1.0-raspbian:stretch bash
sudo docker start -ia soundml
```
```
mkdir /app
exit
```
#### Test by using WAV format
```
sudo docker cp ./fender-sound-20200209170603399214.wav soundml:/app
sudo docker cp ./loadwavsounds.py  soundml:/app
sudo docker cp ./test-wav.py soundml:/app
sudo docker cp ./classify.py soundml:/app
sudo docker cp ./sounddata-wav.yml soundml:/app
sudo docker cp ./sound-classification-model.h5 soundml:/app 
sudo docker start -ia soundml
```
```
cd /app
python3 test-wav.py
```
#### Test by using CSV format (Optional)  
※ Current H5 model is trained by wav format so please change it when you want try by CSV format.
```
sudo docker cp ./cherry-sound-20200218113643319806.csv soundml:/app
sudo docker cp ./loadsounds.py  soundml:/app
sudo docker cp ./test-csv.py soundml:/app
sudo docker cp ./sounddata-csv.yml soundml:/app
sudo docker cp ./sound-classification-model.h5 soundml:/app 
sudo docker start -ia soundml
```
```
cd /app
python3 test-csv.py
```


---
## For Nvidia Jetoson Nano 
[https://hub.docker.com/repository/docker/embeddedgeorge/tf2.1.0-jetson](https://hub.docker.com/repository/docker/embeddedgeorge/tf2.1.0-jetson) 

### How to build

```
sudo docker build -t tf-jetson -f Docker.tf-jetson .
```
Need more than 32GB micro SD card  
Build work is available on Ubuntu/Arm64 only

### Test 
```
sudo docker create -v /usr/local/cuda-10.0:/usr/local/cuda-10.0 -v /usr/lib/aarch64-linux-gnu/tegra:/usr/lib/aarch64-linux-gnu/tegra -v /usr/lib/aarch64-linux-gnu/libcudnn.so.7.6.3:/usr/lib/aarch64-linux-gnu/libcudnn.so.7.6.3 -v /usr/lib/aarch64-linux-gnu/libcudnn.so.7:/usr/lib/aarch64-linux-gnu/libcudnn.so.7  --device=/dev/nvmap  --device=/dev/nvhost-ctrl  --device=/dev/nvhost-ctrl-gpu --name soundml -it embeddedgeorge/tf2.1.0-jetson:arm64-ubuntu18.04 bash
sudo docker start -ia soundml
```
```
mkdir /app
exit
```

#### Test by using WAV format
```
sudo docker cp ./fender-sound-20200209170603399214.wav soundml:/app
sudo docker cp ./loadwavsounds.py  soundml:/app
sudo docker cp ./classify.py soundml:/app
sudo docker cp ./test-wav.py soundml:/app
sudo docker cp ./sounddata-wav.yml soundml:/app
sudo docker cp ./sound-classification-model.h5 soundml:/app 
sudo docker start -ia soundml
```
```
cd /app
python3 test-wav.py
```
#### Test by using CSV format (Optional)  
※ Current H5 model is trained by wav format so please change it when you want try by CSV format.
```
sudo docker cp ./cherry-sound-20200218113643319806.csv soundml:/app
sudo docker cp ./loadsounds.py  soundml:/app
sudo docker cp ./test-csv.py soundml:/app
sudo docker cp ./sounddata-csv.yml soundml:/app
sudo docker cp ./sound-classification-model.h5 soundml:/app 
sudo docker start -ia soundml
```
```
cd /app
python3 test-csv.py
```
