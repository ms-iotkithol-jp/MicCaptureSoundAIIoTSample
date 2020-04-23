# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import time
import os
import sys
import json
import datetime
import asyncio
from six.moves import input
import threading
import requests
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import Message
from classify import SoundClassifier

async def main(data_folder_path):
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
        print ( "IoT Hub Client for Python" )

        # The client object is used to interact with your Azure IoT hub.
        module_client = IoTHubModuleClient.create_from_edge_environment()

        # connect the client.
        await module_client.connect()

        # initialize sound classifier
        sound_classifer = SoundClassifier()
        for file in os.listdir('model'):
            if file.rfind('.h5') > 0:
                model_file_path = os.path.join('model',file)
                sound_classifer.load_model(model_file_path)

        async def desired_twin_update_listener(module_client, soundclassifier):
            print('Get current desired properties...')
            currentTwin = module_client.get_twin()
            print('Resolve current spec...')
            predictSpec = currentTwin['desired']
            chunkKey = 'record-chunk'
            if chunkKey in predictSpec:
                soundclassifier.set_data_chunk(predictSpec['record-chunk'])
            modelFileKey = 'model-file'
            if modelFileKey in predictSpec:
                modelUrl = predictSpec[modelFileKey]['url']
                modelFileName = predictSpec[modelFileKey]['name']
                print('Receive request of model update - {} - {}'.format(modelFileName, modelUrl))
                response = requests.get(modelUrl)
                if response.status_code == 200:
                    saveFileName = os.path.join('model',modelFileName)
                    with open(saveFileName, 'wb') as saveFile:
                        saveFile.write(response.content)
                    print('Succeeded to download new model')
                    soundclassifier.load_model(saveFileName)
                    for file in os.listdir('model'):
                        if file != saveFileName:
                            os.remove(file)
                    module_client.patch_twin_reported_properties({'current-mode':predictSpec[modelFileKey]})
                else:
                    print('Failed to download new model - {}'.format(response.status_code))

        # define behavior for receiving an input message on input_sound_data
        async def input_sound_data_listener(module_client, soundclassifier):
            while True:
                input_message = await module_client.receive_message_on_input("input_sound_data")  # blocking call
                try:
                    print("the data in the message received on input_sound_data was ")
                    print(input_message.data)
                    msgJson = json.loads(input_message.data)
                    print("custom properties are")
                    print(input_message.custom_properties)
                    predictedResult = soundclassifier.predict(msgJson['data-file'])
                    print('Classification Succeeded')
                    outputMessageJson = {'timestamp':'{0:%Y/%m/%dT%H:%M:%S.%f}'.format(datetime.datetime.now()),'predicted': []}
                    for p in predictedResult.keys():
                        outputMessageJson['predicted'].append({'channel':str(p), 'predicted':predictedResult[p]})
                    content = json.dumps(outputMessageJson)
                    message = Message(content)
                    message.custom_properties['message-source']='sound-classifier'
                    await module_client.send_message_to_output(outputMessageJson, "output_classified")
                except Exception as e:
                    print('Failed to classify - {0}'.format(e))
                
        # define behavior for halting the application
        def stdin_listener():
            while True:
                try:
                    selection = input("Press Q to quit\n")
                    if selection == "Q" or selection == "q":
                        print("Quitting...")
                        break
                except:
                    time.sleep(10)
        
        # Schedule task for C2D Listener
        listeners = asyncio.gather(
            input_sound_data_listener(module_client, sound_classifer),
            desired_twin_update_listener(module_client, sound_classifer))

        print ( "The sample is now waiting for messages. ")

        # Run the stdin listener in the event loop
        loop = asyncio.get_event_loop()
        user_finished = loop.run_in_executor(None, stdin_listener)

        # Wait for user to indicate they are done listening for messages
        await user_finished

        # Cancel listening
        listeners.cancel()

        # Finally, disconnect
        await module_client.disconnect()

    except Exception as e:
        print ( "Unexpected error %s " % e )
        raise

if __name__ == "__main__":
    SOUND_DATA_FOLDER = os.environ['SOUND_DATA_FOLDER']

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(SOUND_DATA_FOLDER))
    loop.close()

    # If using Python 3.7 or above, you can use following code instead:
    # asyncio.run(main())