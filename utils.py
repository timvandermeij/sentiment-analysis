import json
import re

class Utilities(object):
    COLORS = {1: '\033[1;32m', -1: '\033[1;31m', 0: '\033[1m', 'head': '\033[1;36m', 'end': '\033[0m'}
    WORD_SPLIT = r'"|(?:(?<=[a-z])[;\.])?\s+|(?:(?<=[a-z])[;\.])?$|(?!.[/(]\S)([^;\.\-\"\'+\w\s][^+\w\s]*(?:[-a-z]\b)?)|(?!.[/(]\S)((?:\b[a-z])?[^+\w\s]*[^;\.\-\"\'+\w\s])'

    @classmethod
    def split(cls, message):
        # Only keep alphanumeric and some punctuation characters
        # Keep emoticons together but beware of edge cases that should be split
        return filter(lambda x: x != '' and x is not None, re.split(cls.WORD_SPLIT, message.lower()))

    @classmethod
    def get_colored_text(cls, c, text=None):
        if text is None:
            text = cls.score_to_label(c)

        if c != 'head':
            if type(c) == str:
                c = cls.label_to_score(c)
            if c is None:
                c = 0

            c = cmp(c, 0)

        b = cls.COLORS[c] if c in cls.COLORS else cls.COLORS[0]
        return b + str(text) + cls.COLORS['end']

    @classmethod
    def score_to_label(cls, score):
        if score < 0:
            return 'negative'
        elif score > 0:
            return 'positive'
        elif score == 0:
            return 'neutral'

        return 'unknown'

    @classmethod
    def label_to_score(cls, label):
        if label == "positive":
            return 1.0
        elif label == "negative":
            return -1.0
        elif label == "neutral":
            return 0.0

        return None

    @classmethod
    def convert_keep_fields(cls, keep_fields, group):
        if type(keep_fields) == list:
            keep_fields = dict([(k,k) for k in keep_fields])
        elif type(keep_fields) != dict:
            k = {"message": "body"}
            if type(keep_fields) == str:
                k[keep_fields] = keep_fields
            if group != "score":
                k["group"] = group

            keep_fields = k

        return keep_fields

    @classmethod
    def filter_fields(cls, data, keep_fields):
        # Rename the fields and filter
        fields = {}
        for new,old in keep_fields.iteritems():
            fields[new] = data[old]

        return fields

    @classmethod
    def read_json(cls, file, keep_fields=True, group="score"):
        keep_fields = cls.convert_keep_fields(keep_fields, group)

        i = 0
        for jsonObject in file:
            try:
                # Allow control characters which are sometimes in the strings.
                data = json.loads(jsonObject, strict=False)
            except ValueError as e:
                raise(ValueError("Incorrect JSON string: '{}' with error '{}'".format(jsonObject, e)))

            # Normalize newlines
            if "body" in data:
                data["body"] = data["body"].replace('\r\n', '\n')

            fields = cls.filter_fields(data, keep_fields)

            yield fields
            i = i + 1

    @classmethod
    def write_json(cls, filename, json_object, keep_fields=True):
        keep_fields = cls.convert_keep_fields(keep_fields, "id")
        json_object = Utilities.filter_fields(json_object, keep_fields)

        output = open(filename, 'a')
        output.write(json.dumps(json_object) + '\n')
        output.close()
