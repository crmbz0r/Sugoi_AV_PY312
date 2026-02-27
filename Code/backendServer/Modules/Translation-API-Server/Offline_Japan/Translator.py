from flask import Flask
from flask import request
from flask_cors import CORS, cross_origin
from waitress import serve
import ctranslate2
import re
import time
import getopt, sys, os, json, signal
import sentencepiece as spm
import json
import plugins 
#===========================================================
# INITIALIATION
#===========================================================
user_settings_file = open("../../../../User-Settings.json", encoding="utf-8")
user_settings_data = json.load(user_settings_file)

port = user_settings_data["Translation_API_Server"]["Offline_Japan"]["HTTP_port_number"]
gpu = user_settings_data["Translation_API_Server"]["Offline_Japan"]["gpu"]
device = user_settings_data["Translation_API_Server"]["Offline_Japan"]["device"] # cuda or cpu
intra_threads = user_settings_data["Translation_API_Server"]["Offline_Japan"]["intra_threads"]
inter_threads= user_settings_data["Translation_API_Server"]["Offline_Japan"]["inter_threads"]
beam_size = user_settings_data["Translation_API_Server"]["Offline_Japan"]["beam_size"]
repetition_penalty = user_settings_data["Translation_API_Server"]["Offline_Japan"]["repetition_penalty"]
silent = user_settings_data["Translation_API_Server"]["Offline_Japan"]["silent"]
disable_unk = user_settings_data["Translation_API_Server"]["Offline_Japan"]["disable_unk"]

modelDir = "./Sugoi_Model/ct2Model/"
sp_source_model = "./Sugoi_Model/spmModels/spm.ja.nopretok.model"
sp_target_model = "./Sugoi_Model/spmModels/spm.en.nopretok.model"

#===========================================================
# MAIN APPLICATION
#===========================================================

# translator = ctranslate2.Translator(modelDir, device=device, intra_threads=intra_threads, inter_threads=inter_threads)

def tokenizeBatch(text, sp_source_model):
    sp = spm.SentencePieceProcessor(sp_source_model)
    if isinstance(text, list):
        return sp.encode(text, out_type=str)
    else:
        return [sp.encode(text, out_type=str)]


def detokenizeBatch(text, sp_target_model):
    sp = spm.SentencePieceProcessor(sp_target_model)
    translation = sp.decode(text)
    return translation



class Main_Translator:
    def __init__(self):
        self.translator_ready_or_not = False
        self.can_change_language_or_not = False
        self.supported_languages_list = {"English": "English", "Japanese": "Japanese"}
        self.input_language = self.supported_languages_list["Japanese"]
        self.output_language = self.supported_languages_list["English"]
        self.translator = ""
        self.stop_translation = False

    def pause(self):
        self.stop_translation = True

    def resume(self):
        self.stop_translation = False

    def activate(self):
        self.translator = ctranslate2.Translator(modelDir, device=device, intra_threads=intra_threads, inter_threads=inter_threads)
        self.translator_ready_or_not = True
        return self.translator_ready_or_not
    
    def translate(self, input_text):
        if isinstance(input_text, list):
            result = self.translate_batch(input_text)
            return result
        else:
            input_text = plugins.process_input_text(input_text)
            if (self.stop_translation == True):
                return "Translation is paused at the moment"
            else:
                translated = self.translator.translate_batch(
                    source=tokenizeBatch(input_text, sp_source_model), 
                    beam_size=beam_size, 
                    num_hypotheses=1, 
                    return_alternatives=False, 
                    disable_unk=disable_unk, 
                    replace_unknowns=False, 
                    no_repeat_ngram_size=repetition_penalty
                )

                finalResult = []
                for result in translated:
                    detokenized = ''.join(detokenizeBatch(result.hypotheses[0], sp_target_model))
                    finalResult.append(detokenized)

                if isinstance(input_text, list):
                    return finalResult
                else:
                    result = plugins.process_output_text(finalResult[0])
                    return result

    def translate_batch(self, list_of_input_text):
        if (self.stop_translation == True):
            return "Translation is paused at the moment"
        else:
            translated = self.translator.translate_batch(
                source=tokenizeBatch(list_of_input_text, sp_source_model), 
                beam_size=beam_size, 
                num_hypotheses=1, 
                return_alternatives=False, 
                disable_unk=disable_unk, 
                replace_unknowns=False, 
                no_repeat_ngram_size=repetition_penalty
            )

            finalResult = []
            for result in translated:
                detokenized = ''.join(detokenizeBatch(result.hypotheses[0], sp_target_model))
                finalResult.append(detokenized)

            if isinstance(list_of_input_text, list):
                return finalResult
            else:
                return finalResult[0]


    def check_if_language_available(self, language):
        if (self.supported_languages_list.get(language) == None):
            return False
        else: 
            return True
    
    def change_output_language(self, output_language):
        if (self.can_change_language_or_not == True):
            if (self.check_if_language_available(output_language) == True):
                self.output_language = output_language
                return f"output language changed to {output_language}"
            else:
                return "sorry, translator doesn't have this language"
        else: 
            return "sorry, this translator can't change languages"

    def change_input_language(self, input_language):
        if (self.can_change_language_or_not == True):
            if (self.check_if_language_available(input_language) == True):
                self.input_language = input_language
                return f"input language changed to {input_language}"
            else:
                return "sorry, translator doesn't have this language"
        else: 
            return "sorry, this translator can't change languages"
    

# sugoi_translator = Sugoi_Translator()
# sugoi_translator.activate()
# print(sugoi_translator.change_input_language("Vietnamese"))
# print(sugoi_translator.translate("たまに閉じているものがあっても、中には何も入っていなかった。"))