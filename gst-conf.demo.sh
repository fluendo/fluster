set -eux

# install
git clone https://github.com/fluendo/fluster.git
cd fluster
# or wget https://github.com/fluendo/fluster/archive/refs/heads/master.zip


# list
./fluster.py -h
./fluster.py list
./fluster.py list -c
./fluster.py list -c | grep 264 | grep ✔


# Download
rm -rf resources/GSTCONF2023/
./fluster.py download GSTCONF2023


# Run
set +e
./fluster.py run -ts GSTCONF2023 -s
./fluster.py run -ts GSTCONF2023 -tv AUD_MW_E -s
./fluster.py run -ts GSTCONF2023 -tv AUD_MW_E -d GStreamer-H.264-VA-Gst1.0 -s
./fluster.py run -ts GSTCONF2023 -tv AUD_MW_E -d GStreamer-H.264-VA-Gst1.0 -s -v
gst-launch-1.0 --no-fault filesrc location=/home/rgonzalez/src/github.com/fluendo/fluster/fluster/../resources/GSTCONF2023/AUD_MW_E/AUD_MW_E.264 ! h264parse ! vah264dec ! video/x-raw ! videoconvert dither=none ! video/x-raw,format=I420 ! videocodectestsink -m
set -e
LIBVA_DRIVER_NAME=iHD ./fluster.py run -ts GSTCONF2023 -tv AUD_MW_E -d GStreamer-H.264-VA-Gst1.0 -s -v
export LIBVA_DRIVER_NAME=iHD

# Other

./fluster.py --no-emoji run -ts GSTCONF2023 -d GStreamer-H.264-VA-Gst1.0 -s
mkdir -p /opt/fluster_resources/
cp -r resources/GSTCONF2023 /opt/fluster_resources/
./fluster.py -r /opt/fluster_resources run -ts GSTCONF2023 -d GStreamer-H.264-VA-Gst1.0 -s
./fluster.py run -ts GSTCONF2023 -d GStreamer-H.264-VA-Gst1.0 -s -f junitxml -so /tmp/junitout.xml
./fluster.py run -ts GSTCONF2023 -d GStreamer-H.264-VA-Gst1.0 --keep
./fluster.py run -ts GSTCONF2023 -d GStreamer-H.264-VA-Gst1.0 -j 1
./fluster.py run -ts GSTCONF2023 -d GStreamer-H.264-VA-Gst1.0 -th 2
LIBVA_DRIVER_NAME=i965 ./fluster.py run -ts GSTCONF2023 -d GStreamer-H.264-VA-Gst1.0 -th 2
