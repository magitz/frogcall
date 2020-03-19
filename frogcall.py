#!/usr/bin/env python3

import dateparser
from pydub import AudioSegment
from pydub.silence import split_on_silence
import glob,re, os, sys, argparse
import speech_recognition as sr
import yaml


def split_audio(filepath,silence_len):
    sound = AudioSegment.from_wav(filepath)
    dBFS = sound.dBFS
    chunks = split_on_silence(sound, 
        min_silence_len = silence_len,
        silence_thresh = dBFS-16,
        keep_silence = 250 )#optional
    return chunks

# Do Speech Recognition on an audio file
def transcribe_file(file, key_dict, language='fr-FR', recognizer="Google", duration=20):
   # Create a recognizer
   recog = sr.Recognizer()

   Audio = sr.AudioFile(file)
   with Audio as source:
     audio = recog.record(source,duration=duration)
   if recognizer == "Google":
     transcript = recog.recognize_google(audio,language=language)
   elif recognizer == "Wit":
     transcript = recog.recognize_wit(audio, key_dict['wit_key'])
   elif recognizer == "IBM":
     transcript = recog.recognize_ibm(audio, key_dict['IBM_USER'], key_dict['IBM_PASS'],language=language) 
   else:
      sys.exit(f"{recognizer} is not a valid transcription tool.\n")

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

def prep_outputs(output_folder, outfile, trans):
   # Make output dirctory if it doesn't exist
   if (not os.path.isdir(output_folder)):
      os.mkdir(output_folder)

   # Setup the output summary file
   outfile_name = os.path.join(output_folder,outfile)
   
   # If the file doesn't exist, create it and add the header.
   if (not os.path.isfile(outfile_name)):
      try:
         OUT=open(outfile_name, 'w')
         if args.verbose:
            print(f"Writing output to {outfile_name}")
      except:
         print("Can't open summary for writing: %s" %(outfile_name))

      header = "Filename," + ','.join(transcriptions) + "\n"
      OUT.write(header)

   # If it does exist, append to existing file.
   else:
      try:
         OUT=open(outfile_name, 'a')
         if args.verbose:
            print(f"Writing output to {outfile_name}")
      except:
         print("Can't open summary for writing: %s" %(outfile_name))

   return OUT

def get_api_keys(file):
    try:
        key_file = open(file, 'r')
    except:
        print("Can't open apikey file for reading API keys")
    
    key_dict= yaml.load(key_file, Loader=yaml.SafeLoader)
    return key_dict

if __name__ == '__main__': 

   # Parse command line arguments
   parser = argparse.ArgumentParser(
        usage = "%(prog)s -p path_to_call -o output_folder -s summary_file -d silence duration",
        description = "Parses frog calls"
    )
   parser.add_argument(
        "--version", action='version',
        version = "version 0.3"
    )
   parser.add_argument(
        "-f", "--file", type=str, action="store", dest = "file",
        help = "Frog call file"
    )
   parser.add_argument(
      "-o", "--output_folder", type = str, 
      default = 'Compare', action="store", dest = "output_folder",
      help="*Folder* name for the split sound files and summary file. Default: ./Compare"
   )
   parser.add_argument(
      "-s", "--summary_file", type=str,
      default = 'Frog_calls.csv', action="store", dest = "summary_file",
      help = "Name for summary file, default: Frog_calls.csv"
   )
   parser.add_argument(
      "-d", "--silence_duration", type=int, dest = "silence_duration",
      default = 750, action="store",
      help = "Silence duration when splitting audio clips"
   )
   parser.add_argument(
      "-t", "--transcriptions", dest = "transcriptions",
      choices=['Google', 'Wit', 'IBM'],
      default = ["Google"], nargs='+',
      help = "Transcription service to use: Google, Wit, IBM. Can be used multiple times. Default= 'Google'"
   )
   parser.add_argument(
        "-v","--verbose", action = "store_true", dest = "verbose",
        help = "Turn on high verbosity and printing to screen"
    )

   args = parser.parse_args()
   transcriptions =  [item for item in args.transcriptions]
   path = os.path.dirname(args.file)

   OUT = prep_outputs(args.output_folder, args.summary_file,args.transcriptions)

   # Load API keys into dict--"apikeys" should be a yaml file with your API keys
   # See apikey.example for example file
   api_key_dict = get_api_keys('apikeys')
   
   transcript={}

   for trans in transcriptions:
      transcript[trans] = transcribe_file(args.file, api_key_dict, recognizer=trans)

   
   if args.verbose : 
      print(f" Transcript of {os.path.basename(args.file)}:\n ") 
      for trans in transcriptions:
         print(f"{trans} : {transcript[trans]} \n")
      print("\n\n")

   output_string = os.path.basename(args.file) 
   for key, value in transcript.items():
      output_string = ','.join([output_string,value])
   output_string = output_string  + "\n" 
   OUT.write(output_string)

   OUT.close()