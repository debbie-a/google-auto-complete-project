

class AutoCompleteData:
    root = "technology_texts\\"

    def __init__(self, sentence, source, offset, score_):
        self.completed_sentence = sentence
        self.source_text = source
        self.offset = offset
        self.score = score_

    def __str__(self):
        return f'{self.completed_sentence} ({self.source_text} {self.offset})'

    @staticmethod
    def get_score(word, sentence):
        return len(word) * 2


