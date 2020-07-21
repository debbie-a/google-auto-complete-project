class AutoCompleteData:
    def __init__(self, sentence, source, offset, score_):
        self.completed_sentence = sentence
        self.source_text = source
        self.offset = offset
        self.score = score_

    def __str__(self):
        return f'{self.completed_sentence} ({self.source_text} {self.offset})'