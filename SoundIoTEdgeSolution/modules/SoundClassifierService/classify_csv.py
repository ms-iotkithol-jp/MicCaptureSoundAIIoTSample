import numpy as np
from loadsounds import parse_file, load_data_definition, reshape_dataset

import tensorflow as tf
from tensorflow.keras import datasets, layers, models

print('tensorflow version - '+tf.__version__)

class SoundClassifier:
    def __init__(self):
        self.version = '0.1.0'
    #    self.data_chunk = load_data_definition('sounddata-csv.yml')
        self.data_chunk = 1024
        self.file_format = 'csv'

    def load_model(self, model_file_path):
        self.model = models.load_model(model_file_path)

    def update_data_def(self, data_def_file_path):
        self.data_chunk = load_data_definition(data_def_file_path)
    
    def get_fileformat(self):
        return self.file_format

    def predict(self, datafile):
        predicted_results = {}
        if datafile.endswith(self.file_format):
            print('parsing - {}...'.format(datafile))
            # For CSV Style
            csv_dataset = parse_file(datafile,np.array([]), self.data_chunk, by_channel=True)

            for channel, csvds in enumerate(csv_dataset[1]):
                sound_dataset = reshape_dataset(csvds, self.data_chunk)   
                predicted = self.model.predict(sound_dataset)
                print('channel:{}'.format(channel))
                result = predicted.tolist()
                for r in result:
                    print('{0}<->{1}'.format(r[0],r[1]))
                predicted_results[channel] = result
        else:
            print('bad format - {}'.format(datafile))

        return predicted_results


