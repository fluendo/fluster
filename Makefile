PY_FILES=fluster
CONTRIB_DIR=contrib
DECODERS_DIR=decoders
PYTHONPATH=.
FLUSTER=python3 ./fluster.py -tsd check
ifeq ($(OS),Windows_NT)
FLUSTER+=--no-emoji
else
KERNEL_NAME=$(shell uname -s)
endif
CMAKE_GENERATOR=Unix Makefiles

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
	$(FLUSTER) download dummy dummy_fail -k
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
	$(FLUSTER) download dummy non_existing_test_suite -k; test $$? -ne 0
	$(FLUSTER) download dummy dummy_download_fail -k; test $$? -ne 0
	$(FLUSTER) download H264-min H265-min VP8-min VP9-min -k
	$(FLUSTER) run -ts H264-min -d GStreamer-H.264-Libav-Gst1.0 FFmpeg-H.264 -s
	$(FLUSTER) run -ts H265-min -d GStreamer-H.265-Libav-Gst1.0 FFmpeg-H.265 -s
	$(FLUSTER) run -ts VP8-min -d libvpx-VP8 -s
	$(FLUSTER) run -ts VP9-min -d libvpx-VP9 -s
endif
	@echo "\nAll test finished succesfully!"

format: ## format Python code using black
	@echo "Formatting coding style with black..."
	black $(PY_FILES)

format-check:
	@echo "Checking coding style with black... Run '$(MAKE) format' to fix if needed"
	black --check $(PY_FILES)

lint: format-check ## run static analysis using pylint, flake8 and mypy
# ignore similar lines error: it's a bug when running parallel jobs - https://github.com/PyCQA/pylint/issues/4118
	@echo "Checking with pylint... "
	pylint --fail-under=10.0 $(PY_FILES)
	@echo "Checking with flake8..."
	flake8 --max-line-length=120 $(PY_FILES)
	@echo "Checking with mypy..."
	mypy --strict $(PY_FILES)

create_dirs=mkdir -p $(CONTRIB_DIR) $(DECODERS_DIR)

all_reference_decoders: h264_reference_decoder h265_reference_decoder h266_reference_decoder mpeg_4_aac_reference_decoder mpeg_2_aac_reference_decoder ## build all reference decoders

h266_reference_decoder: ## build H.266 reference decoder
	$(create_dirs)
	cd $(CONTRIB_DIR) && git clone https://github.com/fraunhoferhhi/vvdec.git --depth=1 || true
	cd $(CONTRIB_DIR)/vvdec && git pull --autostash || true
	cd $(CONTRIB_DIR)/vvdec && cmake -H. -Bbuild -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS="-Wno-stringop-truncation -Wno-stringop-overflow" && $(MAKE) -C build vvdecapp
	find $(CONTRIB_DIR)/vvdec/bin/release-static/ -name "vvdecapp" -type f -exec cp {} $(DECODERS_DIR)/ \;

h265_reference_decoder: ## build H.265 reference decoder
	$(create_dirs)
	cd $(CONTRIB_DIR) && git clone https://vcgit.hhi.fraunhofer.de/jct-vc/HM.git --depth=1 || true
	cd $(CONTRIB_DIR)/HM && git stash && git pull && git stash apply || true
	cd $(CONTRIB_DIR)/HM && cmake -H. -Bbuild -DCMAKE_BUILD_TYPE=Release && $(MAKE) -C build TAppDecoder
	find $(CONTRIB_DIR)/HM/bin/umake -name "TAppDecoder" -type f -exec cp {} $(DECODERS_DIR)/ \;

h264_reference_decoder: ## build H.264 reference decoder
	$(create_dirs)
	cd $(CONTRIB_DIR) && git clone https://vcgit.hhi.fraunhofer.de/jct-vc/JM.git --depth=1 || true
	cd $(CONTRIB_DIR)/JM && git stash && git pull && git stash apply || true
	cd $(CONTRIB_DIR)/JM && cmake -H. -Bbuild -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS="-Wno-stringop-truncation -Wno-stringop-overflow" && $(MAKE) -C build ldecod
	find $(CONTRIB_DIR)/JM/bin/umake -name "ldecod" -type f -exec cp {} $(DECODERS_DIR)/ \;

mpeg_4_aac_reference_decoder: ## build ISO MPEG4 AAC reference decoder
ifeq ($(dpkg -l | grep gcc-multilib), "")
	sudo apt-get install gcc-multilib
endif
ifeq ($(dpkg -l | grep g++-multilib), "")
	sudo apt-get install g++-multilib
endif
ifeq ($(wildcard /usr/include/asm), )
ifneq ($(wildcard /usr/include/asm-generic), )
		sudo ln -s /usr/include/asm-generic /usr/include/asm
endif
endif

ifeq ($(wildcard $(CONTRIB_DIR)/C050470e_Electronic_inserts), )
	$(create_dirs)
	cd $(CONTRIB_DIR) && rm -f iso_cookies.txt
	cd $(CONTRIB_DIR) && wget -qO- --keep-session-cookies --save-cookies iso_cookies.txt \
	'https://standards.iso.org/ittf/PubliclyAvailableStandards/c050470__ISO_IEC_14496-5_2001_Amd_20_2009_Reference_Software.zip' > /dev/null
	cd $(CONTRIB_DIR) && wget --keep-session-cookies --load-cookies iso_cookies.txt --post-data 'ok=I+accept' \
	'https://standards.iso.org/ittf/PubliclyAvailableStandards/c050470__ISO_IEC_14496-5_2001_Amd_20_2009_Reference_Software.zip'
	cd $(CONTRIB_DIR) && unzip -oq c050470__ISO_IEC_14496-5_2001_Amd_20_2009_Reference_Software.zip
	cd $(CONTRIB_DIR) && rm -f iso_cookies.txt c050470__ISO_IEC_14496-5_2001_Amd_20_2009_Reference_Software.zip

	cd $(CONTRIB_DIR) && git clone https://github.com/MPEGGroup/isobmff.git
	cd $(CONTRIB_DIR)/isobmff && mkdir build && cd build && cmake .. -DCMAKE_C_FLAGS=-m64 && $(MAKE) libisomediafile
	cd $(CONTRIB_DIR)/isobmff && mv lib/liblibisomediafile.a lib/libisomediafile.a
	cd $(CONTRIB_DIR) && cp isobmff/lib/libisomediafile.a C050470e_Electronic_inserts/audio/natural/import/lib/
	cd $(CONTRIB_DIR) && cp isobmff/IsoLib/libisomediafile/src/ISOMovies.h C050470e_Electronic_inserts/audio/natural/import/include/
	cd $(CONTRIB_DIR) && cp isobmff/IsoLib/libisomediafile/src/MP4Movies.h C050470e_Electronic_inserts/audio/natural/import/include/
ifeq ($(OS), Windows_NT)
	cd $(CONTRIB_DIR) && cp isobmff/IsoLib/libisomediafile/w32/MP4OSMacros.h C050470e_Electronic_inserts/audio/natural/import/include/
else ifeq ($(KERNEL_NAME), Linux)
	cd $(CONTRIB_DIR) && cp isobmff/IsoLib/libisomediafile/linux/MP4OSMacros.h C050470e_Electronic_inserts/audio/natural/import/include/ || true
else ifeq ($(KERNEL_NAME), Darwin)
	cd $(CONTRIB_DIR) && cp isobmff/IsoLib/libisomediafile/macosx/MP4OSMacros.h C050470e_Electronic_inserts/audio/natural/import/include/ || true
endif
	cd $(CONTRIB_DIR) && wget --no-check-certificate https://www-mmsp.ece.mcgill.ca/Documents/Downloads/libtsp/libtsp-v7r0.tar.gz
	cd $(CONTRIB_DIR) && tar -zxf libtsp-v7r0.tar.gz && chmod -R ugo=rwx libtsp-v7r0/ && cd libtsp-v7r0/ && $(MAKE) -s COPTS=-m64
	cd $(CONTRIB_DIR) && rm -f libtsp-v7r0.tar.gz
	cd $(CONTRIB_DIR) && cp libtsp-v7r0/lib/libtsp.a C050470e_Electronic_inserts/audio/natural/import/lib/
	cd $(CONTRIB_DIR) && cp libtsp-v7r0/include/libtsp.h C050470e_Electronic_inserts/audio/natural/import/include/
	cd $(CONTRIB_DIR) && mkdir C050470e_Electronic_inserts/audio/natural/import/include/libtsp/
	cd $(CONTRIB_DIR) && cp libtsp-v7r0/include/libtsp/AFpar.h C050470e_Electronic_inserts/audio/natural/import/include/libtsp/
	cd $(CONTRIB_DIR) && cp libtsp-v7r0/include/libtsp/UTpar.h C050470e_Electronic_inserts/audio/natural/import/include/libtsp/
endif
	cd $(CONTRIB_DIR)/C050470e_Electronic_inserts/audio/natural/mp4mcDec && MAKELEVEL=0 $(MAKE) mp4audec_mc REFSOFT_INCLUDE_PATH=../import/include REFSOFT_LIBRARY_PATH=../import/lib CFLAGS=-m64 LDFLAGS=-m64
	find $(CONTRIB_DIR)/C050470e_Electronic_inserts/audio/natural/bin/mp4mcDec -name "mp4audec_mc" -type f -exec cp {} $(DECODERS_DIR) \;

ifneq ($(wildcard /usr/include/asm), )
ifneq ($(wildcard /usr/include/asm-generic), )
		sudo unlink /usr/include/asm
endif
endif

mpeg_2_aac_reference_decoder: ## build ISO MPEG2 AAC reference decoder
ifeq ($(dpkg -l | grep gcc-multilib), "")
	sudo apt-get install gcc-multilib
endif
ifeq ($(dpkg -l | grep g++-multilib), "")
	sudo apt-get install g++-multilib
endif
ifeq ($(wildcard /usr/include/asm), )
ifneq ($(wildcard /usr/include/asm-generic), )
	sudo ln -s /usr/include/asm-generic /usr/include/asm
endif
endif

ifeq ($(wildcard $(CONTRIB_DIR)/C039486_Electronic_inserts), )
	$(create_dirs)
	cd $(CONTRIB_DIR) && rm -f iso_cookies.txt
	cd $(CONTRIB_DIR) && wget -qO- --keep-session-cookies --save-cookies iso_cookies.txt \
	'https://standards.iso.org/ittf/PubliclyAvailableStandards/c039486_ISO_IEC_13818-5_2005_Reference_Software.zip' > /dev/null
	cd $(CONTRIB_DIR) && wget --keep-session-cookies --load-cookies iso_cookies.txt --post-data 'ok=I+accept' \
	'https://standards.iso.org/ittf/PubliclyAvailableStandards/c039486_ISO_IEC_13818-5_2005_Reference_Software.zip'
	cd $(CONTRIB_DIR) && unzip -oq c039486_ISO_IEC_13818-5_2005_Reference_Software.zip
	cd $(CONTRIB_DIR) && rm -f iso_cookies.txt c039486_ISO_IEC_13818-5_2005_Reference_Software.zip ipmp.zip mpeg2audio.zip systems.zip video.zip

	# Unzip and setup MPEG-2 AAC decoder files
	cd $(CONTRIB_DIR) && unzip -oq mpeg2aac.zip
	cd $(CONTRIB_DIR) && rm -f mpeg2aac.zip

	cd $(CONTRIB_DIR) && git clone https://github.com/MPEGGroup/isobmff.git
	cd $(CONTRIB_DIR)/isobmff && mkdir build && cd build && cmake .. -DCMAKE_C_FLAGS=-m64 && $(MAKE) libisomediafile
	cd $(CONTRIB_DIR)/isobmff && mv lib/liblibisomediafile.a lib/libisomediafile.a
	cd $(CONTRIB_DIR) && cp isobmff/lib/libisomediafile.a mpeg2aac/import/lib/
	cd $(CONTRIB_DIR) && cp isobmff/IsoLib/libisomediafile/src/ISOMovies.h mpeg2aac/import/include/
	cd $(CONTRIB_DIR) && cp isobmff/IsoLib/libisomediafile/src/MP4Movies.h mpeg2aac/import/include/
ifeq ($(OS), Windows_NT)
	cd $(CONTRIB_DIR) && cp isobmff/IsoLib/libisomediafile/w32/MP4OSMacros.h mpeg2aac/import/include/
else ifeq ($(KERNEL_NAME), Linux)
	cd $(CONTRIB_DIR) && cp isobmff/IsoLib/libisomediafile/linux/MP4OSMacros.h mpeg2aac/import/include/ || true
else ifeq ($(KERNEL_NAME), Darwin)
	cd $(CONTRIB_DIR) && cp isobmff/IsoLib/libisomediafile/macosx/MP4OSMacros.h mpeg2aac/import/include/ || true
endif
	cd $(CONTRIB_DIR) && wget --no-check-certificate https://www-mmsp.ece.mcgill.ca/Documents/Downloads/libtsp/libtsp-v7r0.tar.gz
	cd $(CONTRIB_DIR) && tar -zxf libtsp-v7r0.tar.gz && chmod -R ugo=rwx libtsp-v7r0/ && cd libtsp-v7r0/ && $(MAKE) -s COPTS=-m64
	cd $(CONTRIB_DIR) && rm -f libtsp-v7r0.tar.gz
	cd $(CONTRIB_DIR) && cp libtsp-v7r0/lib/libtsp.a mpeg2aac/import/lib/
	cd $(CONTRIB_DIR) && cp libtsp-v7r0/include/libtsp.h mpeg2aac/import/include/
	cd $(CONTRIB_DIR) && mkdir mpeg2aac/import/include/libtsp/
	cd $(CONTRIB_DIR) && cp libtsp-v7r0/include/libtsp/AFpar.h mpeg2aac/import/include/libtsp/
	cd $(CONTRIB_DIR) && cp libtsp-v7r0/include/libtsp/UTpar.h mpeg2aac/import/include/libtsp/
endif

	# Build the MPEG-2 AAC decoder
	cd $(CONTRIB_DIR)/mpeg2aac/aacDec && MAKELEVEL=0 $(MAKE) aacdec_mc REFSOFT_INCLUDE_PATH=../import/include REFSOFT_LIBRARY_PATH=../import/lib CFLAGS=-m64 LDFLAGS=-m64
	find $(CONTRIB_DIR)/mpeg2aac/bin/mp4mcDec -name "aacdec_mc" -type f -exec cp {} $(DECODERS_DIR) \;

ifneq ($(wildcard /usr/include/asm), )
ifneq ($(wildcard /usr/include/asm-generic), )
	sudo unlink /usr/include/asm
endif
endif

clean: ## remove contrib temporary folder
	rm -rf $(CONTRIB_DIR)

dbg-%:
	echo "Value of $* = $($*)"

.PHONY: help all_reference_decoders h264_reference_decoder h265_reference_decoder mpeg_4_aac_reference_decoder mpeg_2_aac_reference_decoder lint check format install_deps clean
