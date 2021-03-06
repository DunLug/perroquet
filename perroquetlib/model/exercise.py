# -*- coding: utf-8 -*-

# Copyright (C) 2009-2011 Frédéric Bertolus.
#
# This file is part of Perroquet.
#
# Perroquet is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Perroquet is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Perroquet. If not, see <http://www.gnu.org/licenses/>.

import copy
import hashlib
import random
import re
import string
import os.path

from languages_manager import LanguagesManager
from perroquetlib.config import config
from sub_exercise import SubExercise
from subtitles_loader import SubtitlesLoader

class Exercise(object):

    def __init__(self):
        self.subtitles = SubtitlesLoader()
        self.repeatCount = 0
        self.currentSubExerciseId = 0
        self.subExercisesList = []
        self.currentSubExercise = None
        self.repeatAfterCompleted = True
        self.maxSequenceLength = 60.0
        self.timeBetweenSequence = 0.0
        self.outputSavePath = None
        self.template = False
        self.name = None
        self.mediaChangeCallback = None
        self.language = None
        self.randomOrder = False
        self.playMarginAfter = 500
        self.playMarginBefore = 1000
        self.use_dynamic_correction = True
        self.repeat_count_limit_by_sequence = 0
        self.lock_help = False
        self.lock_properties = False
        self.lock_correction = False
        self.lock_properties_password = None
        self.lock_correction_password = None
        self.lock_properties_salt = None
        self.lock_correction_salt = None

    def initialize(self):
        self.__load_subtitles()
        if self.randomOrder:
            self.order = [x for x in range(self.get_sequence_count())]
            random.shuffle(self.order)
            self.reverseOrder = copy.copy(self.order)
            for i, j in enumerate(self.order):
                self.reverseOrder[j] = i

    def new(self):
        if len(self.subExercisesList) == 0:
            self.currentSubExercise = SubExercise(self)
            self.subExercisesList.append(self.currentSubExercise)
            self.currentSubExerciseId = 0
            self.currentSequenceId = 0
            languageManager = LanguagesManager()
            self.language = languageManager.get_default_language()

            self.maxSequenceLength = float(config.get("default_exercise_max_sequence_length")) / 1000
            self.timeBetweenSequence = float(config.get("default_exercise_time_between_sequences")) / 1000
            self.playMarginAfter = config.get("default_exercise_play_margin_before")
            self.playMarginBefore = config.get("default_exercise_play_margin_after")

            self.repeatAfterCompleted = (config.get("default_exercise_repeat_after_completed") == 1)
            self.randomOrder = (config.get("default_exercise_random_order") == 1)
            self.use_dynamic_correction = (config.get("default_exercise_dynamic_correction") == 1)

            self.set_language_id(config.get("default_exercise_language"))

            self.repeat_count_limit_by_sequence = int(config.get("default_repeat_count_limit_by_sequence"))

    def __load_subtitles(self):

        for subExo in self.subExercisesList:
            subExo.load_subtitles()

    # Reset the work done in the exercise
    def reset(self):
        for sequence in self.get_sequence_list():
            sequence.reset()

    def extract_word_list(self):
        wordList = []

        for subExo in self.subExercisesList:
            wordList = wordList + subExo.extract_word_list()

        #Remove double words and sort
        wordList = list(set(wordList))
        wordList.sort()
        return wordList


    def goto_sequence(self, id):
        self.currentSequenceId = id
        localId = id

        for subExo in self.subExercisesList:
            if localId < len(subExo.get_sequence_list()):
                subExo.set_current_sequence(localId)
                if self.currentSubExercise != subExo:
                    self.currentSubExercise = subExo
                    self.notify_media_change()
                return True
            else:
                localId -= len(subExo.get_sequence_list())


        self.goto_sequence(self.get_sequence_count() - 1)
        return False


    def goto_next_sequence(self):

        if self.randomOrder:
            randomId = self.reverseOrder[self.currentSequenceId]
            randomId += 1
            if randomId >= len(self.order):
                randomId = 0
            return self.goto_sequence(self.order[randomId])
        else:
            return self.goto_sequence(self.currentSequenceId + 1)

    def goto_previous_sequence(self):


        if self.randomOrder:
            randomId = self.reverseOrder[self.currentSequenceId]
            randomId -= 1
            if randomId < 0:
                randomId = len(self.order) - 1
            return self.goto_sequence(self.order[randomId])
        else:
            if self.currentSequenceId > 0:
                return self.goto_sequence(self.currentSequenceId - 1)
            else:
                return False

    def goto_next_valid_sequence(self):
        if not self.goto_next_sequence():
            return False
        else:
            if not self.get_current_sequence().is_valid():
                return True
            else:
                return self.goto_next_valid_sequence()


    def goto_previous_valid_sequence(self):
        if not self.goto_previous_sequence():
            return False
        else:
            if not self.get_current_sequence().is_valid():
                return True
            else:
                return self.goto_previous_valid_sequence()



    def is_paths_valid(self):
        error = False
        errorList = []

        for subExo in self.subExercisesList:
            (valid, subErrorList) = subExo.is_paths_valid()
            if not valid:
                error = True
            errorList = errorList + subErrorList

        return (not error), errorList

    def increment_repeat_count(self):
        self.repeatCount += 1

    def set_video_path(self, videoPath):
        self.currentSubExercise.set_video_path(videoPath)
        if not self.get_name():
            self.set_name(os.path.basename(videoPath))

    def set_exercise_path(self, exercisePath):
        self.currentSubExercise.set_exercise_path(exercisePath)

    def set_translation_path(self, translationPath):
        self.currentSubExercise.set_translation_path(translationPath)

    def get_current_sequence(self):
        return self.currentSubExercise.get_current_sequence()

    def get_previous_sequence(self):

        previousSequenceId = -1

        if self.randomOrder:
            randomId = self.reverseOrder[self.currentSequenceId]
            randomId -= 1
            if randomId < 0:
                randomId = len(self.order) - 1
            previousSequenceId = self.goto_sequence(self.order[randomId])
        else:
            if self.currentSequenceId > 0:
                previousSequenceId = self.currentSequenceId - 1
            else:
                return None

        for subExo in self.subExercisesList:
            if previousSequenceId < len(subExo.get_sequence_list()):
                return subExo.sequenceList[previousSequenceId]
            else:
                previousSequenceId -= len(subExo.get_sequence_list())

    def get_current_sequence_id(self):
        return self.currentSequenceId

    def get_sequence_list(self):
        list = []
        for subExo in self.subExercisesList:
            list += subExo.get_sequence_list()
        return list

    def get_sequence_count(self):
        count = 0
        for subExo in self.subExercisesList:
            count += subExo.get_sequence_count()
        return count

    def set_repeat_count(self, count):
        self.repeatCount = count

    def get_repeat_count(self):
        return self.repeatCount

    def get_video_path(self):
        return self.currentSubExercise.get_video_path()

    def get_exercise_path(self):
        return self.currentSubExercise.get_exercise_path()

    def get_translation_path(self):
        return self.currentSubExercise.get_translation_path()

    def get_translation_list(self):
        return self.currentSubExercise.get_translation_list()

    def set_repeat_after_completed(self, state):
        self.repeatAfterCompleted = state

    def get_repeat_after_completed(self):
        return self.repeatAfterCompleted

    def set_time_between_sequence(self, time):
        self.timeBetweenSequence = time

    def get_time_between_sequence(self):
        return self.timeBetweenSequence

    def set_max_sequence_length(self, time):
        self.maxSequenceLength = time

    def get_max_sequence_length(self):
        return self.maxSequenceLength

    def get_output_save_path(self):
        return self.outputSavePath

    def set_output_save_path(self, outputSavePath):
        self.outputSavePath = outputSavePath
        self.set_template(False)

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def is_template(self):
        return self.template

    def set_template(self, is_template):
        self.template = is_template

    def is_random_order(self):
        return self.randomOrder

    def set_random_order(self, is_random_order):
        self.randomOrder = is_random_order

    def set_media_change_callback(self, mediaChangeCallback):
        self.mediaChangeCallback = mediaChangeCallback

    def notify_media_change(self):
        if self.mediaChangeCallback != None:
            self.mediaChangeCallback()


    def set_language_id(self, langId):
        languageManager = LanguagesManager()
        self.language = languageManager.get_language_by_id(langId)

    def get_language_id(self):
        return self.language.id

    def is_character_match(self, char):
        langAvailableChars = self.language.availableChars
        return re.match('^[' + langAvailableChars + ']$', char)

    def get_play_margin_before(self):
        return self.playMarginBefore

    def set_play_margin_before(self, margin):
        self.playMarginBefore = margin

    def get_play_margin_after(self):
        return self.playMarginAfter

    def set_play_margin_after(self, margin):
        self.playMarginAfter = margin

    def is_use_dynamic_correction(self):
        return self.use_dynamic_correction

    def set_use_dynamic_correction(self, use):
        self.use_dynamic_correction = use

    def set_repeat_count_limit_by_sequence(self, repeat_count_limit):
        self.repeat_count_limit_by_sequence = repeat_count_limit

    def get_repeat_count_limit_by_sequence(self):
        return self.repeat_count_limit_by_sequence

    def is_current_sequence_repeat_limit_reach(self):
        return  self.get_repeat_count_limit_by_sequence() != 0 and self.get_current_sequence().get_repeat_count() >= self.get_repeat_count_limit_by_sequence()

    def increment_current_sequence_repeat_count(self):
        self.get_current_sequence().set_repeat_count(self.get_current_sequence().get_repeat_count() + 1)

    def clear_sequence_repeat_count(self):
        for sequence in self.get_sequence_list():
            sequence.set_repeat_count(0)

    def is_lock_properties(self):
        return self.lock_properties

    def is_lock_properties_password(self):
        return self.lock_properties_salt != None

    def set_lock_properties(self, state, new_password=None):
        self.lock_properties = state
        if new_password is not None:
            salt = ""
            pop = string.hexdigits
            while len(salt) < 6:
                salt += random.choice(pop)

            self.lock_properties_password = self.hash(salt, new_password)
            self.lock_properties_salt = salt
        else:
            self.lock_properties_salt = None
            self.lock_properties_password = None

    def verify_lock_properties_password(self, password):
        return self.lock_properties_password == self.hash(self.lock_properties_salt, password)

    def is_lock_correction(self):
        return self.lock_correction

    def is_lock_correction_password(self):
        return self.lock_correction_salt != None

    def set_lock_correction(self, state, new_password=None):
        self.lock_correction = state
        if new_password is not None:
            salt = ""
            pop = string.hexdigits
            while len(salt) < 6:
                salt += random.choice(pop)

            self.lock_correction_password = self.hash(salt, new_password)
            self.lock_correction_salt = salt
        else:
            self.lock_corrections_salt = None
            self.lock_correction_password = None

    def verify_lock_correction_password(self, password):
        return self.lock_correction_password == self.hash(self.lock_correction_salt, password)

    def hash(self, salt, password):
        """Compute the hashed password for the salt and the password"""
        m = hashlib.sha256()
        m.update(salt + password)
        return m.hexdigest()

    def is_lock_help(self):
        return self.lock_help

    def set_lock_help(self, state):
        self.lock_help = state
