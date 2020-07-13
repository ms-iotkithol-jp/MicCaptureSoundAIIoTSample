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
from azure.iot.device import IoTHubModuleClient
from azure.iot.device import Message

import tarfile
import shutil

def decompress_files(filename, dest_forder):
    os.makedirs(dest_forder,exist_ok=True)
    tar = tarfile.open(filename, "r:gz")
    tar.extractall(dest_forder)
    tar.close()

def parse_desired_property_request(predictSpec, module_client, sound_classifer):
    modelFileKey = 'model-file'
    if modelFileKey in predictSpec:
        modelUrl = predictSpec[modelFileKey]['url']
        modelFileName = predictSpec[modelFileKey]['name']
        print('Receive request of model update - {} - {}'.format(modelFileName, modelUrl))
        response = requests.get(modelUrl)
        if response.status_code == 200:
            os.makedirs('model',exist_ok=True)
            saveFileName = os.path.join('model',modelFileName)
            with open(saveFileName, 'wb') as saveFile:
                saveFile.write(response.content)
                print('Succeeded to download new model')
                if modelFileName.endswith('.tar.gz'):
                    print('try to decompress - {}'.format(saveFileName))
                    decompress_files(saveFileName, 'model')
                    print('decompress done.')
                    os.remove(saveFileName)
                    saveFileName = saveFileName[:len(saveFileName)-len('.tar.gz')]
                    print('new model is {}'.format(saveFileName))
                sound_classifer.load_model(saveFileName)
                print('loaded learned model!')
                for existingFile in os.listdir('model'):
                    print('compare name - {} <-> {}'.format(existingFile, saveFileName))
                    if os.path.basename(existingFile) != saveFileName:
                        print('Found old model')
                        old_file_path = os.path.join('model', existingFile)
                        if os.path.isfile(old_file_path):
                            os.remove(old_file_path)
                        else:
                            shutil.rmtree(old_file_path)
#                sound_classifer.load_model(saveFileName)
                module_client.patch_twin_reported_properties({'current-model':predictSpec[modelFileKey]})
        else:
            print('Failed to download new model - {}'.format(response.status_code))

    dataDefFileKey = 'data-def-file'
    if dataDefFileKey in predictSpec:
        dataDefUrl = predictSpec[dataDefFileKey]['url']
        dataDefFileName = predictSpec[dataDefFileKey]['name']
        print('Receive request of model update - {} - {}'.format(dataDefFileName, dataDefUrl))
        response = requests.get(dataDefUrl)
        if response.status_code == 200:
            os.makedirs('data-def',exist_ok=True)
            saveFileName = os.path.join('data-def',dataDefFileName)
            with open(saveFileName, 'wb') as saveFile:
                saveFile.write(response.content)
                print('Succeeded to download new data def file')
            for existingFile in os.listdir('data-def'):
                if existingFile != os.path.basename(saveFileName):
                    old_file_path = os.path.join('data_def',existingFile)
                    os.remove(old_file_path)
            sound_classifer.update_data_def(saveFileName)
            module_client.patch_twin_reported_properties({'current-data-def':predictSpec[dataDefFileKey]})
        else:
            print('Failed to download new model - {}'.format(response.status_code))
        print("Learned model and data definition file have been updated.")

async def main(data_folder_path):
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
        print ( "IoT Hub Client for Python" )

        if sys.version < "3.6.0":
            from classify_csv import SoundClassifier
        else:
            from classify_wav import SoundClassifier

        # The client object is used to interact with your Azure IoT hub.
        module_client = IoTHubModuleClient.create_from_edge_environment()

        # connect the client.
        module_client.connect()
        print("Connected to Edge Runtime.")

        currentTwin = module_client.get_twin()
        print('Resolve current spec...')
        predictSpec = currentTwin['desired']
        sound_classifer = SoundClassifier()
        parse_desired_property_request(predictSpec, module_client, sound_classifer)

        # initialize sound classifier

        for file in os.listdir('model'):
            if file.rfind('.h5') > 0:
                model_file_path = os.path.join('model',file)
                sound_classifer.load_model(model_file_path)

        async def desired_twin_update_listener(module_client, soundclassifier):
            print('Get current desired properties...')
            currentTwin = module_client.get_twin()
            print('Resolve current spec...')
            predictSpec = currentTwin['desired']
            parse_desired_property_request(predictSpec, module_client, sound_classifer)

        # define behavior for receiving an input message on input_sound_data
        async def input_sound_data_listener(module_client, soundclassifier):
            while True:
                print("waiting message from 'input_sound_data'")
                input_message = module_client.receive_message_on_input("input_sound_data")  # blocking call
                try:
                    print("custom properties are")
                    print(input_message.custom_properties)
                    if 'message-source' in input_message.custom_properties:
                        if input_message.custom_properties['message-source'] == 'sound-capturing':
                            print("the data in the message received on input_sound_data was ")
                            tmpFileName = 'data' + soundclassifier.get_fileformat()
                            targetDataFile = input_message.custom_properties['data-file']
                            if targetDataFile.endswith(soundclassifier.get_fileformat()):
                                with open(tmpFileName,'wb') as tf:
                                    tf.write(input_message.data)
                                    print('Saved content in {} as {}'.format(targetDataFile,tmpFileName))
                                predictedResult = soundclassifier.predict(tmpFileName)
                                print('Classification Succeeded')
                                os.remove(tmpFileName)
                                
                                outputMessageJson = {'timestamp':'{0:%Y/%m/%dT%H:%M:%S.%f}'.format(datetime.datetime.now()),'channels': []}
                                for p in predictedResult.keys():
#                                    print('channel:{},predicted:{} as type:{}'.format(p,predictedResult[p],type(predictedResult[p])))
                                    channelPredicted = {}
                                    channelPredicted['channel'] = p
                                    if soundclassifier.get_fileformat() == 'csv':
                                        channelPredicted['predicted'] = []
                                        cindex = 1
                                        for cdata in predictedResult[p]:
                                            channelPredicted['predicted'].append({'chunk':cindex,'result':cdata})
                                        outputMessageJson['channels'].append(channelPredicted)
                                    else: # wav
                                        channelPredicted['predicted'] = predictedResult[p]
                                content = json.dumps(outputMessageJson)
                                message = Message(content)
                                message.custom_properties['message-source']='sound-classifier'
                                module_client.send_message_to_output(content, "output_classified")
                                print('sent result:{} to {}'.format(content),'output_classified')
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
        user_finished = loop.run_in_executor(None, listeners)

        # Wait for user to indicate they are done listening for messages
        await user_finished

        # Cancel listening
        listeners.cancel()

        # Finally, disconnect
        module_client.disconnect()

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