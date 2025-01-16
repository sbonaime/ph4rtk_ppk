#!/usr/bin/env python3
# pylint: disable=no-member

import sys
from argparse import ArgumentParser, FileType, RawDescriptionHelpFormatter
from dataclasses import dataclass
from os.path import basename
import csv
from math import radians, cos
import numpy as np
from io import StringIO

DEGREE_LAT_IN_METERS = 10000000/90



@dataclass
class PpkTimestamp:
    """Calculate position from ppk timestamp"""

    index: str
    time: float
    northing: str
    easting: str
    elevation: str
    ph4_base_file: str

    def calculate_values(self, pos_data_float, file_index):
        northing_diff = float(self.northing.strip().split(',', maxsplit=1)[0])
        easting_diff = float(self.easting.strip().split(',', maxsplit=1)[0])
        elevation_diff = float(self.elevation.strip().split(',', maxsplit=1)[0])

        # Find nearest Timestamp
        for idx, line in enumerate(pos_data_float):
            if line[1] > self.time:
                inf = pos_data_float[idx-1]
                sup = pos_data_float[idx]
                break
        percent_diff_between_timestamps = (self.time - inf[1])/(sup[1]-inf[1])
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
    delimiter : str
    output_path : str

    def calculate_ppk_positions(self):
        """Calculate position from ppk data"""
        #        __import__("IPython").embed()
        #        sys.exit()
        with self.pos_ph4_rinex_file as rinex_file:

            # skip headers
            tout = rinex_file.readlines()
            output =""

            for line in tout:
                if not '%' in line:
                    output+=line

            pos_data = list(csv.reader(output.splitlines(), delimiter=self.delimiter))
            pos_data_float = np.asarray(pos_data, dtype=float)

        ph4_part_a,ph4_part_b,_ = basename(self.timestamp_file.name).split('_')

        ph4_base_file=f'{ph4_part_a}_{ph4_part_b}'
        file_index = 1
        with open(f'{self.output_path}/{ph4_part_a}_{ph4_part_b}_PPK.csv','w',encoding="UTF_8") as output_csv:
            self.odm and output_csv.write("EPSG:4326\n")
            with self.timestamp_file as timestamp_file:
                for line in timestamp_file:
                    index, time, day_number, northing, easting, elevation, _, _, _, _, _ = line.split('\t')

                    result = PpkTimestamp(index, float(time), northing, easting, elevation, ph4_base_file).calculate_values(pos_data_float, file_index)
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

    parser.add_argument('--input_timestamp', '-t', type=FileType('r'),
        metavar='PATH',required=True,
        help="Timestamp input file from PH4RTK Sdcard.\n ex: 100_0138_Timestamp.MRK")

    parser.add_argument(
        '--delimiter', '-d', type=str, required=False, default=',',
        help="Char delimiter of the Rinex")

    parser.add_argument('--odm', action='store_true',
                    help='output with EPSG:4326 header for ODM')

    parser.add_argument('--output_path','-o',  type=str, required=True,
                    help='output path to write PPK.csv data')
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

    if len(args.delimiter) > 1 :
        print("Delimiter is just one char like ',' or ' '")
        sys.exit()

    rinextoppk = RinexToPpk(args.input_rinex , args.input_timestamp,args.odm, args.delimiter,args.output_path)
    rinextoppk.calculate_ppk_positions()


if __name__ == "__main__":
    main()
