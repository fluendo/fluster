import os
import os.path
import json

from fluxion.test_suite import TestSuite
from fluxion.test_vector import TestVector


class Fluxion:
    def __init__(self, test_suites_dir, verbose=False):
        self.test_suites_dir = test_suites_dir
        self.verbose = verbose
        self.test_suites = []
        self.codecs = []
        self.load_test_suites()

    def load_test_suites(self):
        for root, _, files in os.walk(self.test_suites_dir):
            for file in files:
                if os.path.splitext(file)[1] == '.json':
                    if self.verbose:
                        print(f'Test suite found: {file}')
                    try:
                        with open(os.path.join(root, file)) as f:
                            content = json.load(f)
                            test_suite = TestSuite(
                                content['name'], content['codec'], content['description'])
                            for tv in content['test_vectors']:
                                test_suite.add_test_vector(TestVector(
                                    tv['name'], tv['source'], tv['input'], tv['result']))
                            self.test_suites.append(test_suite)
                    except Exception:
                        print(f'Error loading test suite {file}')
