import numpy as np
from loadsounds import parse_file, load_data_definition, reshape_dataset

data_def_file = 'sounddata.yml'
datafile = 'cherry-sound-20200218113643319806.csv'
data_chunk = load_data_definition(data_def_file)
csv_dataset = parse_file(datafile,np.array([]),data_chunk, by_channel=True)
#sound_dataset = np.zeros((csv_dataset[0], 1, 1, data_chunk))
#index = 0
#for d in csv_dataset[1]:
#    sound_dataset[index][0][0] = d
#    index = index + 1

import datetime
import json
import tensorflow as tf
from tensorflow.keras import datasets, layers, models

print('tensorflow version - '+tf.__version__)

model_file_path ='sound-classification-model.h5'
# model name should be used other style
model = models.load_model(model_file_path)

predicted_results ={}

for channel, csvds in enumerate(csv_dataset[1]):
    sound_dataset = reshape_dataset(csvds, data_chunk)
    predicted = model.predict(sound_dataset)
    print('channel:{}'.format(channel))
    result = predicted.tolist()
    for r in result:
        print('{0}<->{1}'.format(r[0],r[1]))
    predicted_results[channel] = result

outputMessageJson = {'timestamp':'{0:%Y/%m/%dT%H:%M:%S.%f}'.format(datetime.datetime.now()),'predicted': []}
for p in predicted_results.keys():
    outputMessageJson['predicted'].append({'channel':str(p), 'predicted':predicted_results[p]})

print('result - {}'.format(json.dumps(outputMessageJson)))