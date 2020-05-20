class TestSuite:
    def __init__(self, name, codec, description):
        self.name = name
        self.codec = codec
        self.description = description
        self.test_vectors = []

    def add_test_vector(self, test_vector):
        self.test_vectors.append(test_vector)
