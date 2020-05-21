import os
import os.path
import json
import functools

from fluxion.test_suite import TestSuite
from fluxion.test_vector import TestVector
from fluxion.decoder import DECODERS


def lazy_init(call_func):
    def decorator_lazy_init(func):
        @functools.wraps(func)
        def func_wrapper(self, *args, **kwargs):
            if not call_func:
                raise Exception(
                    'A function needs to be given to the lazy_init decorator')
            flag_name = call_func.__name__ + '_already_called'
            if not hasattr(self, flag_name):
                self.flag_name = False
            if not self.flag_name:
                call_func(self)
            self.flag_name = True
            func(self, *args, **kwargs)
        return func_wrapper
    return decorator_lazy_init


class Fluxion:
    def __init__(self, test_suites_dir, decoders_dir, verbose=False):
        self.test_suites_dir = test_suites_dir
        self.decoders_dir = decoders_dir
        self.verbose = verbose
        self.test_suites = []
        self.decoders = DECODERS

    def load_decoders(self):
        for root, _, files in os.walk(self.decoders_dir):
            for file in files:
                if os.path.splitext(file)[1] == '.py':
                    if self.verbose:
                        print(f'Decoder found: {file}')
                    try:
                        exec(open(os.path.join(root, file)).read(), globals())
                    except Exception as e:
                        print(f'Error loading decoder {file}: {e}')

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
                                content[TestSuite.NAME], content[TestSuite.CODEC], content[TestSuite.DESCRIPTION])
                            for tv in content[TestSuite.TEST_VECTORS]:
                                result_frames = None if not TestVector.RESULT_FRAMES in tv else tv[
                                    TestVector.RESULT_FRAMES]
                                test_suite.add_test_vector(TestVector(
                                    tv[TestVector.NAME], tv[TestVector.SOURCE], tv[TestVector.INPUT], tv[TestVector.RESULT], result_frames))
                            self.test_suites.append(test_suite)
                    except Exception as e:
                        print(f'Error loading test suite {file}: {e}')

    @lazy_init(load_decoders)
    def list_decoders(self):
        print('List of available decoders:')
        for codec in self.decoders.keys():
            print(f'  {codec}')
            for decoder in self.decoders[codec]:
                print(decoder)

    @lazy_init(load_test_suites)
    def list_test_suites(self, show_test_vectors=False):
        print('List of available test suites:')
        for ts in self.test_suites:
            print(ts)
            if show_test_vectors:
                for tv in ts.test_vectors:
                    print(tv)
