import sys
from classify import SoundClassifier

if sys.version < "3.6.0":
    print("Wav edition requires Python 3.6.0+ only")
    print("Please use test-csv.py")
    exit

sound_classifier = SoundClassifier()
model_path = 'sound-classification-wav-model.h5'
sound_classifier.load_model(model_path)
datafile = 'fender-sound-20200209170603399214.wav'
predicted = sound_classifier.predict(datafile)
print('result - {}'.format(predicted))
