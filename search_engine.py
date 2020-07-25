import linecache
import os
import string
from collections import defaultdict
import re
from itertools import groupby
from string import ascii_lowercase, digits

from auto_complete_data import AutoCompleteData

K = 5
LENGTH_LIMIT = 10


def clean_string(string_):
    string_ = string_.translate(string_.maketrans("", "", string.punctuation))

    return re.sub(' +', ' ', string_).lower().strip()


def get_files(file_dict):
    # root
    path = f'{AutoCompleteData.root}'

    # add every path to hash map
    for root, dirs, files in os.walk(path):
        for i, file in enumerate(files):
            file_dict[i] = os.path.join(root, file)


def load_data_from_files(list_, file_dict, prefix):
    data = {}
    for pair in list_:
        # load autocomplete objects into dict from file data
        sentence = linecache.getline(file_dict[pair[0]], pair[1])[:-1]
        data['*'.join(map(str, pair))] = AutoCompleteData(sentence, file_dict[pair[0]][:file_dict[pair[0]].index(".")],
                                                          pair[1], AutoCompleteData.get_score(prefix, sentence))
    return data


def who_to_remove(list_):
    list_.sort(key=lambda x: x.completed_sentence, reverse=True)
    return min(list_, key=lambda x: x.score)


def remove_lowest_score(list_, file_dict, prefix):
    data = load_data_from_files(list_, file_dict, prefix)
    tmp_list = []

    for val in data.values():
        tmp_list.append(val)

    min_score = who_to_remove(tmp_list)
    pair_to_remove = list(data.keys())[list(data.values()).index(min_score)]
    list_.remove(list(map(int, pair_to_remove.split("*"))))

    del tmp_list


def remove_duplicate_lists_from_list(list_to_remove_duplicates):
    tmp = []
    for list_ in list_to_remove_duplicates:
        if list_ not in tmp:
            tmp.append(list_)

    del list_to_remove_duplicates
    return tmp


def get_all_string_sub_strings(sentence_):
    return [sentence_[i: j] for i in range(min(len(sentence_), LENGTH_LIMIT)) for j in range(i + 1, len(sentence_) + 1)]


def is_eof(f):
    cur = f.tell()  # save current position
    f.seek(0, os.SEEK_END)
    end = f.tell()  # find the size of file
    f.seek(cur, os.SEEK_SET)
    return cur == end


def init_data_collection(data_collection, file_dict):
    print("Loading the files and preparing the system...")

    # get all paths of files from where we need to store data from and init file hash map
    get_files(file_dict)

    # for each file read data
    for key_, file in file_dict.items():
        file_id = key_
        f = open(file, "r", encoding="utf8")
        file_line = 0
        while not is_eof(f):
            line = f.readline()
            file_line += 1
            sentence_ = clean_string(line[::])
            if sentence_.strip():
                for substring in get_all_string_sub_strings(sentence_):
                    data_collection[substring] += [[file_id, file_line]]
                    data_collection[substring] = remove_duplicate_lists_from_list(data_collection[substring])

                    # if a substring has more than k matches, take care...
                    if len(data_collection[substring]) > K:
                        remove_lowest_score(data_collection[substring], file_dict, substring)
        f.close()


def remove_duplicate_objects_from_list(list_):
    list_.sort(key=lambda x: x.score, reverse=True)
    list2 = []
    flag = True
    for obj1 in list_:
        for obj2 in list2:
            if obj1.completed_sentence == obj2.completed_sentence and obj1.source_text == obj2.source_text:
                flag = False
                break
        if flag:
            list2.append(obj1)
    return list2


def add_letter_to_match(data_collection, file_dict, prefix, i):
    SCORING = [5, 4, 3, 2, 1]

    tmp = get_best_k_completions(data_collection, file_dict, prefix)
    tmp = remove_duplicate_objects_from_list(tmp)
    for object_ in tmp:
        object_.set_score(SCORING[i] if i < len(SCORING) else SCORING[-1])
    return tmp


def remove_letter_to_match(data_collection, file_dict, prefix, i):
    SCORING = [10, 8, 6, 4, 2]

    tmp = get_best_k_completions(data_collection, file_dict, prefix)
    tmp = remove_duplicate_objects_from_list(tmp)
    for object_ in tmp:
        object_.set_score(SCORING[i] if i < len(SCORING) else SCORING[-1])
    return tmp


def change_letter_to_match(data_collection, file_dict, prefix, i):
    SCORING = [5, 4, 3, 2, 1]

    tmp = get_best_k_completions(data_collection, file_dict, prefix)
    tmp = remove_duplicate_objects_from_list(tmp)
    for object_ in tmp:
        object_.set_score(SCORING[i] if i < len(SCORING) else SCORING[-1])
    return tmp


def complete_word(data_collection, file_dict, prefix, search_result):
    CHAR_LIST = list(ascii_lowercase) + list(digits)

    for i in range(len(prefix)):

        # remove one letter to match a completion
        if prefix[:i] + prefix[i + 1:] in list(data_collection.keys()):
            search_result += remove_letter_to_match(data_collection, file_dict, prefix[:i] + prefix[i + 1:], i)

            while len(search_result) > K:
                search_result.remove(who_to_remove(search_result))

        for char_ in CHAR_LIST:

            # change one letter to match a completion
            if prefix[:i] + char_ + prefix[i + 1:] in list(data_collection.keys()):
                search_result += change_letter_to_match(data_collection, file_dict, prefix[:i] + prefix[i + 1:], i)

                while len(search_result) > K:
                    search_result.remove(who_to_remove(search_result))

            # add one letter to match a completion
            if prefix[:i] + char_ + prefix[i:] in list(data_collection.keys()):
                search_result += add_letter_to_match(data_collection, file_dict, prefix[:i] + char_ + prefix[i:], i)

                while len(search_result) > K:
                    search_result.remove(who_to_remove(search_result))

    # just in case...
    while len(search_result) > K:
        search_result.remove(who_to_remove(search_result))

    search_result = remove_duplicate_objects_from_list(search_result)

    return search_result


def get_best_k_completions(data_collection, file_dict, prefix):
    list_of_auto_completes = load_data_from_files(data_collection[prefix], file_dict, prefix)
    return list(list_of_auto_completes.values())


def offline(data_collection, file_dict):
    # initialize the data structure (hash map)
    init_data_collection(data_collection, file_dict)


def online(data_collection, file_dict, string_to_complete):
    # get best k completions
    search_result = get_best_k_completions(data_collection, file_dict, clean_string(string_to_complete))

    # found - return to user...
    if len(search_result) == K:
        return search_result

    # try to find similar completions to match search
    else:
        return complete_word(data_collection, file_dict, string_to_complete, search_result)


def read_input_from_user(message):
    return input(message)


def run():
    data_collection = defaultdict(list)
    file_dict = {}

    # offline
    offline(data_collection, file_dict)

    # online
    STOP_INPUT = '#'
    PRINT_GREEN = "\u001b[38;5;28m\x1B[3m"
    RESET_COLOR = "\033[0m"
    PRINT_ITALLIC = "\x1B[3m"

    while True:
        string_to_complete = read_input_from_user("The system is ready. Enter your text:\n")

        while string_to_complete[len(string_to_complete) - 1] != STOP_INPUT:

            search_result = online(data_collection, file_dict, string_to_complete)

            if search_result:
                print(f'Here are {len(search_result)} suggestions') if len(search_result) > 1 else print("Here is 1 "
                                                                                                         "suggestion")
                for i, res in enumerate(search_result, 1):
                    print(f'{i}. {res}')

                # let user continue his search
                string_to_complete += read_input_from_user(
                    f"{PRINT_GREEN}{PRINT_ITALLIC}{string_to_complete}{RESET_COLOR}")

            else:
                break
