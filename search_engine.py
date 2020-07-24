import json
import linecache
import os
import string
from collections import defaultdict
import re
from string import ascii_lowercase, digits
from itertools import groupby

from auto_complete_data import AutoCompleteData

K = 5
LENGTH_LIMIT = 10
JSON = "JSON"


def clean_string(string_):
    string_ = string_.translate(string_.maketrans("", "", string.punctuation + "•" + "◊" + "é" + "◆" + "" + "©"))
    return re.sub(' +', ' ', string_).lower().strip()


def get_files(file_dict):
    # root
    path = f'{AutoCompleteData.root}'

    # add every path to hash map
    for root, dirs, files in os.walk(path):
        for i, file in enumerate(files):
            file_dict[i] = os.path.join(root, file)


def read_data_from_file(file):
    my_file = open(file, encoding="utf8")
    data = my_file.read().split("\n")
    my_file.close()

    return data


def load_data_from_files(file_dict, prefix):
    if prefix.strip():
        with open(f"{JSON}/{prefix[0]}.json", encoding='utf-8') as data_file:
            data_collection = json.load(data_file)

    data = {}
    list_ = data_collection.get(prefix, None)
    if list_:
        for pair in list_:
            # load autocomplete objects into dict from file data
            sentence = linecache.getline(file_dict[pair[0]], pair[1])[:-1]
            data['*'.join(map(str, pair))] = AutoCompleteData(sentence,
                                                              file_dict[pair[0]][:file_dict[pair[0]].index(".")],
                                                              pair[1], pair[2])
    return data


def who_to_remove(list_):
    list_.sort(key=lambda x: x.completed_sentence, reverse=True)
    return min(list_, key=lambda x: x.score)


def remove_lowest_score(list_, file_dict, prefix):
    data = load_data_from_files(file_dict, prefix)
    tmp_list = []

    for val in data.values():
        tmp_list.append(val)

    min_score = who_to_remove(tmp_list)
    pair_to_remove = list(data.keys())[list(data.values()).index(min_score)]
    list_.remove(list(map(int, pair_to_remove.split("*"))))

    del tmp_list


def remove_duplicate_lists_from_list(list_to_remove_duplicates):
    tmp = []
    tmp_list = []
    for list_ in list_to_remove_duplicates:
        if list_ not in tmp and list_[:-1] not in tmp_list:
            tmp_list.append(list_[:-1])
            tmp.append(list_)

    del list_to_remove_duplicates, tmp_list
    return tmp


def get_all_string_sub_strings(sentence_):
    return [sentence_[i: j] for i in range(min(len(sentence_), LENGTH_LIMIT)) for j in range(i + 1, len(sentence_) + 1)]


def get_most_completions(substring):
    CHAR_LIST = list(ascii_lowercase) + list(digits)
    FULL_SCORE = 2
    SCORING_FOR_REMOVE = [10, 8, 6, 4, 2]
    SCORING_FOR_ADD_AND_REPLACE = [5, 4, 3, 2, 1]

    list_ = [[substring, len(substring) * FULL_SCORE]]
    for i in range(1, len(substring)):
        score_to_remove = SCORING_FOR_REMOVE[i] if i < len(SCORING_FOR_REMOVE) else SCORING_FOR_REMOVE[-1]
        list_.append([substring[:i] + substring[i + 1:], (len(substring) - 1) * FULL_SCORE - score_to_remove])
        for char in CHAR_LIST:
            score_to_remove = SCORING_FOR_ADD_AND_REPLACE[i] if i < len(SCORING_FOR_ADD_AND_REPLACE) else \
                SCORING_FOR_ADD_AND_REPLACE[-1]
            list_.append(
                [substring[:i] + str(char) + substring[i + 1:], ((len(substring) - 1) * FULL_SCORE) - score_to_remove])
            list_.append(
                [substring[:i] + str(char) + substring[i:], ((len(substring) - 1) * FULL_SCORE) - score_to_remove])
            list_.append([substring + char, ((len(substring) - 1) * FULL_SCORE) - score_to_remove])
    return list_


def get_rest_completions(substring):
    CHAR_LIST = list(ascii_lowercase) + list(digits)
    list_ = []
    FULL_SCORE = 2
    SCORING_FOR_ADD_AND_REPLACE_FIRST = 5
    for char in CHAR_LIST:
        list_.append([str(char) + substring[1:], (len(substring) - 1) * FULL_SCORE - SCORING_FOR_ADD_AND_REPLACE_FIRST])
        list_.append([str(char) + substring, (len(substring) - 1) * FULL_SCORE - SCORING_FOR_ADD_AND_REPLACE_FIRST])
    res = list(list(ele) for i, ele in groupby(sorted(list_, key=lambda x: x[0][0]), lambda x: x[0][0]))
    return res


def read_dict_from_json(letter):
    with open(f"{JSON}/{letter}.json", encoding='utf-8') as data_file:
        data_collection = json.load(data_file)

    return data_collection


def write_dict_to_json_file(data_collection, letter):
    with open(f"{JSON}/{letter}.json", "w", encoding='utf-8') as json_file:
        json.dump(data_collection, json_file)


def init_data_collection(file_dict):
    print("Loading the files and preparing the system...")

    # get all paths of files from where we need to store data from and init file hash map
    get_files(file_dict)

    # for each file read data:
    for key_, file in file_dict.items():
        file_id = key_
        data = read_data_from_file(file)

        # taking care of each line of data
        for file_line, sentence in enumerate(data, 1):
            sentence = clean_string(sentence)
            if sentence.strip():
                # most of substring's completions (all the ones that start with same letter as substring)
                for substring in get_all_string_sub_strings(sentence[:LENGTH_LIMIT]):
                    substring = \
                        substring.strip()
                    if substring:
                        data_collection = read_dict_from_json(substring[0])

                        for list_ in get_most_completions(substring):
                            sub = list_[0]
                            if sub in data_collection:
                                data_collection[sub] += [[file_id, file_line, list_[1]]]
                            else:
                                data_collection.update({sub: [[file_id, file_line, list_[1]]]})

                            # remove duplicate matches (remove lower scores)
                            data_collection[sub] = remove_duplicate_lists_from_list(data_collection[sub])

                            # if a substring has more than k matches, take care...
                            if len(data_collection[sub]) > K:
                                remove_lowest_score(data_collection[sub], file_dict, sub)

                        write_dict_to_json_file(data_collection, substring[0])

                        # add rest of completions
                        for list_ in get_rest_completions(substring):
                            if os.path.getsize(f"{JSON}/{list_[0][0][0]}.json") > 2:
                                data_collection = read_dict_from_json(list_[0][0][0])

                                for sub_ in list_:
                                    if sub_[0] in data_collection.keys():
                                        data_collection[sub_[0]] += [[file_id, file_line, sub_[1]]]
                                    else:
                                        data_collection.update({sub_[0]: [[file_id, file_line, sub_[1]]]})

                                    data_collection[sub_[0]] = remove_duplicate_lists_from_list(
                                        data_collection[sub_[0]])

                                    # remove duplicate matches (remove lower scores)
                                    data_collection[sub_[0]] = remove_duplicate_lists_from_list(
                                        data_collection[sub_[0]])

                                    # if a substring has more than k matches, take care...
                                    if len(data_collection[sub_[0]]) > K:
                                        remove_lowest_score(data_collection[sub_[0]], file_dict, sub_[0])

                            write_dict_to_json_file(data_collection, list_[0][0][0])


def get_best_k_completions(file_dict, prefix):
    dict_of_auto_completes = load_data_from_files(file_dict, prefix)
    return list(dict_of_auto_completes.values())


def offline(file_dict):
    # initialize the data structure (hash map)
    init_data_collection(file_dict)


def online(file_dict, string_to_complete):
    # get best k completions
    return get_best_k_completions(file_dict, clean_string(string_to_complete))


def read_input_from_user(message):
    input_ = input(message)
    for i in input_[:LENGTH_LIMIT]:

        # if input is not in english... (this system supports only english searches..)
        if i not in list(ascii_lowercase) + list(digits) + list(string.punctuation):
            return "#"
    return input_


def init_json_files():
    CHAR_LIST = list(ascii_lowercase) + list(digits)
    for letter in CHAR_LIST:
        d = defaultdict(list)
        with open(f"{JSON}/{letter}.json", 'w+', encoding='utf-8') as f:
            json.dump(d, f)


def run():
    init_json_files()
    file_dict = {}

    # offline
    offline(file_dict)

    # online
    STOP_INPUT = '#'
    PRINT_GREEN = "\u001b[38;5;28m\x1B[3m"
    RESET_COLOR = "\033[0m"

    while True:
        string_to_complete = read_input_from_user("The system is ready. Enter your text:\n")

        while string_to_complete[len(string_to_complete) - 1] != STOP_INPUT:

            search_result = online(file_dict, string_to_complete)

            if search_result:
                print(f'Here are {len(search_result)} suggestions') if len(search_result) > 1 else print("Here is 1 "
                                                                                                         "suggestion")
                for i, res in enumerate(search_result, 1):
                    print(f'{i}. {res}')

                # let user continue his search
                string_to_complete += read_input_from_user(f'{PRINT_GREEN}{string_to_complete}{RESET_COLOR}')

            else:
                break
