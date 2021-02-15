import argparse
import subprocess
import os
import sys
from pathlib import Path
from subprocess import Popen, PIPE
from shlex import split


def main(args):
    # Get dump archive directory, name and extension
    dump_dir = os.path.dirname(os.path.realpath(args.dump))
    dump_name = os.path.splitext(os.path.basename(os.path.realpath(args.dump)))[0]
    dump_extension = os.path.splitext(args.dump)[1]
    print("Dump directory: " + dump_dir)
    print("Dump name: " + dump_name)

    # Read dump archive with standard shell data compressor and pass dump file to wikiedits script by PIPE
    print("Reading archive...")
    if dump_extension == ".7z":
        unzip_process = Popen(split("7zr e -so " + args.dump), stdout=PIPE)
    elif dump_extension == ".bz2":
        unzip_process = Popen(split("bzip2 -cdk " + args.dump), stdout=PIPE)
    else:
        sys.exit("Wrong archive type. Supported extensions: .7z and .bz2")

    # Specify data directories for errant and wikiedits
    data_dir = "data/"
    errant_data_dir = data_dir + "errant_data/"
    extracted_dumps_dir = data_dir + "wikiedits_extracts/"
    original_data_dir = errant_data_dir + "original/"
    corrected_data_dir = errant_data_dir + "corrected/"
    m2_unfiltered_data_dir = errant_data_dir + "m2-unfiltered/"
    m2_filtered_data_dir = errant_data_dir + "m2-filtered/"
    result_data_dir = errant_data_dir + "result/"
    new_directories_list = [extracted_dumps_dir, original_data_dir, corrected_data_dir, m2_unfiltered_data_dir,
                            m2_filtered_data_dir, result_data_dir]
    # Create specified directories
    for directory in new_directories_list:
        Path(directory).mkdir(parents=True, exist_ok=True)

    # Specify filename for extracted wikiedits
    extracted_file_name = dump_name + ".wikiedits.60"
    # Launch script for wikiedits, it supports only python2
    launch_wikiedits_cmd = "python2 ./wikiedits/bin/wiki_edits.py -l english -t --max-words 60 "
    print("Extracting data with WikiEdits...")
    # Launch wikiedits and write results into .wikiedits.60 file where each line is OLD_EDIT-TAB-NEW_EDIT
    with open(extracted_dumps_dir + extracted_file_name, "w") as outfile:
        subprocess.call(launch_wikiedits_cmd, shell=True, stdin=unzip_process.stdout, stdout=outfile)

    print("Splitting extracted file into original and corrected files...")
    # Split .wikiedits.60 data into two: .src contains only Old Edits Data and .trg contains only New Edits Data
    wikiedits_raw = open(extracted_dumps_dir + extracted_file_name, "r")
    lines = wikiedits_raw.readlines()
    old_edits, new_edits = [], []
    for line in lines:
        splitted_edits = line.split("\t")
        old_edits.append(splitted_edits[0])
        new_edits.append(splitted_edits[1])
    original_file_path = original_data_dir + dump_name + ".src"
    corrected_file_path = corrected_data_dir + dump_name + ".trg"
    with open(original_file_path, 'w') as f:
        f.write("\n".join(old_edits))
    with open(corrected_file_path, 'w') as f:
        f.write("".join(new_edits))

    print("Generating unfiltered .m2 file from original and corrected files...")
    # Analyze untokenized wikipedia edits with ERRANT and tokenize input data with spacy tokenizer
    m2_unfiltered_file_path = m2_unfiltered_data_dir + dump_name + '-unfiltered.m2'
    launch_parallel_to_m2_cmd = "python3 errant/parallel_to_m2.py -orig " + original_file_path + " -cor " + \
                                corrected_file_path + " -out " + m2_unfiltered_file_path + " -lang " + " en " + " -tok "
    subprocess.call(launch_parallel_to_m2_cmd, shell=True)

    # Select gold GEC training data
    if args.gold == "fce":
        gold_data_file_name = "fce.train.gold.bea19.m2"
    elif args.gold == "locness":
        gold_data_file_name = "ABC.train.gold.bea19.m2"
    elif args.gold == "lang8":
        gold_data_file_name = "lang8.train.auto.bea19.m2"

    print("Filtering .m2 data based on a profile of the gold GEC data...")
    # Filter the wikipedia edits with reference to chosen gold GEC training data
    m2_filtered_file_path = m2_filtered_data_dir + dump_name + '-' + args.gold + '-filtered.m2'
    gold_data_file_path = data_dir + "gold_data/" + gold_data_file_name
    launch_filter_m2_cmd = "python3 errant/filter_m2.py -filt " + m2_unfiltered_file_path + " -ref " + \
                           gold_data_file_path + " -out " + m2_filtered_file_path
    subprocess.call(launch_filter_m2_cmd, shell=True)
    print("Done.")

    print("Converting filtered .m2 data to plain .txt format...")
    # Convert the filtered wiki m2 data to a plaintext file of parallel sentences splitted by tab
    result_file_path = result_data_dir + dump_name + '-' + args.gold + '.src-trg.txt'
    launch_m2_to_parallel_cmd = "python3 errant/m2_to_parallel.py -m2 " + m2_filtered_file_path + \
                                " -out " + result_file_path
    subprocess.call(launch_m2_to_parallel_cmd, shell=True)

    print("Dataset successfully generated. Location: " + result_file_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Extract sentences with grammatical-like mistakes edits from wikipedia .7z or .bz2 compressed dump "
                    "file",
        formatter_class=argparse.RawTextHelpFormatter,
        usage="%(prog)s [-h] [options] -dump DUMP")
    parser.add_argument("-dump", help="Wikipedia dump file .7z or .bz2 archive.", required=True)
    parser.add_argument("-gold", choices=["fce", "locness", "lang8"], default="fce",
                        help="Choose gold GEC data for filtering extracted sentences.\n"
                             "Available: FCE v2.1 (default), W&I+LOCNESS v2.1, Lang-8 Corpus of Learner English \n")
    args = parser.parse_args()
    main(args)
