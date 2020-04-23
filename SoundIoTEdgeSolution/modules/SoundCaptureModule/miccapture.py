import io
import sys
import time
import datetime
import asyncio
import pyaudio
import wave
import numpy as np
import os
from updaterbase import FileUpdaterBase

class MicCapture:
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.flagLock = asyncio.Lock()
        self.captureingFlag = 0

    def findReSpeakerDevice(self, mic_device_name, mic_num_of_device):
        self.mic_id = -1
        info = self.pa.get_host_api_info_by_index(0)
        nummics = info.get('deviceCount')
        for i in range(0, nummics):
            micInfo = self.pa.get_device_info_by_host_api_device_index(0, i)
            micName = micInfo.get('name')
            if micName.startswith(mic_device_name):
                self.mic_num_of_channel = micInfo['maxInputChannels']
                self.current_mic_spec = micInfo
                self.mic_num_of_device = mic_num_of_device
                self.mic_id = i
                break
        if self.mic_id == -1:
            print('Mic device[{}] has not been found'.format(mic_device_name))
        else:
            print('Mic device[{0}] device id is {1}'.format(mic_device_name, self.mic_id))
        
    def getCurrentMicSpec(self):
        return self.current_mic_spec

    async def startCapture(self,
            capture_channels,
            mic_device_chunk,
            mic_device_rate,
            mic_device_width,
            record_start_level, record_milliseconds,
            folder,
            stateChangeListener,
            fileUpdater:FileUpdaterBase):
        print('startCapture is called...')
        if self.mic_id == -1:
            print("mic device has not been found!")
            return
        if not os.path.exists(folder):
            os.mkdir(folder)
            print('Folder created - {}'.format(folder))

        lastCapturingFlag = -1
        await self.flagLock.acquire()
        try:
            lastCapturingFlag = self.captureingFlag
        finally:
            self.flagLock.release()
        if lastCapturingFlag > 0:
            print("Capturing has been started.")
            return

        self.mic_device_rate = mic_device_rate
        self.mic_device_width = mic_device_width
        self.mic_device_chunk = mic_device_chunk

        self.record_start_level = record_start_level
        self.record_milliseconds = record_milliseconds

        print('* recording - {}'.format(self.mic_id))
        numofmics = self.mic_num_of_device       # ReSpeaker depend 4
        numofchannels = self.mic_num_of_channel   # ReSpeaker depend 6
        lastCapturingFlag = -1
        await self.flagLock.acquire()
        try:
            self.captureingFlag = 1  # 1->checking record level, 2->recording, 0->end of this loop
            lastCapturingFlag =self.captureingFlag
        finally:
            self.flagLock.release()
        print('Start capturing in loop...')
        while lastCapturingFlag >= 1:
            stream = self.pa.open(
                rate=self.mic_device_rate,
                format=self.pa.get_format_from_width(self.mic_device_width),
                channels=self.mic_num_of_channel,
                input=True,
                input_device_index=self.mic_id,)
            frames = []
            dframes = []
            for i in range(0,len(capture_channels)):
                frames.append([])
                dframes.append([])
            soundFileNameBase = ''
            now = datetime.datetime.now()
            soundFileNameBase = 'sound-{0:%Y%m%d%H%M%S%f}'.format(now)
            for i in range(0, int(self.mic_device_rate / self.mic_device_chunk * self.record_milliseconds / 1000.0)):
                try:
                    data = stream.read(self.mic_device_chunk)
                    atemp =[]
                    higherLevelDatas = 0
                    for j in capture_channels:
                        a = np.fromstring(data,dtype=np.int16)[j::numofchannels]
                        atemp.append(a)
                        includingHighLevels = np.any(abs(a)>self.record_start_level)
                        if includingHighLevels:
                            higherLevelDatas += 1
                    if higherLevelDatas > 0:
                        if lastCapturingFlag==1:
                            lastCapturingFlag = 2
                            print('capturing started...')
                            if stateChangeListener:
                                stateChangeListener.stateUpdated('start-capturing',now)
                    else:
                        if lastCapturingFlag == 2:
                            lastCapturingFlag = 3
                            print('capturing to be ended...')

                    if (lastCapturingFlag==2):
                        for j in range(0, len(capture_channels)):
                            frames[j].append(atemp[j].tostring())
                            dframes[j].extend(atemp[j])
                    if (lastCapturingFlag==2 or lastCapturingFlag==3):
                        dframesT = np.array(dframes).T.tolist()
                        if len(dframesT) > 0:
                            wav_filename = '{0}/{1}.wav'.format(folder, soundFileNameBase )
                            wf = wave.open( wav_filename, 'wb')
                            wf.setnchannels(len(capture_channels))
                            wf.setsampwidth(self.pa.get_sample_size(self.pa.get_format_from_width(self.mic_device_width)))
                            wf.setframerate(self.mic_device_rate)
                            for frame in frames:
                                wf.writeframes(b''.join(frame))
#                            wf.writeframes(b''.join(frames[1]))
                            wf.close()
                            print('saved - {0}'.format(wav_filename))

                            csv_filename = '{0}/{1}.csv'.format(folder, soundFileNameBase)
                            csv = open(csv_filename, 'w')
                            colNams = ''
                            for micIndex in capture_channels:
                                if (len(colNams)>0):
                                    colNams += ','
                                colNams += 'mic{}'.format(micIndex)
                            colNams += '\n'
                            csv.writelines([colNams])
                            for d in dframesT:
                                raw = ''
                                for i in range(0,numofmics):
                                    if i>0:
                                        raw+=','
                                    raw+='{}'.format(d[i])
                                csv.writelines([raw+'\n'])
                            csv.close()
                            print('saved - {0}'.format(csv_filename))
                            if fileUpdater:
                                await fileUpdater.uploadFile(wav_filename)
                                await fileUpdater.uploadFile(csv_filename)
                                os.remove(wav_filename)
                                os.remove(csv_filename)
                except Exception as e:
                    print('Exception during capture sound. - {}'.format(e))

                if lastCapturingFlag==3:
                    lastCapturingFlag = 1
                    if stateChangeListener:
                        stateChangeListener.stateUpdated('end-capturing',datetime.datetime.now())
                    print('capture stopped and waiting...')
            
            stream.close()
            await self.flagLock.acquire()
            try:
                if (self.captureingFlag==0):
                    lastCapturingFlag =self.captureingFlag
            finally:
                self.flagLock.release()

        print("Sound Capture has been finished")

    async def stopCapture(self):
        await self.flagLock.acquire()
        try:
            self.captureingFlag = 0
            print('Sound Capture will be stopped...')
        finally:
            self.flagLock.release()

# define behavior for halting the application
async def stdin_listener():
    while True:
        try:
            selection = input("Press Q to quit\n")
            if selection == "Q" or selection == "q":
                await micCapture.stopCapture()
                print("Quitting...")
                break
        except:
            time.sleep(10)

async def main(micCapture):
    capturing = asyncio.gather(micCapture.startCapture(
        capture_channels= [1,2,3,4],
        mic_device_rate=16000,
        mic_device_width= 2,
        mic_device_chunk=1024,
        record_start_level = 1000,
        record_milliseconds=500,
        folder= 'data',stateChangeListener=None,fileUpdater=None))

    loop = asyncio.get_event_loop()
    user_finished = loop.run_in_executor(None,stdin_listener)
    await user_finished
    capturing.cancel()

    loop.close()

if __name__ == '__main__':
    # ReSpeaker mic_num_of_device is 4, mic_num_of_channel is 6
    micCapture = MicCapture()
    micCapture.findReSpeakerDevice('ReSpeaker 4 Mic Array',4)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(micCapture))
    loop.close()
