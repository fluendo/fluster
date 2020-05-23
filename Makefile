PY_FILES=fluxion decoders scripts fluxion.py

check:
	echo "Checking style with autopep8..."
	autopep8 --exit-code --diff -r $(PY_FILES)
	echo "Running pylint..."
	PYTHONPATH=. pylint $(PY_FILES) --fail-under=10
	echo "Running dummy test..."
	./fluxion.py run -ts dummy

format:
	autopep8 -j4 -i -r fluxion decoders scripts

lint:
	PYTHONPATH=. pylint $(PY_FILES)

h265_reference_decoder:
	git clone https://vcgit.hhi.fraunhofer.de/jct-vc/HM.git | true
	cd HM && git pull
	cd HM && cmake .
	cd HM %% make TAppDecoder -j
	find HM/bin/* -name 'TAppDecoder' -exec cp "{}" HM/bin/  \;