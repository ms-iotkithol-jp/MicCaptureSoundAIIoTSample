import numpy as np
# For CSV style 
# from loadsounds import parse_file, load_data_definition, reshape_dataset
# For WAV style
import wave
from scipy.io.wavfile import read
from loadwavsounds import take_fft, divid_data_by_minimum_shape, load_data_definition

import tensorflow as tf
from tensorflow.keras import datasets, layers, models

print('tensorflow version - '+tf.__version__)

class SoundClassifier:
    # data_def_file = 'sounddata.yml'
    # datafile = 'cherry-sound-20200218113643319806.csv'
    def __init__(self):
        self.version = '0.1.0'
  #      self.data_def = load_data_definition('sounddata-wav.yml')
        self.file_format = 'wav'

    #model_file_path ='model/sound-classification-model.h5'
    # model name should be used other style
    def load_model(self, model_file_path):
        self.model = models.load_model(model_file_path)

    def update_data_def(self, data_def_file_path):
        self.data_def = load_data_definition(data_def_file_path)

    def predict(self, datafile):
        predicted_results ={}
        if datafile.endswith(self.file_format):
            print('parsing - {}...'.format(datafile))
        
            # For WAV Style
            fft = self.data_def['fft-freq']
            mels = self.data_def['fft-mels']
            dataWidth = self.data_def['data-width']

            wv = wave.open(datafile,'rb')
            wvinfo = wv.getparams()
            fs, data = read(datafile)
            sounds = []
            if wvinfo.nchannels == 1:
                sounds.append(data)
            else:
                tdata = data.T
                for w in tdata:
                    sounds.append(w)

            for channel, data in enumerate(sounds):
                fft_data = take_fft(data, fs, fft, mels)
                wav_dataset = divid_data_by_minimum_shape(fft_data[0], dataWidth)
                data_of_sounds = np.zeros((len(wav_dataset),1, mels, dataWidth), dtype=np.float)
                for index, wd in enumerate(wav_dataset):
                    data_of_sounds[index][0] = wd
    
                dataShape = data_of_sounds[0].shape
                data_of_sounds = data_of_sounds.reshape(len(data_of_sounds),dataShape[1],dataShape[2],dataShape[0])

                predicted = self.model.predict(data_of_sounds)
                result = predicted.tolist()
                predicted_results[channel] = result

        else:
            print('bad format - {}'.format(datafile))

        return predicted_results


