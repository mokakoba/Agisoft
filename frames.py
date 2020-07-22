import argparse
import FFMPEGframes

f = argparse.ArgumentParser()
f.add_argument("-i", "--input", required=True)
f.add_argument("-f", "--fps", required=True)
args = vars(f.parse_args())

input = args["input"]
fps = args["fps"]

f = FFMPEGframes.FFMPEGframes("data/images/")
f.extract_frames(input, fps)