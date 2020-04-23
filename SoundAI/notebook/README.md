# Sample CNN modeling and traing for sound classication
Before you try 'ai-sound-major-miner-classification-part1.ipynb' please learn basis of Azure Machine Learning Studio by 
- [Tutorial 1st experiment SDK setup](https://docs.microsoft.com/ja-jp/azure/machine-learning/tutorial-1st-experiment-sdk-setup)
- [Tutorial train mode with aml](https://docs.microsoft.com/ja-jp/azure/machine-learning/tutorial-train-models-with-aml)

Then create folder named 'sound' in the same level of the 'tutorials' folder on your Azure ML studio's workspace and upload files in the folder.
- [AI Sound major/minor chord classification part1 - training](./ai-sound-major-miner-classification-part1-wav.ipynb)
- [AI Sound major/minor chord classification part2 - deploy trained model on cloud side](ai-sound-major-miner-classification-part2-wav.ipynb) ※ This is just alpha level with no testing
- Deploy trained model on edge side - please see [Sound Classifier Service module on IoT Edge](../SoundIoTEdgeSolution)

<b><font color=red>Caution:</font></b>  
I don't believe the CNN model for sound classification in this tutorial. The purpose of this tutorial is not to show sound classification modeling itself but to demonstrate basis for practicing sound classification with CNN in the environment using Azure ML Studio! 
If you know some other pracitical algorithm, FFT, Time Series based approach and so on, please let me know how to do it in detail.  Thank you! 