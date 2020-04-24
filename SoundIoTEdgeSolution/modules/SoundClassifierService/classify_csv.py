import numpy as np
from loadsounds import parse_file, load_data_definition, reshape_dataset

import tensorflow as tf
from tensorflow.keras import datasets, layers, models

print('tensorflow version - '+tf.__version__)

class SoundClassifier:
    def __init__(self):
        self.version = '0.1.0'
        self.data_def = load_data_definition('sounddata.yml')

    def load_model(self, model_file_path):
        self.model = models.load_model(model_file_path)

    def set_data_chunk(self, chunk):
        self.data_chunk = chunk

    def predict(self, datafile):
        print('parsing - {}...'.format(datafile))
        # For CSV Style
        csv_dataset = parse_file(datafile,np.array([]), self.data_chunk, by_channel=True)

        predicted_results = {}

        for channel, csvds in enumerate(csv_dataset[1]):
            sound_dataset = reshape_dataset(csvds, self.data_chunk)   
            predicted = self.model.predict(sound_dataset)
            print('channel:{}'.format(channel))
            result = predicted.tolist()
            for r in result:
                print('{0}<->{1}'.format(r[0],r[1]))
            predicted_results[channel] = result
        return predicted_results


