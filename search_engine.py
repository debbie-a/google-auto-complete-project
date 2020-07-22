import os
from collections import defaultdict
import re
from auto_complete_data import AutoCompleteData


def clean_string(string_):
    pattern = re.compile('[^A-Za-z0-9 -]')
    string_ = pattern.sub('', string_)
    return " ".join(string_.split()).lower()


def remove_lowest_score(list_):
    list_.sort(key=lambda x: x.completed_sentence, reverse=True)
    min_score = min(list_, key=lambda x: x.score)
    list_.remove(min_score)


def get_files():
    path = f'{AutoCompleteData.root}collection'
    file_list = []
    for root, dirs, files in os.walk(path):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list


def read_data_from_file(file):
    my_file = open(file, encoding="utf8")
    data = my_file.read().split("\n")
    my_file.close()

    return data


def init_data_collection(data_collection):
    print("Loading the files and preparing the system...")
    files = get_files()

    for file in files:
        source = file[file.index("\\") + 1: file.index(".")]
        data = read_data_from_file(file)

        for i, sentence in enumerate(data, 1):
            sentence_ = clean_string(sentence[::])

            for key in [sentence_[i: j] for i in range(len(sentence_)) for j in range(i + 1, len(sentence_) + 1)]:
                data_collection[key] += [AutoCompleteData(sentence, source, i, AutoCompleteData.get_score(key, sentence))]
                data_collection[key] = list(dict.fromkeys(data_collection[key]))

                if len(data_collection[key]) > 5:
                    remove_lowest_score(data_collection[key])


def get_best_k_completions(prefix, data_collection):
    return data_collection[prefix]


def read_input_from_user(message):
    return input(message)


def run():
    STOP_INPUT = '#'
    data_collection = defaultdict(list)
    init_data_collection(data_collection)

    while True:
        string_to_complete = read_input_from_user("The system is ready. Enter your text:\n")

        while string_to_complete[len(string_to_complete) - 1] != STOP_INPUT:
            search_result = get_best_k_completions(clean_string(string_to_complete), data_collection)
            if search_result:
                print(f'Here are {len(search_result)} suggestions') if len(search_result) > 1 else print("Here is 1 "
                                                                                                         "suggestion")
                for i, res in enumerate(search_result, 1):
                    print(f'{i}. {res}')

                # let user continue his search
                string_to_complete += read_input_from_user(f"\u001b[38;5;28m\x1B[3m{string_to_complete}\033[0m")

            else:
                break
