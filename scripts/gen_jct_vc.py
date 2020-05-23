import hashlib
from html.parser import HTMLParser
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from fluxion import utils
from fluxion.test_suite import TestSuite, TestVector

JCT_VT_SITE_BASE_URL = "https://www.itu.int/"
JCT_VT_SITE_URL = JCT_VT_SITE_BASE_URL + \
    "wftp3/av-arch/jctvc-site/bitstream_exchange/draft_conformance/"


class HREFParser(HTMLParser):
    links = []

    def handle_starttag(self, tag, attrs):
        # Only parse the 'anchor' tag.
        if tag == "a":
            # Check the list of defined attributes.
            for name, value in attrs:
                # If href is defined, print it.
                if name == "href":
                    self.links.append(JCT_VT_SITE_BASE_URL + value)


class JCTVTGenerator:

    def __init__(self, name, suite_name, codec, description):
        self.name = name
        self.suite_name = suite_name
        self.codec = codec
        self.description = description

    def generate(self):
        test_suite = TestSuite(
            self.suite_name, self.codec, self.description, list())

        parser = HREFParser()
        with urllib.request.urlopen(JCT_VT_SITE_URL + self.name) as resp:
            data = str(resp.read())
            parser.feed(data)

        for url in parser.links[1:]:
            f = url.split('/')[-1]
            name = f.split('.')[0]
            file_input = "{name}.bin".format(name=name)
            test_vector = TestVector(name, url, "", file_input, "")
            test_suite.test_vectors.append(test_vector)

        test_suite.download('resources', verify=False)

        for test_vector in test_suite.test_vectors:
            dest_dir = os.path.join(
                'resources', test_suite.name, test_vector.name)
            dest_path = os.path.join(
                dest_dir, test_vector.source.split('/')[-1])
            test_vector.input = self._find_input(dest_dir)
            test_vector.source_hash = utils.file_checksum(dest_path)
            test_vector.result = utils.file_checksum(test_vector.input)

        test_suite.to_json_file(os.path.join(test_suite.name + '.json'))
        print("Generate new test suite: " + test_suite.name + '.json')

    def _find_input(self, dest_dir):
        for subdir, _, files in os.walk(dest_dir):
            for filename in files:
                filepath = subdir + os.sep + filename
                if filepath.endswith(".bin") or filepath.endswith(".bit"):
                    return filepath


if __name__ == "__main__":
    generator = JCTVTGenerator("HEVC_v1", "JCT-VC-HEVC_V1", "H.265",
                               "JCT-VC HEVC version 1")
    generator.generate()
