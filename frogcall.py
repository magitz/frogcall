#!/usr/bin/env python3

import dateparser
from pydub import AudioSegment
from pydub.silence import split_on_silence
import glob,re,os
import speech_recognition as sr
import yaml
import argparse


def split_audio(filepath,silence_len):
    sound = AudioSegment.from_wav(filepath)
    dBFS = sound.dBFS
    chunks = split_on_silence(sound, 
        min_silence_len = silence_len,
        silence_thresh = dBFS-16,
        keep_silence = 250 )#optional
    return chunks

# Do Speech Recognition on an audio file
def transcribe_file(file, language='fr-FR', recognizer="Google", duration=20):
   Audio = sr.AudioFile(file)
   with Audio as source:
     audio = recog.record(source,duration=duration)
   if recognizer == "Google":
     transcript = recog.recognize_google(audio,language=language)
   elif recognizer == "Wit":
     transcript = recog.recognize_wit(audio, api_key_dict[wit_key])
   elif recognizer == "IBM":
     transcript = recog.recognize_ibm(audio, api_key_dict[IBM_USER], api_key_dict[IBM_PASS],language=language) 

   return transcript

# Split transcription into text and date
#   Method adapted from: https://stackoverflow.com/questions/4510709/find-the-index-of-the-first-digit-in-a-string
def split_transcript(transcript):
   match = re.search(r"\d",transcript)
   if match is not None:
      text=transcript[:match.start()]
      date=transcript[match.start():]
  
   return text,date

def make_chunk_files(chunks,write=False):
   chunk_count=0
   for chunk in chunks:
     name_text = text[:35].strip().replace(' ', '_')  # Rename files based on transcribed text
     if len(name_text) <= 4:                          # But keep original name if transcription is too short
       name_text = os.path.basename(file)

   new_name= os.path.join(file_path,output_folder,name_text) + "_" + str(chunk_count) + ".wav"
  

   file_handle = chunk.export(new_name, 
                              format='wav',
                              bitrate='192k')
    
   if write:
      # Write summary information to output file.
      output_string= ",".join([os.path.basename(file), os.path.basename(new_name), transcript, text, date, str(formatted_date), str(chunk_count), str(len(mychunks))])
      OUT.write(output_string)
      OUT.write('\n')

   chunk_count+=1

def get_api_keys(file):
    try:
        key_file = open(file, 'r')
    except:
        f"Can't open {file} for reading API keys"
    
    key_dict= yaml.load(key_file)
    return key_dict

if __name__ ==  '__main__ ': 


   ###############
   # Define some constants 

   # Set foldername for the split sound files and summary file.
   output_folder = 'Compare'

   # Summary filename
   outfile = 'Frog_calls.csv'

   # Set duration for silence
   silence_duration = 750

   parser = argparse.ArgumentParser(
        usage = "%(prog)s path_to_calls ...",
        description = "Parses frog calls"
    )
   parser.add_argument(
        "-v","--version", action='version',
        version = "version 0.3"
    )
   parser.add_argument(
        "-p", "--path", type=str, 
        help = "Path to folder of frog calls"
    )

   # Create a recognizer
   recog = sr.Recognizer()

   # Load API keys into dict--"apikeys" should be a yaml file with your API keys
   # See apikey.example for example file
   api_key_dict = get_api_keys('apikeys')

   # Make output dirctory if it doesn't exist.
   output_folder_path = os.path.join(args.p, output_folder)

   if (not os.path.isdir(output_folder_path)):
      os.mkdir(output_folder_path)

   # Setup the output file
   outfile_name = os.path.join(output_folder_path,outfile)
   print(f"Writing output to {outfile_name}")

   try:
      OUT=open(outfile_name, 'w')
   except:
      print("Can't open outfile for writing: %s" %(outfile_name))


   #OUT.write("Original_filename,New_filename,Full_Trasncription,Text_Transcription,Date_Transcription,Formatted_Date,Chunk_N,Number_of_chunks\n")
   OUT.write("Filename,Google_Transcription,Wit_Transcription,IBM_Transcription\n")

   files = os.path.join(args.p,'*.wav')

   for file in glob.glob(files):
      Google_transcript =transcribe_file(file)
      Wit_transcript = transcribe_file(file, recognizer='Wit')
      #IBM_transcript = transcribe_file(file,recognizer='IBM')

      print(f" Transcript of {os.path.basename(file)}:\n   Google: {Google_transcript}\n   Wit: {Wit_transcript}\n   IBM: {IBM_transcript}\n")

      output_string= ",".join([os.path.basename(file),Google_transcript,Wit_transcript,IBM_transcript,"\n"])
      OUT.write(output_string)

      print("\n\n")

   OUT.close()