class TestVector:
    NAME = 'name'
    SOURCE = 'source'
    INPUT = 'input'
    RESULT = 'result'
    RESULT_FRAMES = 'result_frames'

    def __init__(self, name, source, input, result, result_frames=None):
        self.name = name
        self.source = source
        self.input = input
        self.result = result
        self.result_frames = result_frames

    def __str__(self):
        ret = f'    {self.name}\n' \
            f'        Source: {self.source}\n' \
            f'        Input: {self.input}\n' \
            f'        Result: {self.result}'
        if self.result_frames:
            ret += f'\n        Result frames: {", ".join(self.result_frames)}'
        return  ret
