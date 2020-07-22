import itertools
import os
from collections import defaultdict
import re
from auto_complete_data import AutoCompleteData


def clean_string(string_):
    pattern = re.compile('[^A-Za-z0-9 -]')
    string_ = pattern.sub('', string_)
    return " ".join(string_.split()).lower()


def get_files(file_dict):
    path = f'{AutoCompleteData.root}'

    for root, dirs, files in os.walk(path):
        for i, file in enumerate(files):
            file_dict[i] = os.path.join(root, file)


def read_data_from_file(file):
    my_file = open(file, encoding="utf8")
    data = my_file.read().split("\n")
    my_file.close()
    return data


def load_data_from_files(list_, file_dict, prefix):
    data = {}
    for pair in list_:
        sentence = read_data_from_file(file_dict[pair[0]])[pair[1] - 1]
        data['*'.join(map(str, pair))] = AutoCompleteData(sentence, file_dict[pair[0]][:file_dict[pair[0]].index(".")], pair[1], AutoCompleteData.get_score(prefix, sentence))
    return data


def remove_lowest_score(list_, file_dict, prefix):
    data = load_data_from_files(list_, file_dict, prefix)
    tmp_list = []
    for val in data.values():
        tmp_list.append(val)
    tmp_list.sort(key=lambda x: x.completed_sentence, reverse=True)
    min_score = min(tmp_list, key=lambda x: x.score)
    pair_to_remove = list(data.keys())[list(data.values()).index(min_score)]
    list_.remove(list(map(int, pair_to_remove.split("*"))))


def init_data_collection(data_collection, file_dict):
    print("Loading the files and preparing the system...")
    get_files(file_dict)

    for key_, file in file_dict.items():
        file_id = key_
        data = read_data_from_file(file)

        for file_line, sentence in enumerate(data, 1):
            sentence_ = clean_string(sentence[::])

            for key in [sentence_[i: j] for i in range(len(sentence_)) for j in range(i + 1, len(sentence_) + 1)]:

                data_collection[key] += [[file_id, file_line]]
                tmp = []
                for list_ in data_collection[key]:
                    if list_ not in tmp:
                        tmp.append(list_)

                data_collection[key] = tmp

                if len(data_collection[key]) > 5:
                    remove_lowest_score(data_collection[key], file_dict, key)


def get_best_k_completions(prefix, data_collection, file_dict):
    auto_completes = load_data_from_files(data_collection[prefix], file_dict, prefix)
    return list(auto_completes.values())


def read_input_from_user(message):
    return input(message)


def run():
    STOP_INPUT = '#'
    data_collection = defaultdict(list)
    file_dict = {}
    init_data_collection(data_collection, file_dict)
    while True:
        string_to_complete = read_input_from_user("The system is ready. Enter your text:\n")

        while string_to_complete[len(string_to_complete) - 1] != STOP_INPUT:
            search_result = get_best_k_completions(clean_string(string_to_complete), data_collection, file_dict)
            if search_result:
                print(f'Here are {len(search_result)} suggestions') if len(search_result) > 1 else print("Here is 1 "
                                                                                                         "suggestion")
                for i, res in enumerate(search_result, 1):
                    print(f'{i}. {res}')

                # let user continue his search
                string_to_complete += read_input_from_user(f"\u001b[38;5;28m\x1B[3m{string_to_complete}\033[0m")

            else:
                break
