# Frog Call AI

This set of functions and scripts is part of a project to train artificial intelligence/deep learning models to score recordings taken over long time periods at a lakeside for frog species, call frequency and call duration.

The firs step is to create a training dataset for the models. For this we used the four disk audio recordings from the book *need reference here*. This book comes with audio disks with recordings of several hundred frog calls. The author starts each recording with a spoken description of the species, location and date of the recording and then there are several calls of that species. In some cases there is additional information in the spoken portion of the recording. The audio is in French.

## frogcall.py

As a first pass, this script uses one or more of the available [speech recognition engines](https://pypi.org/project/SpeechRecognition/) to transcribe the French speech. In addition, if the Google recognizer is used, the script will parse the date of the recording, using the first digits in the transcription to locate the date information and the [dateparser](https://dateparser.readthedocs.io/en/latest/#) library.

The script will also split the audio file into chunks using a configurable period of silence using the [pydub library](https://github.com/jiaaro/pydub). This is both to remove the portion of the audio that is the speaking portion, and to split individual calls into multiple files. This is used to generate the model training and testing data. This value, the `silence_duration` will likely need some exploration to determine the best value to use.

The main output of the script is a .csv file that includes to input filename, the path and filenames of the output chunk files, the date parsed from the Google transcription, and the text of the selected transcriptions.

Additional manual work will be needed to:

* Verify the date
* Populate a column with species names. Initial testing showed that the transcriptions do not do the best with species names, so while some may be correct, and others may give a good start, someone with knowledge of the species should listen to the audio and add a column with the correct species names for each chunk file.
* Populate a column with the location data. While there may not be a use for the data, it is most easily recorded while going through the audio files the first time and should be done in case there is a need.
* Flag which chunk files are audio of the speaker vs which are in fact the frog species. This could be done in the species column with something like "human" to designate spoken audio which can then be ignored for the training dataset.
* Verify that the chunk files are reasonable splitting of individual frog calls. If there are multiple calls in a file, you might re-run with a smaller `silence_duration`, if a single call is split, re-run with a larger `silence_duration`.
* Add any other pertinent notes based on the speech, audio file or other information.

Once the output is processed, the next step will be to train the AI model to recognize each species.

### apikey file

You will need to generate API keys if you want to use the Wit or IBM speech recognition engines. The `apikeys.example` file shows the format. Please add your keys and rename the file to just "apikeys". The script will look in the same directory it is in for the apikeys file. apikeys is in the .gitignore list and will be ignored.
