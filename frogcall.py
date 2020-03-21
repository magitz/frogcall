#!/usr/bin/env python3
""" frogcall.py
   
   This is a set of functions and a general script to parse audio from recorded frog calls.

   These files begin with French audio which describes the species, location and date
   the recording. The script transcribes the audio with one or more text to speech services, 
   parses out the recoding date, and outputs the transcriptions. The script also splits the 
   original audio using periods of silence to create individual calls and to separate the 
   speaking from the frog calls themselves.

   Author: Matt Gitzendanner
           magitz@ufl.edu
           University of Florida
           Department of Biology
   
   License: GLP3
   
   Version history:
      0.5: First functional release: March 21, 2020
"""

import dateparser
from pydub import AudioSegment
from pydub.silence import split_on_silence
import glob,re, os, sys, argparse
import speech_recognition as sr
import yaml

def transcribe_file(file, key_dict, language='fr-FR', recognizer="Google", duration=20):
   """Transcribe an audio file with Speech Recognition library.
   
   Positional Parameters: 
      the file, a dictionary of apikeys

   Key word parameters: 
      language= audio language 
      recognizer= speech recognizer ot use 
      duration= duration of audio to transcribe.
   """
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

def split_transcript(transcript):
   """Split transcription into text and date using first digit in transcription.

      Method is adapted from: https://stackoverflow.com/questions/4510709/find-the-index-of-the-first-digit-in-a-string
      
      In the Google transcript of the sample data, the date is the first digit of the transcript text.
      This may or may not be appropriate for your text, this works for our needs.
   """
   match = re.search(r"\d",transcript)
   if match is not None:
      text=transcript[:match.start()]
      date=transcript[match.start():]
  
   return text,date

def split_audio(filepath, silence_len):
   """Split audio file based on periods of silence.

      Positional Parameters:
         the path to the audio file,
         the length of silence in milliseconds for splitting the audio.
   """
   sound = AudioSegment.from_wav(filepath)
   dBFS = sound.dBFS
   chunks = split_on_silence(sound, 
      min_silence_len = silence_len,
      silence_thresh = dBFS-16,
      keep_silence = 250 ) #optional
   return chunks

def make_chunk_files(chunks, file_name, out_folder):
   """Make the individual chunk files created with split_audio."""
   chunk_count=0
   for chunk in chunks:
      # Name for the chunk files, replacing spaces in filenames with "_"
      new_name= os.path.join(out_folder,os.path.splitext(file_name)[0].replace(' ', '_')) + "_" + str(chunk_count) + ".wav"

      # Export the chunk file
      file_handle = chunk.export(new_name, 
                                 format='wav',
                                 bitrate='192k')
     
      chunk_count+=1
   return chunk_count
   

def prep_outputs(output_folder, outfile, trans):
   """Prepare the output folder and header of summary file."""
   # Make output directory if it doesn't exist
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

      header = "Original_Filename,Chunk_file_name"
      if 'Google' in transcriptions:
         header = header + ",Parsed_Date"
      header = header + "," + ','.join(transcriptions) + "\n"

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
   """Read the api key file into a dictionary."""
   try:
      key_file = open(file, 'r')
   except:
      print(f"Can't open apikey file for reading API keys: {file}")
    
   key_dict= yaml.load(key_file, Loader=yaml.SafeLoader)
   return key_dict

if __name__ == '__main__': 

   # Parse command line arguments
   parser = argparse.ArgumentParser(
        usage = "%(prog)s -f call_file -o output_folder -s summary_file -d silence duration -t transcription service to use",
        description = "Parses frog calls"
    )
   parser.add_argument(
        "--version", action='version',
        version = "version 0.5"
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
   api_file=sys.path[0] + '/apikeys'
   api_key_dict = get_api_keys(api_file)
   
   transcript={}

   for trans in transcriptions:
      transcript[trans] = transcribe_file(args.file, api_key_dict, recognizer=trans)

   if 'Google' in transcriptions:
      text,date = split_transcript(transcript['Google'])
      formatted_date = dateparser.parse(date, languages=['fr'], locales=['fr-PF'])
   else:
      if args.verbose:
         print('No Google transcript requested, date will not be parsed\n')

   file_chunks = split_audio(args.file,args.silence_duration)
   n_chunks = make_chunk_files(file_chunks, os.path.basename(args.file), args.output_folder)

   if args.verbose : 
      print(f" Transcript of {os.path.basename(args.file)}:\n ") 
      for trans in transcriptions:
         print(f"{trans} : {transcript[trans]} \n")
      if formatted_date:
         print(f"Date: {formatted_date}\n")
      print("\n\n")

   for chunk in range(n_chunks):
      output_string = os.path.basename(args.file)
      chunk_name = os.path.join(args.output_folder,os.path.splitext(args.file)[0].replace(' ', '_')) + "_" + str(chunk) + ".wav"
      output_string = ','.join([output_string,chunk_name])
      if 'Google' in transcriptions:
         output_string = ','.join([output_string,formatted_date.isoformat()])
      for key, value in transcript.items():
         output_string = ','.join([output_string,value])
      output_string = output_string  + "\n" 
      OUT.write(output_string)

   OUT.close()