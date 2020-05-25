PY_FILES=fluxion scripts fluxion.py
CONTRIB_DIR=contrib
DECODERS_DIR=decoders

install_deps:
	python3 -m pip install -r requirements.txt

check:
	@echo "Checking style with autopep8..."
	autopep8 --exit-code --diff -r $(PY_FILES)
	@echo "Running pylint..."
	PYTHONPATH=. pylint -j0 $(PY_FILES) --fail-under=10
	@echo "Running dummy test..."
	./fluxion.py list
	./fluxion.py download dummy
	./fluxion.py run -ts dummy -d H.264Dummy

format:
	autopep8 -i -j0 -r $(PY_FILES)

lint:
	PYTHONPATH=. pylint -j0 $(PY_FILES)

$(CONTRIB_DIR):
	mkdir -p $@

$(DECODERS_DIR):
	mkdir -p $@

h265_reference_decoder: $(CONTRIB_DIR) $(DECODERS_DIR)
	cd $(CONTRIB_DIR) && git clone https://vcgit.hhi.fraunhofer.de/jct-vc/HM.git --depth=1 | true
	cd $(CONTRIB_DIR)/HM && git stash && git pull && git stash apply | true
	cd $(CONTRIB_DIR)/HM && cmake -H. -Bbuild -DCMAKE_BUILD_TYPE=Release && $(MAKE) -C build TAppDecoder
	find $(CONTRIB_DIR)/HM/bin/umake -name "TAppDecoder" -type f -exec cp "{}" $(DECODERS_DIR) \;

h264_reference_decoder: $(CONTRIB_DIR)
	cd $(CONTRIB_DIR) && git clone https://vcgit.hhi.fraunhofer.de/jct-vc/JM.git --depth=1 | true
	cd $(CONTRIB_DIR)/JM && git stash && git pull && git stash apply | true
	cd $(CONTRIB_DIR)/JM && cmake -H. -Bbuild -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS="-Wno-stringop-truncation -Wno-stringop-overflow" && $(MAKE) -C build ldecod
	find $(CONTRIB_DIR)/JM/bin/umake -name "ldecod" -type f -exec cp "{}" $(DECODERS_DIR) \;
