import os


class Fluxion:
    def __init__(self, test_suites_dir, verbose=False):
        self.test_suites_dir = test_suites_dir
        self.test_suites = []
        self.codecs = []
        self.load_test_suites()
        self.verbose = verbose

    def load_test_suites(self):
        for root, dirs, files in os.walk(self.test_suites_dir):
            for file in files:
                if file.splittext(file)[1] == '.json':
                    if self.verbose:
                        print(f'Test suite found: {file}')
