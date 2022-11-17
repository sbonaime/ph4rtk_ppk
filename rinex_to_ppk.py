#!/usr/bin/env python3
# pylint: disable=no-member

from argparse import ArgumentParser, FileType, RawDescriptionHelpFormatter
from dataclasses import dataclass
from os.path import basename
import csv
from math import radians, cos
import numpy as np


DEGREE_LAT_IN_METERS = 10000000/90

@dataclass
class PpkTimestamp:
    """Calculate position from ppk timestamp"""

    a_column: str
    b_column: float
    d_column: str
    e_column: str
    f_column: str
    ph4_base_file: str

    def calculate_values(self, pos_data_float, file_index):
        northing_diff = float(self.d_column.strip().split(',', maxsplit=1)[0])
        easting_diff = float(self.e_column.strip().split(',', maxsplit=1)[0])
        elevation_diff = float(self.f_column.strip().split(',', maxsplit=1)[0])

        # Find nearest Timestamp
        for idx, line in enumerate(pos_data_float):
            if line[1] > self.b_column:
                inf = pos_data_float[idx-1]
                sup = pos_data_float[idx]
                break
        percent_diff_between_timestamps = (self.b_column - inf[1])/(sup[1]-inf[1])
        interpolated_lat = (
            inf[2]*(1-percent_diff_between_timestamps)+sup[2]*percent_diff_between_timestamps)
        interpolated_lon = (
            inf[3]*(1-percent_diff_between_timestamps)+sup[3]*percent_diff_between_timestamps)
        interpolated_alti = (
            inf[4]*(1-percent_diff_between_timestamps)+sup[4]*percent_diff_between_timestamps)

        degree_lon_in_meters = DEGREE_LAT_IN_METERS*cos(radians(inf[2]))

        lat_diff_deg = northing_diff / 1000 / DEGREE_LAT_IN_METERS
        lon_diff_deg = easting_diff / 1000 / degree_lon_in_meters
        alti_diff = elevation_diff / 1000

        new_lat = interpolated_lat + lat_diff_deg
        new_lon = interpolated_lon + lon_diff_deg
        new_alt = interpolated_alti - alti_diff
        print(f'{self.ph4_base_file}_{file_index:0>4}.JPG\t{new_lat}\t{new_lon}\t{new_alt}')
        return f'{self.ph4_base_file}_{file_index:0>4}.JPG\t{new_lat}\t{new_lon}\t{new_alt}\n'


@dataclass
class RinexToPpk:
    """Import calculated RINEX from PH4RTK with images date and find accurate PPK positions"""
    pos_ph4_rinex_file: str
    timestamp_file: str
    odm : bool

    def calculate_ppk_positions(self):
        """Calculate position from ppk data"""
        #        __import__("IPython").embed()
        #        sys.exit()
        with self.pos_ph4_rinex_file as rinex_file:

            # skip headers
            rinex_file.readline()
            rinex_file.readline()

            pos_data = list(csv.reader(rinex_file, delimiter=','))
            pos_data_float = np.asfarray(pos_data, dtype=float)

        ph4_part_a,ph4_part_b,_ = basename(self.timestamp_file.name).split('_')

        ph4_base_file=f'{ph4_part_a}_{ph4_part_b}'
        file_index = 1
        with open(f'{ph4_part_a}_{ph4_part_b}_PPK.csv','w',encoding="UTF_8") as output_csv:
            self.odm and output_csv.write("EPSG:4326\n")
            with self.timestamp_file as timestamp_file:
                for line in timestamp_file:
                    a_column, b_column, _, d_column, e_column, f_column, _, _, _, _, _ = line.split('\t')
                    result = PpkTimestamp(a_column, float(b_column), d_column, e_column, f_column, ph4_base_file).calculate_values(pos_data_float, file_index)
                    output_csv.write(result)
                    file_index = file_index+1
        

def parse_arguments():
    parser = ArgumentParser(prog='RinexRoPPK',
        formatter_class=RawDescriptionHelpFormatter,
        description='''Convert rinex file form RTKPOST and timestamp.MRK from PH4RTK
        to csv file for opendronemap
        ''')

    parser.add_argument(
        '--input_rinex', '-r', type=FileType('r'),
        metavar='PATH',required=True,
        help="Rinex input file from RTKPOST.\n ex: 100_0138_Rinex.pos")

    parser.add_argument(
        '--input_timestamp', '-t', type=FileType('r'),
        metavar='PATH',required=True,
        help="Timestamp input file from PH4RTK Sdcard.\n ex: 100_0138_Timestamp.MRK")

    parser.add_argument('--odm','-o', action='store_true',
                    help='output with EPSG header for ODM')
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

    rinextoppk = RinexToPpk(args.input_rinex , args.input_timestamp,args.odm)
    rinextoppk.calculate_ppk_positions()


if __name__ == "__main__":
    main()
