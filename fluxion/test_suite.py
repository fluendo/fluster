class TestSuite:
    NAME = 'name'
    CODEC = 'codec'
    DESCRIPTION = 'description'
    TEST_VECTORS = 'test_vectors'

    def __init__(self, name, codec, description):
        self.name = name
        self.codec = codec
        self.description = description
        self.test_vectors = []

    def add_test_vector(self, test_vector):
        self.test_vectors.append(test_vector)

    def __str__(self):
        return f'\n{self.name}\n' \
            f'  Codec: {self.codec}\n' \
            f'  Description: {self.description}\n' \
            f'  Test vectors: {len(self.test_vectors)}'
