PY_FILES=fluster scripts fluster.py
CONTRIB_DIR=contrib
DECODERS_DIR=decoders
PYTHONPATH=.
FLUSTER=python3 ./fluster.py -tsd check
ifeq ($(OS),Windows_NT)
FLUSTER+=--no-emoji
endif

help:
	@awk -F ':|##' '/^[^\t].+?:.*?##/ { printf "\033[36m%-30s\033[0m %s\n", $$1, $$NF }' $(MAKEFILE_LIST)

install_deps: ## install Python dependencies
	python3 -m pip install -r requirements.txt

check: format-check lint ## check that very basic tests run
	@echo "Running dummy test..."
	$(FLUSTER) list
	$(FLUSTER) list -c
	$(FLUSTER) -ne list -c
	$(FLUSTER) list -ts dummy -tv
	$(FLUSTER) download dummy dummy_fail
	$(FLUSTER) run -ts dummy -tv one
	$(FLUSTER) reference Dummy dummy
	$(FLUSTER) run -ts dummy -tv one -j1
	$(FLUSTER) run -ts dummy -s
	$(FLUSTER) -ne run -ts dummy -s
	$(FLUSTER) run -ts dummy -so summary.log && cat summary.log && rm -rf summary.log
	$(FLUSTER) run -ts dummy -j1 -s
	$(FLUSTER) run -ts dummy -th 1
	$(FLUSTER) run -ts dummy -tth 10
ifneq ($(OS),Windows_NT)
	$(FLUSTER) run -ts dummy non_existing_test_suite; test $$? -ne 0
	$(FLUSTER) run -ts dummy -th 2; test $$? -eq 2
	$(FLUSTER) run -ts dummy -tth 0.000000001; test $$? -eq 3
	$(FLUSTER) run -ts dummy_fail -th 1
	$(FLUSTER) run -ts dummy_fail -th 2; test $$? -eq 2
	$(FLUSTER) run -ts dummy_fail -j1 -ff -s; test $$? -ne 0
	$(FLUSTER) download dummy non_existing_test_suite; test $$? -ne 0
	$(FLUSTER) download dummy dummy_download_fail; test $$? -ne 0
endif
	@echo "\nAll test finished succesfully!"

format: ## format Python code using black
	@echo "Formatting coding style with black..."
	black $(PY_FILES)

format-check:
	@echo "Checking coding style with black..."
	black --check $(PY_FILES)

lint: ## run static analysis using pylint
	pylint -j0 $(PY_FILES)

$(CONTRIB_DIR):
	mkdir -p $@

$(DECODERS_DIR):
	mkdir -p $@

decoders: h265_reference_decoder h264_reference_decoder ## build all reference decoders

h265_reference_decoder: $(CONTRIB_DIR) $(DECODERS_DIR) ## build H.265 reference decoder
	cd $(CONTRIB_DIR) && git clone https://vcgit.hhi.fraunhofer.de/jct-vc/HM.git --depth=1 | true
	cd $(CONTRIB_DIR)/HM && git stash && git pull && git stash apply | true
	cd $(CONTRIB_DIR)/HM && cmake -H. -Bbuild -DCMAKE_BUILD_TYPE=Release && $(MAKE) -C build TAppDecoder
	find $(CONTRIB_DIR)/HM/bin/umake -name "TAppDecoder" -type f -exec cp "{}" $(DECODERS_DIR) \;

h264_reference_decoder: $(CONTRIB_DIR) ## build H.264 reference decoder
	cd $(CONTRIB_DIR) && git clone https://vcgit.hhi.fraunhofer.de/jct-vc/JM.git --depth=1 | true
	cd $(CONTRIB_DIR)/JM && git stash && git pull && git stash apply | true
	cd $(CONTRIB_DIR)/JM && cmake -H. -Bbuild -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS="-Wno-stringop-truncation -Wno-stringop-overflow" && $(MAKE) -C build ldecod
	find $(CONTRIB_DIR)/JM/bin/umake -name "ldecod" -type f -exec cp "{}" $(DECODERS_DIR) \;

dbg-%:
	echo "Value of $* = $($*)"

.PHONY: help decoders h264_reference_decoder h265_reference_decoder lint check format install_deps
