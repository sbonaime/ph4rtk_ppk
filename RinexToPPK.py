#!/usr/bin/env python3

from argparse import ArgumentParser, FileType, RawDescriptionHelpFormatter
import os.path
#from symbol import argument
import sys
from dataclasses import dataclass
from os.path import exists,basename
import csv
from math import radians, cos
import numpy as np


degree_lat_in_meters = 10000000/90


@dataclass
class ppk_timestamp:
    A: str
    B: float
    C: str
    D: str
    E: str
    F: str
    G: str
    H: str
    I: str
    J: str
    K: str
    PH4_Base_File: str

    def calculate_values(self, pos_data_float, file_index):
        Northing_diff = float(self.D.strip().split(',')[0])
        Easting_diff = float(self.E.strip().split(',')[0])
        Elevation_diff = float(self.F.strip().split(',')[0])

        # Find nearest Timestamp
        for idx, line in enumerate(pos_data_float):
            if line[1] > self.B:
                inf = pos_data_float[idx-1]
                sup = pos_data_float[idx]
                break
        percent_diff_between_timestamps = (self.B - inf[1])/(sup[1]-inf[1])
        Interpolated_Lat = (
            inf[2]*(1-percent_diff_between_timestamps)+sup[2]*percent_diff_between_timestamps)
        Interpolated_Lon = (
            inf[3]*(1-percent_diff_between_timestamps)+sup[3]*percent_diff_between_timestamps)
        Interpolated_Alti = (
            inf[4]*(1-percent_diff_between_timestamps)+sup[4]*percent_diff_between_timestamps)

        degree_lon_in_meters = degree_lat_in_meters*cos(radians(inf[2]))

        Lat_Diff_deg = Northing_diff / 1000 / degree_lat_in_meters
        Lon_Diff_deg = Easting_diff / 1000 / degree_lon_in_meters
        Alti_Diff = Elevation_diff / 1000

        new_lat = Interpolated_Lat + Lat_Diff_deg
        new_lon = Interpolated_Lon + Lon_Diff_deg
        new_alt = Interpolated_Alti - Alti_Diff
        print(f'{self.PH4_Base_File}_{file_index:0>4}.JPG\t{new_lat}\t{new_lon}\t{new_alt}')
        return f'{self.PH4_Base_File}_{file_index:0>4}.JPG\t{new_lat}\t{new_lon}\t{new_alt}\n'

@dataclass
class RinexToPPK:
    """Import calculated RINEX from PH4RTK with images adte and find accurate PPK positions"""
    pos_ph4_rinex_file: str
    Timestamp_file: str

    def calculate_PPK_positions(self):

        #        __import__("IPython").embed()
        #        sys.exit()
        #with open(self.pos_ph4_rinex_file, newline='',encoding="utf-8") as open_file:
        with self.pos_ph4_rinex_file as rinex_file:

            # skip headers
            rinex_file.readline()
            rinex_file.readline()

            pos_data = list(csv.reader(rinex_file, delimiter=','))
            pos_data_float = np.asfarray(pos_data, dtype=float)
        
        rinex_file.close()

        #posrows = sum(1 for line in open(self.pos_ph4_rinex_file)) - 2
        #timerows = sum(1 for line in open(self.Timestamp_file))

        # print(f'posrows {posrows} timerows {timerows}')
        
        PH4_part_A,PH4_part_B,_ = basename(self.Timestamp_file.name).split('_')

        PH4_Base_File=f'{PH4_part_A}_{PH4_part_B}'
        file_index = 1
        with open(f'{PH4_part_A}_{PH4_part_B}_PPK.csv','w') as output_csv:
            output_csv.write("EPSG:4326\n")
            with self.Timestamp_file as timestamp_file:
                for line in timestamp_file:
                    # print(line.strip())
                    # ppk_timestamp(line.split('\t')).calculate_values()
                    A, B, C, D, E, F, G, H, I, J, K = line.split('\t')
                    result = ppk_timestamp(A, float(B), C, D, E, F, G, H, I, J, K,PH4_Base_File).calculate_values(pos_data_float, file_index)
                    output_csv.write(result)
                    file_index = file_index+1
            timestamp_file.close()


def parse_arguments():
    parser = ArgumentParser(prog='RinexRoPPK',
        formatter_class=RawDescriptionHelpFormatter,
        description='''Convert Rinex File form RTKPOST and Timestamp.MRK
        to csv file for opendronemap
        ''')

    parser.add_argument(
        '--input_rinex', '-r', type=FileType('r'), 
        metavar='PATH',required=True,
        help="Rinex input file from RTKPOST.")

    parser.add_argument(
        '--input_timestamp', '-t', type=FileType('r'), 
        metavar='PATH',required=True,
        help="Timestamp input file from PH4TK Sdcard.")
    # parser.add_argument(
    #     '--codes', '-c', type=FileType('r'), metavar='PATH',
    #     required=True,
    #     help="File with BPE codes (created by learn_bpe.py).")
    # parser.add_argument(
    #     '--output', '-o', type=FileType('w'), default=sys.stdout,
    #     metavar='PATH',
    #     help="Output file (default: standard output)")
    # parser.add_argument(
    #     '--separator', '-s', type=str, default='@@', metavar='STR',
    #     help="Separator between non-final subword units (default: '%(default)s'))")

    return parser


def main():
    arguments=parse_arguments()
    args=arguments.parse_args()



    RinextoPPK = RinexToPPK(args.input_rinex , args.input_timestamp)
    RinextoPPK.calculate_PPK_positions()


if __name__ == "__main__":
    main()
