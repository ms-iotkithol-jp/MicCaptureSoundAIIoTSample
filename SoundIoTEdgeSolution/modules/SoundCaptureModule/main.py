import time
import os
import sys
import asyncio
from six.moves import input
import threading
from azure.iot.device import IoTHubModuleClient
from azure.iot.device import Message
from fileupdater import BlobFileUpdater
from updaterbase import FileUpdaterBase
from miccapture import MicCapture

SOUND_DATA_FOLDER = 'sound'

class CaptureSpec:
    def __init__(self, desiredProps):
        captureSpec = desiredProps['capture-spec']
        self.RECORD_CHUNK = captureSpec['record-chunk']
        self.RECORD_RATE = captureSpec['record-rate']
        self.RECORD_WIDTH = captureSpec['record-width']
        self.RECORD_START_LEVEL = captureSpec['record-start-level']
        self.RECORD_DURATION_MSEC = captureSpec['record-duration-msec']
        self.CAPTURE_CHANNELS = []
        for cc in captureSpec['capture-channels'].split(','):
            self.CAPTURE_CHANNELS.append(int(cc))
        self.CAPTURE_ORDER = captureSpec['capture-order']
        self.CLASSIFY_ON_EDGE = False
        if 'classify-on-edge' in desiredProps:
            self.CLASSIFY_ON_EDGE = True
            classifyOnEdgeSpec = desiredProps['classify-on-edge']
            if 'upload-to-cloud'  in classifyOnEdgeSpec:
                self.CLASSIFY_ON_EDGE_UPLOAD = classifyOnEdgeSpec['upload-to-cloud']
            else:
                self.CLASSIFY_ON_EDGE_UPLOAD = False
            # for the future...
            self.CLASSIFY_ON_EDGE_FILE_FORMAT = []
            classifyOnEdgeFileFormatSpec = classifyOnEdgeSpec['file-format']
            for ff in classifyOnEdgeFileFormatSpec.split(','):
                self.CLASSIFY_ON_EDGE_FILE_FORMAT.append(ff)
        else:
            self.CLASSIFY_ON_EDGE = False

class CaptureStateChangeListener:
    def __init__(self, client, deviceId):
        self.client = client
        self.deviceId = deviceId

    def stateUpdated(self, stateChangeMessage, time):
        content = '"timestamp":"{0:%Y%m%d%H%M%S%f}","deviceid":"{1}","status":"{2}"'.format(time, self.deviceId, stateChangeMessage)
        content = '{' + content + '}'
        message = Message(content)
        message.custom_properties['message-source']='sound-capturing'
        self.client.send_message_to_output(message,'output_status')
        print('Notified to Edge messeging - {}'.format(content))

class AIonEdgeFileUpdater(FileUpdaterBase):
    def __init__(self, client, deviceId, captureSpec):
        self.client = client
        self.deviceId = deviceId
        self.captureSpec = captureSpec
    
    async def uploadFile(self, fileName):
        content = '"deviceid":"{0}","data-file":"{1}"'.format(self.deviceId, fileName)
        content = '{' + content + '}'
        message = Message(content)
        message.custom_properties['message-source']='sound-capturing'
        self.client.send_message_to_output(message, 'output_data_file')
        if self.Fowarder is not None:
            self.Fowarder.uploadFile(fileName)

class SoundCaptureExecuter:
    def __init__(self, capture):
        self.capture = capture
        self.executingFlag = False
    def working(self,
            capture_channels,
            mic_device_chunk,
            mic_device_rate,
            mic_device_width,
            record_start_level, record_milliseconds,
            folder,
            capturingFileUpdater,
            stateChangeListener):

        loop = asyncio.new_event_loop()
        print('capturing working thread start...')
        loop.run_until_complete(self.capture.startCapture(capture_channels,
            mic_device_chunk,
            mic_device_rate,
            mic_device_width,
            record_start_level, record_milliseconds,
            folder,
            stateChangeListener,
            capturingFileUpdater))
        loop.close()
        print('capturing working thread done.')
        
    def start(self,
            captureSpec,
            folder,
            capturingFileUpdater,
            stateChangeListener):
        if self.executingFlag:
            print('thread has been started')
            return

        self.thread = threading.Thread(target=self.working,args=(captureSpec.CAPTURE_CHANNELS,
            captureSpec.RECORD_CHUNK,
            captureSpec.RECORD_RATE,
            captureSpec.RECORD_WIDTH,
            captureSpec.RECORD_START_LEVEL,
            captureSpec.RECORD_DURATION_MSEC,
            folder,
            capturingFileUpdater,
            stateChangeListener))
        print('Capturing thread will be started')
        self.thread.start()
        print('Capturing thread has been started')
        self.executingFlag = True

    async def stop(self):
        if self.executingFlag:
            print('Invoke stopCapture...')
            await self.capture.stopCapture()
            print('Stop requested')
            self.thread.join()
            print('worker thread is finished')
        else:
            print('thread ha not been started')

def resolveCaptureSetting(desiredPropsTwin):
    spec = CaptureSpec(desiredPropsTwin)
    return spec

async def main(micCapture):
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
        print ( "IoT Hub Client for Python version - {}".format(sys.version) )

        fileUpdater = BlobFileUpdater(BLOB_ON_EDGE_MODULE, BLOB_ON_EDGE_ACCOUNT_NAME, BLOB_ON_EDGE_ACCOUNT_KEY, SOUND_CONTAINER_NAME, IOTEDGE_DEVICEID)
        try:
            await fileUpdater.initialize()
            print('fileUpdater initialize completed.')
        except Exception as e:
            print('Exception happens during fileUpdater initialize - {}'.format(e))


        # The client object is used to interact with your Azure IoT hub.
        module_client = IoTHubModuleClient.create_from_edge_environment()

        # connect the client.
        module_client.connect()
        print('Connected to edge runtime.')

        if micCapture.getCurrentMicSpec():
            module_client.patch_twin_reported_properties(micCapture.getCurrentMicSpec())

        statusChangeListener = CaptureStateChangeListener(module_client, IOTEDGE_DEVICEID)

        async def desired_twin_update_listener(module_client, capture):
            print('Get current desired properties...')
            currentTwin = module_client.get_twin()
            print('Resolve current spec...')
            captureSpec = resolveCaptureSetting(currentTwin['desired'])
            capturingFileUpdater = None
            if captureSpec.CLASSIFY_ON_EDGE:
                capturingFileUpdater = AIonEdgeFileUpdater(module_client, IOTEDGE_DEVICEID, captureSpec)
                if captureSpec.CLASSIFY_ON_EDGE_UPLOAD:
                    capturingFileUpdater.Fowarder = BlobFileUpdater(BLOB_ON_EDGE_MODULE, BLOB_ON_EDGE_ACCOUNT_NAME, BLOB_ON_EDGE_ACCOUNT_KEY, SOUND_CONTAINER_NAME, IOTEDGE_DEVICEID)
            else:
                capturingFileUpdater = BlobFileUpdater(BLOB_ON_EDGE_MODULE, BLOB_ON_EDGE_ACCOUNT_NAME, BLOB_ON_EDGE_ACCOUNT_KEY, SOUND_CONTAINER_NAME, IOTEDGE_DEVICEID)

            while True:
                try:
                    soundCaptureExecuter = SoundCaptureExecuter(capture)
                    if (captureSpec.CAPTURE_ORDER):
                        print('Capturing on - capture thread starting...')
                        soundCaptureExecuter.start(captureSpec, SOUND_DATA_FOLDER, capturingFileUpdater, statusChangeListener)
                    else:
                        print("Capturing off...")
                    print('Waiting for module twin desired properties updated...')
                    patch = module_client.receive_twin_desired_properties_patch()  # blocking call
                    print("Twin patch received: - {}".format(patch))
                    captureSpec = resolveCaptureSetting(patch)
                    await soundCaptureExecuter.stop()

                    print('Current capture order is {}'.format(captureSpec.CAPTURE_ORDER))
                except Exception as e:
                    print('desired_twin_update_listener exception - {}'.format(e))


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

        # Schedule task for C2D Listener
        print('try to get device twin')
        dtwin = module_client.get_twin()
        print('current twin - {}'.format(dtwin['desired']))

        listeners = asyncio.gather(desired_twin_update_listener(module_client,micCapture))

        print ( "The sample is now waiting for messages and module twin update. ")

        # Run the stdin listener in the event loop
        loop = asyncio.get_event_loop()
        user_finished = loop.run_in_executor(None, stdin_listener)

        # Wait for user to indicate they are done listening for messages
        await user_finished

        print('executing loop exited')

        # Cancel listening
        listeners.cancel()

        # Finally, disconnect
        module_client.disconnect()
        print('IoT Hub connection is disconnected')

    except Exception as e:
        print ( "Unexpected error %s " % e )
        raise

if __name__ == "__main__":
    BLOB_ON_EDGE_MODULE = os.environ['BLOB_ON_EDGE_MODULE']
    BLOB_ON_EDGE_ACCOUNT_NAME = os.environ['BLOB_ON_EDGE_ACCOUNT_NAME']
    BLOB_ON_EDGE_ACCOUNT_KEY = os.environ['BLOB_ON_EDGE_ACCOUNT_KEY']
    SOUND_CONTAINER_NAME=os.environ['SOUND_CONTAINER_NAME']
    IOTEDGE_DEVICEID=os.environ['IOTEDGE_DEVICEID']
    MIC_DEVICE_NAME = os.environ['MIC_DEVICE_NAME']
    SOUND_DATA_FOLDER = os.environ['SOUND_DATA_FOLDER']
    MIC_DEVICE_NUM_OF_MIC = int(os.environ['MIC_DEVICE_NUM_OF_MIC'])

#    RESPEAKER_RATE = int(os.environ['RESPEAKER_RATE'])
#    RESPEAKER_CHANNELS = int(os.environ['RESPEAKER_CHANNELS'])
#    RESPEAKER_WIDTH = int(os.environ['RESPEAKER_WIDTH'])
#    RESPEAKER_CHUNK = int(os.environ['RESPEAKER_CHUNK'])
#    RECORD_MILLISECONDS = int(os.environ['RECORD_MILLISECONDS'])
#    RECORD_START_LEVEL = int(os.environ['RECORD_START_LEVEL'])

    print('IOTEDGE_DEVICEID:'+ IOTEDGE_DEVICEID)
    print('BLOB_ON_EDGE_MODULE:'+BLOB_ON_EDGE_MODULE)
    print('BLOB_ON_EDGE_ACCOUNT_NAME:'+BLOB_ON_EDGE_ACCOUNT_NAME)
    print('BLOB_ON_EDGE_ACCOUNT_KEY:'+BLOB_ON_EDGE_ACCOUNT_KEY)
    print('SOUND_CONTAINER_NAME:'+SOUND_CONTAINER_NAME)

    print('MI_DEVICE_NAME:'+ MIC_DEVICE_NAME)
    print('MIC_DEVICE_NUM_OF_MIC:'+ str(MIC_DEVICE_NUM_OF_MIC))
#    print('RESPEAKER_RATE:'+RESPEAKER_RATE);
#    print('RESPEAKER_CHANNELS:'+RESPEAKER_CHANNELS);
#    print('RESPEAKER_WIDTH:'+RESPEAKER_WIDTH);
#    print('RESPEAKER_CHUNK:'+RESPEAKER_CHUNK);

    micCapture = MicCapture()
    micCapture.findReSpeakerDevice(MIC_DEVICE_NAME,MIC_DEVICE_NUM_OF_MIC)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(micCapture))
    loop.close()


    # If using Python 3.7 or above, you can use following code instead:
    # asyncio.run(main())